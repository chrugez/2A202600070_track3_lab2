from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from src.config import get_settings
from src.llm import LLMClient
from src.memory.context_manager import ContextWindowManager
from src.memory.episodic_json import EpisodicMemory
from src.memory.redis_preferences import RedisPreferenceMemory
from src.memory.router import MemoryRouter
from src.memory.semantic_chroma import SemanticMemory
from src.memory.short_term import ShortTermMemory
from src.types import AgentState, ContextItem
from src.utils import estimate_tokens, normalize_text, now_iso, overlap_score

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = "END"
    START = "START"
    StateGraph = None


SYSTEM_PROMPT = """You are a multi-memory AI agent.
Use memory only when relevant.
Do not invent memories.
If retrieved memory conflicts with the user's current message, prioritize the current message.
Use preferences naturally and avoid robotic recall phrasing.
When recommendations are requested, check preference memory.
When the user refers to prior experiences, check episodic memory.
When the user asks conceptual questions, check semantic memory.
Keep the response aligned with the user's preferred style when known."""


class AgentGraph:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.router = MemoryRouter()
        self.context_manager = ContextWindowManager()
        self.preferences = RedisPreferenceMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.llm = LLMClient()
        self._compiled = self._build_graph()

    def _build_graph(self):
        if StateGraph is None:
            return None
        graph = StateGraph(AgentState)
        graph.add_node("parse_input", self.parse_input)
        graph.add_node("route_memory", self.route_memory)
        graph.add_node("retrieve_memory", self.retrieve_memory)
        graph.add_node("build_context", self.build_context)
        graph.add_node("generate_response", self.generate_response)
        graph.add_node("extract_memory_writes", self.extract_memory_writes)
        graph.add_node("persist_memory", self.persist_memory)
        graph.add_node("log_metrics", self.log_metrics)
        graph.add_edge(START, "parse_input")
        graph.add_edge("parse_input", "route_memory")
        graph.add_edge("route_memory", "retrieve_memory")
        graph.add_edge("retrieve_memory", "build_context")
        graph.add_edge("build_context", "generate_response")
        graph.add_edge("generate_response", "extract_memory_writes")
        graph.add_edge("extract_memory_writes", "persist_memory")
        graph.add_edge("persist_memory", "log_metrics")
        graph.add_edge("log_metrics", END)
        return graph.compile()

    def run(self, state: AgentState) -> AgentState:
        if self._compiled is not None:
            return self._compiled.invoke(state)
        current = state
        for node in (
            self.parse_input,
            self.route_memory,
            self.retrieve_memory,
            self.build_context,
            self.generate_response,
            self.extract_memory_writes,
            self.persist_memory,
            self.log_metrics,
        ):
            current = node(current)
        return current

    def parse_input(self, state: AgentState) -> AgentState:
        state.setdefault("messages", [])
        state["messages"].append({"role": "user", "content": state["user_query"]})
        return state

    def route_memory(self, state: AgentState) -> AgentState:
        state["route_decision"] = self.router.route(state["user_query"], state["messages"])
        return state

    def retrieve_memory(self, state: AgentState) -> AgentState:
        decision = state["route_decision"]
        user_id = state["user_id"]
        retrieved = {"short_term": [], "preferences": [], "episodic": [], "semantic": []}
        if decision["use_short_term"]:
            retrieved["short_term"] = state["messages"][:-1][-6:]
        if decision["use_preferences"]:
            retrieved["preferences"] = self.preferences.search_preferences(user_id, state["user_query"])
        if decision["use_episodic"]:
            retrieved["episodic"] = self.episodic.search_episodes(user_id, state["user_query"])
        if decision["use_semantic"]:
            retrieved["semantic"] = self.semantic.search(user_id, state["user_query"])
        state["retrieved_memories"] = retrieved
        return state

    def build_context(self, state: AgentState) -> AgentState:
        query = state["user_query"]
        items = [
            ContextItem(
                source="current_query",
                content=query,
                priority=1,
                relevance_score=1.0,
                token_count=estimate_tokens(query),
                metadata={},
            )
        ]
        for memory in state["retrieved_memories"].get("preferences", []):
            items.append(
                ContextItem(
                    source="preferences",
                    content=memory["content"],
                    priority=2,
                    relevance_score=memory["relevance_score"],
                    token_count=estimate_tokens(memory["content"]),
                    metadata=memory,
                )
            )
        for memory in state["retrieved_memories"].get("episodic", []):
            items.append(
                ContextItem(
                    source="episodic",
                    content=memory["content"],
                    priority=2,
                    relevance_score=memory["relevance_score"],
                    token_count=estimate_tokens(memory["content"]),
                    metadata=memory,
                )
            )
        for memory in state["retrieved_memories"].get("semantic", []):
            items.append(
                ContextItem(
                    source="semantic",
                    content=memory["content"],
                    priority=2,
                    relevance_score=memory["relevance_score"],
                    token_count=estimate_tokens(memory["content"]),
                    metadata=memory,
                )
            )
        for message in state["retrieved_memories"].get("short_term", []):
            items.append(
                ContextItem(
                    source="short_term",
                    content=f"{message['role']}: {message['content']}",
                    priority=3,
                    relevance_score=overlap_score(query, message["content"]),
                    token_count=estimate_tokens(message["content"]),
                    metadata=message,
                )
            )
        state["context_items"] = items
        state["final_context"] = self.context_manager.build_context(items, self.settings.max_context_tokens)
        return state

    def generate_response(self, state: AgentState) -> AgentState:
        memories = state["retrieved_memories"]
        sections = [
            SYSTEM_PROMPT,
            "",
            "Relevant user preferences:",
            *[f"- {item['content']}" for item in memories.get("preferences", [])[:3]],
            "",
            "Relevant previous episodes:",
            *[f"- {item['content']}" for item in memories.get("episodic", [])[:3]],
            "",
            "Relevant semantic knowledge:",
            *[f"- {item['content']}" for item in memories.get("semantic", [])[:3]],
            "",
            "Recent conversation:",
            *[f"- {item.content}" for item in state["final_context"] if item.source == "short_term"],
            "",
            f"User query: {state['user_query']}",
        ]
        prompt = "\n".join(sections)
        state["response"] = self.llm.generate(
            prompt,
            {
                "user_query": state["user_query"],
                "preferences": memories.get("preferences", []),
                "episodes": memories.get("episodic", []),
                "semantic": memories.get("semantic", []),
            },
        )
        state["messages"].append({"role": "assistant", "content": state["response"]})
        return state

    def extract_memory_writes(self, state: AgentState) -> AgentState:
        query = normalize_text(state["user_query"])
        writes: list[dict] = []
        if "thich" in query or "khong thich" in query or "toi dang hoc" in query:
            payload = {}
            if "python" in query:
                payload.setdefault("likes", []).append("Python")
            if "java" in query and "khong thich" in query:
                payload.setdefault("dislikes", []).append("Java")
            if "ngan" in query or "vi du" in query:
                payload["response_style"] = "short_with_examples"
            if "ai agents" in query or "langgraph" in query:
                payload["learning_topic"] = "AI Agents and LangGraph"
            if payload:
                writes.append(
                    {
                        "memory_type": "preference",
                        "key": "user_preferences",
                        "value": {
                            **payload,
                            "source": state["session_id"],
                            "confidence": 0.95,
                        },
                    }
                )
        if "di ung sua bo" in query:
            writes.append(
                {
                    "memory_type": "preference",
                    "key": "allergy",
                    "value": {"allergy": "sữa bò", "source": state["session_id"], "confidence": 0.9},
                }
            )
        if "di ung dau nanh" in query or "a nham" in query:
            writes.append(
                {
                    "memory_type": "preference",
                    "key": "allergy",
                    "value": {"allergy": "đậu nành", "source": state["session_id"], "confidence": 0.98},
                }
            )
        if "bi roi" in query or "khong hieu" in query or "confused" in query:
            writes.append(
                {
                    "memory_type": "episodic",
                    "value": {
                        "user_id": state["user_id"],
                        "session_id": state["session_id"],
                        "event": f"User was confused about: {state['user_query']}",
                        "context": state["user_query"],
                        "tags": ["confusion", "learning", "async" if "async" in query else "general"],
                        "importance": 0.8,
                    },
                }
            )
        if any(term in query for term in ["async", "await", "decorator", "fastapi", "django"]):
            writes.append(
                {
                    "memory_type": "semantic",
                    "value": {
                        "user_id": state["user_id"],
                        "text": state["response"],
                        "metadata": {
                            "topic": "python_async" if "async" in query else "python_concept",
                            "type": "concept",
                            "source": state["session_id"],
                        },
                    },
                }
            )
        state["memory_writes"] = writes
        return state

    def persist_memory(self, state: AgentState) -> AgentState:
        for write in state["memory_writes"]:
            memory_type = write["memory_type"]
            if memory_type == "preference":
                self.preferences.upsert_preference(state["user_id"], write["key"], write["value"])
            elif memory_type == "episodic":
                self.episodic.add_episode(write["value"])
            elif memory_type == "semantic":
                semantic = write["value"]
                self.semantic.add_document(semantic["user_id"], semantic["text"], semantic["metadata"])
        return state

    def log_metrics(self, state: AgentState) -> AgentState:
        token_breakdown: dict[str, int] = {}
        for item in state["final_context"]:
            token_breakdown[item.source] = token_breakdown.get(item.source, 0) + item.token_count
        token_breakdown["system_prompt"] = estimate_tokens(SYSTEM_PROMPT)
        total_context_tokens = sum(token_breakdown.values())
        relevant_tokens = sum(
            item.token_count for item in state["final_context"] if item.priority <= 2 and item.source != "current_query"
        )
        retrieved_memories = state["retrieved_memories"]
        memory_required = any(
            bool(state["route_decision"].get(flag))
            for flag in ("use_short_term", "use_preferences", "use_episodic", "use_semantic")
        )
        memory_hits = sum(
            1
            for key in ("preferences", "episodic", "semantic")
            if retrieved_memories.get(key)
        )
        state["metrics"] = {
            "timestamp": now_iso(),
            "token_breakdown": token_breakdown,
            "total_context_tokens": total_context_tokens,
            "context_utilization": round(relevant_tokens / total_context_tokens, 3) if total_context_tokens else 0.0,
            "memory_required": memory_required,
            "memory_hits": memory_hits,
            "retrieved_counts": {key: len(value) for key, value in retrieved_memories.items()},
            "route_reason": state["route_decision"]["reason"],
        }
        return state
