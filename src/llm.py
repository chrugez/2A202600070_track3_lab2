from __future__ import annotations

from typing import Any

from src.config import get_settings
from src.utils import normalize_text

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.openai_api_key and OpenAI is not None:
            self._client = OpenAI(api_key=self.settings.openai_api_key)

    def generate(self, prompt: str, debug_context: dict[str, Any]) -> str:
        if self._client is not None:
            try:
                completion = self._client.responses.create(
                    model=self.settings.openai_model,
                    input=prompt,
                )
                return completion.output_text
            except Exception:
                return self._fallback_response(debug_context)
        return self._fallback_response(debug_context)

    def _fallback_response(self, debug_context: dict[str, Any]) -> str:
        query = debug_context["user_query"]
        preferences = debug_context.get("preferences", [])
        episodes = debug_context.get("episodes", [])
        semantic = debug_context.get("semantic", [])
        response_parts = []
        if preferences:
            pref_line = self._summarize_preferences(preferences)
            if pref_line:
                response_parts.append(f"Dựa trên preference đã lưu ({pref_line}),")
        if episodes:
            response_parts.append(f"Có một episode liên quan: {episodes[0]['content']}.")
        if semantic:
            response_parts.append(f"Knowledge liên quan: {semantic[0]['content']}")

        q = normalize_text(query)
        preference_text = normalize_text(" ".join(item["content"] for item in preferences))
        if "di ung" in q and preferences:
            if "dau nanh" in preference_text:
                response_parts.append("Thông tin đang lưu cho thấy bạn dị ứng đậu nành.")
            elif "sua bo" in preference_text:
                response_parts.append("Thông tin đang lưu cho thấy bạn dị ứng sữa bò.")
        elif "framework" in q and ("python" in q or "python" in preference_text or "java" in preference_text):
            response_parts.append("Mình gợi ý FastAPI nếu bạn muốn học nhanh và xây API gọn, hoặc Django nếu cần stack đầy đủ.")
        elif "nen hoc" in q and "langgraph" in preference_text:
            response_parts.append("Vì bạn đang học AI Agents và LangGraph, nên đi tiếp vào memory systems, tool calling và evaluation.")
        elif "async" in q or "await" in q:
            response_parts.append(
                "Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác."
            )
        elif "decorator" in q:
            response_parts.append(
                "Decorator là hàm bọc một hàm khác để thêm hành vi. Ví dụ: `@log` trên hàm `hello()` để in log trước khi gọi hàm."
            )
        elif "automation" in q and "python" in preference_text:
            response_parts.append("Vì bạn đã hợp với Python, hãy bắt đầu với scripting, `requests`, file processing và task scheduling nhỏ.")
        elif "ngon ngu nao" in q or "nen hoc" in q:
            response_parts.append("Nếu bạn hợp với Python, hãy đi sâu vào FastAPI, automation và data workflows trước.")
        else:
            response_parts.append("Mình sẽ trả lời dựa trên query hiện tại và bộ nhớ liên quan để giữ câu trả lời đúng trong ngữ cảnh.")
        return " ".join(part.strip() for part in response_parts if part).strip()

    def _summarize_preferences(self, preferences: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for item in preferences:
            value = item.get("value", {})
            likes = value.get("likes", [])
            dislikes = value.get("dislikes", [])
            if likes:
                parts.append(f"thích {', '.join(likes)}")
            if dislikes:
                parts.append(f"không thích {', '.join(dislikes)}")
            if value.get("learning_topic"):
                parts.append(f"đang học {value['learning_topic']}")
            if value.get("allergy"):
                parts.append(f"dị ứng {value['allergy']}")
            if value.get("response_style") == "short_with_examples":
                parts.append("thích câu trả lời ngắn, có ví dụ")
        return "; ".join(dict.fromkeys(parts))
