# Agents.md — Lab #17: Multi-Memory Agent với LangGraph

## 1. Mục tiêu

Xây dựng một **Multi-Memory Agent** bằng LangGraph có khả năng ghi nhớ và sử dụng thông tin qua nhiều phiên hội thoại.

Agent cần hỗ trợ các loại memory sau:

1. **Short-term memory**: lưu ngữ cảnh hội thoại hiện tại.
2. **Long-term preference memory**: lưu user preferences qua nhiều sessions.
3. **Episodic memory**: lưu các sự kiện/trải nghiệm cụ thể đã xảy ra.
4. **Semantic memory**: lưu tri thức, khái niệm, facts, hoặc hiểu biết tổng quát có thể truy xuất theo ngữ nghĩa.

Deliverable cuối cùng gồm:

* GitHub repo source code hoàn chỉnh.
* Agent chạy được với full memory stack.
* Benchmark report so sánh agent có memory và không memory trên 10 multi-turn conversations.
* Phân tích memory hit rate, response relevance, context utilization, token efficiency và token budget breakdown.

---

## 2. Bối cảnh bài lab

Agent cần chứng minh khả năng nhớ preferences của user qua nhiều sessions.

Ví dụ expected behavior:

### Session 1

User nói:

> Tôi thích Python, không thích Java.

Agent cần ghi preference này vào long-term memory, ví dụ Redis.

Expected stored memory:

```json
{
  "user_id": "user_001",
  "type": "preference",
  "key": "programming_language",
  "value": {
    "likes": ["Python"],
    "dislikes": ["Java"]
  },
  "source": "session_1",
  "confidence": 0.95
}
```

### Session 2: new process

Agent được chạy lại như một process mới.

User hỏi:

> Tôi nên học ngôn ngữ nào tiếp theo?

Agent cần load memory và chủ động gợi ý Python-related solution mà không cần hỏi lại preference.

Expected response:

> Vì bạn thích Python và không thích Java, mình gợi ý bạn học sâu hơn về Python backend, FastAPI, data engineering hoặc automation trước. Nếu muốn mở rộng, TypeScript cũng là lựa chọn tốt nhưng không bắt buộc.

### Session 3

Agent recall episode:

> User từng bị confused về async/await.

Khi user hỏi về code async Python, agent cần tự thêm explanation phù hợp.

Expected response behavior:

* Giải thích async/await chậm hơn, từng bước hơn.
* Nhắc lại ngữ cảnh nếu hữu ích: “Lần trước bạn có vẻ hơi rối ở phần async/await, nên mình sẽ giải thích theo flow execution trước.”
* Không nhắc memory một cách quá máy móc nếu không cần thiết.

---

## 3. Memory taxonomy

Agent cần phân biệt rõ 4 loại memory.

| Memory type              | Backend đề xuất              | Mục đích                                           | Ví dụ                                                     |
| ------------------------ | ---------------------------- | -------------------------------------------------- | --------------------------------------------------------- |
| ConversationBufferMemory | In-memory / LangChain memory | Short-term context trong session hiện tại          | Các tin nhắn gần nhất trong cuộc trò chuyện               |
| Redis long-term memory   | Redis                        | Lưu preferences ổn định qua sessions               | User thích Python, không thích Java                       |
| JSON episodic log        | JSON file                    | Lưu các episode/sự kiện cụ thể                     | User từng confused về async/await ở session 2             |
| Chroma semantic memory   | Chroma vector DB             | Lưu facts/knowledge truy xuất theo semantic search | “Python async/await dùng event loop để xử lý concurrency” |

---

## 4. Khi nào lưu long-term, short-term, episodic, semantic?

### 4.1 Short-term memory

Dùng cho thông tin chỉ cần trong session hiện tại.

Ví dụ:

* User vừa gửi đoạn code cần debug.
* User đang yêu cầu sửa một câu trả lời trước đó.
* User đang nói “ý thứ 2”, “cái trên”, “đoạn đó”.

Không nhất thiết lưu lâu dài.

### 4.2 Long-term preference memory

Dùng cho thông tin ổn định và hữu ích trong tương lai.

Ví dụ nên lưu:

* User thích Python.
* User không thích Java.
* User thích câu trả lời ngắn, có ví dụ cụ thể.
* User đang học AI Agents và LangGraph.

Không nên lưu nếu:

* Chỉ là lựa chọn tạm thời.
* User nói trong một bài tập giả lập.
* Thông tin quá nhạy cảm hoặc không cần thiết cho cá nhân hóa.

### 4.3 Episodic memory

Dùng cho sự kiện cụ thể đã xảy ra.

Ví dụ:

```json
{
  "episode_id": "ep_2026_04_24_001",
  "user_id": "user_001",
  "session_id": "session_3",
  "event": "User was confused about Python async/await",
  "context": "User asked why await does not block the whole program",
  "timestamp": "2026-04-24T10:30:00Z",
  "tags": ["python", "async", "confusion"],
  "importance": 0.8
}
```

Episodic memory nên được dùng khi một sự kiện cụ thể có thể giúp agent phục vụ user tốt hơn sau này.

### 4.4 Semantic memory

Dùng cho tri thức tổng quát, facts, concepts hoặc summary có thể truy xuất bằng vector search.

Ví dụ:

```json
{
  "doc_id": "sem_python_async_001",
  "text": "In Python, async/await enables cooperative concurrency through an event loop. Await pauses the current coroutine but does not block the entire program.",
  "metadata": {
    "topic": "python_async",
    "source": "lab_session",
    "type": "concept"
  }
}
```

Semantic memory thường được lưu trong Chroma để retrieval bằng similarity search.

---

## 5. Kiến trúc hệ thống

```text
User Query
   |
   v
LangGraph Agent
   |
   +--> Memory Router
          |
          +--> Short-term Buffer
          +--> Redis Preference Memory
          +--> JSON Episodic Log
          +--> Chroma Semantic Memory
   |
   v
Context Window Manager
   |
   v
LLM Response
   |
   v
Memory Writer / Updater
```

Agent phải có 3 luồng chính:

1. **Read memory before answering**

   * Phân tích query intent.
   * Router chọn memory backend phù hợp.
   * Retrieve relevant memory.
   * Inject vào prompt.

2. **Answer user**

   * Dùng retrieved context.
   * Không hallucinate memory.
   * Không over-personalize nếu memory không liên quan.

3. **Write memory after answering**

   * Trích xuất preference, episode, semantic fact nếu có.
   * Ghi vào backend phù hợp.
   * Deduplicate memory cũ.

---

## 6. Required implementation tasks

### Task 1 — Implement 4 memory backends

#### 1. ConversationBufferMemory

Yêu cầu:

* Lưu các message gần nhất trong session hiện tại.
* Có giới hạn token hoặc số message.
* Tự trim khi context window gần đầy.

Suggested interface:

```python
class ShortTermMemory:
    def add_message(self, role: str, content: str) -> None:
        ...

    def get_recent_context(self, max_tokens: int) -> list[dict]:
        ...

    def trim(self, max_tokens: int) -> None:
        ...
```

#### 2. Redis long-term preference memory

Yêu cầu:

* Lưu preferences qua nhiều sessions/processes.
* Key theo `user_id`.
* Có thể update/deduplicate preference.

Suggested Redis keys:

```text
user:{user_id}:preferences
user:{user_id}:profile
```

Suggested interface:

```python
class RedisPreferenceMemory:
    def get_preferences(self, user_id: str) -> dict:
        ...

    def upsert_preference(self, user_id: str, key: str, value: dict) -> None:
        ...

    def search_preferences(self, user_id: str, query: str) -> list[dict]:
        ...
```

#### 3. JSON episodic log

Yêu cầu:

* Append-only hoặc semi-append-only log.
* Mỗi episode có timestamp, session_id, event, tags, importance.
* Có hàm search theo keyword/tag.

Suggested file:

```text
memory/episodic_log.jsonl
```

Suggested interface:

```python
class EpisodicMemory:
    def add_episode(self, episode: dict) -> None:
        ...

    def search_episodes(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        ...
```

#### 4. Chroma semantic memory

Yêu cầu:

* Lưu semantic facts/concepts.
* Dùng embedding để similarity search.
* Metadata gồm user_id, topic, type, source.

Suggested interface:

```python
class SemanticMemory:
    def add_document(self, user_id: str, text: str, metadata: dict) -> None:
        ...

    def search(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        ...
```

---

## 7. Task 2 — Build memory router

Memory router chọn loại memory phù hợp dựa trên query intent.

### Required routing logic

| Query intent                        | Memory cần dùng           |
| ----------------------------------- | ------------------------- |
| User hỏi tiếp nội dung vừa nói      | Short-term buffer         |
| User hỏi recommendation cá nhân hóa | Redis preference memory   |
| User nhắc lại trải nghiệm trước đây | Episodic memory           |
| User hỏi concept/fact/knowledge     | Semantic memory           |
| Query phức tạp                      | Kết hợp nhiều loại memory |

### Example routing

Input:

> Tôi nên học framework nào tiếp theo?

Route:

```json
{
  "use_short_term": true,
  "use_preferences": true,
  "use_episodic": false,
  "use_semantic": true,
  "reason": "Recommendation requires user preferences and semantic knowledge about frameworks."
}
```

Input:

> Lần trước tôi bị rối phần async gì đó, giải thích lại giúp tôi.

Route:

```json
{
  "use_short_term": true,
  "use_preferences": false,
  "use_episodic": true,
  "use_semantic": true,
  "reason": "User refers to a previous learning episode and asks for conceptual explanation."
}
```

### Suggested router interface

```python
class MemoryRouter:
    def route(self, user_query: str, session_context: list[dict]) -> dict:
        ...
```

Router có thể dùng:

* Rule-based intent detection.
* LLM classification.
* Hybrid rule + LLM.

Trong lab, nên bắt đầu bằng rule-based để dễ benchmark và debug.

---

## 8. Task 3 — Context window management

Agent cần auto-trim khi gần context limit và dùng priority-based eviction theo 4-level hierarchy.

### 4-level priority hierarchy

Priority từ cao đến thấp:

1. **Current user query**

   * Luôn giữ.

2. **High-confidence relevant memory**

   * Preferences trực tiếp liên quan.
   * Episodes có keyword/topic match.
   * Semantic docs similarity cao.

3. **Recent short-term conversation**

   * Các turn gần nhất trong session.

4. **Low-relevance or stale context**

   * Memory cũ, score thấp.
   * Conversation turns ít liên quan.
   * Dữ liệu trùng lặp.

### Required behavior

* Tính token budget trước khi gọi LLM.
* Nếu vượt limit, loại bỏ context theo priority thấp trước.
* Log lại token usage và context utilization.

Suggested data structure:

```python
@dataclass
class ContextItem:
    source: str
    content: str
    priority: int
    relevance_score: float
    token_count: int
    metadata: dict
```

Suggested interface:

```python
class ContextWindowManager:
    def build_context(self, items: list[ContextItem], max_tokens: int) -> list[ContextItem]:
        ...
```

---

## 9. Task 4 — Benchmark

Benchmark phải so sánh 2 agent variants:

1. **Baseline agent**: không có memory hoặc chỉ có current context.
2. **Memory agent**: có đủ 4 memory backends + router + context manager.

### Dataset

Tạo ít nhất **10 multi-turn conversations**.

Mỗi conversation nên có:

* 2–4 sessions.
* Ít nhất 1 preference cần nhớ.
* Ít nhất 1 episode cần recall.
* Ít nhất 1 semantic retrieval case.
* Một câu hỏi cần personalization.

### Example benchmark conversation

#### Conversation 1 — Programming preference

Session 1:

```text
User: Tôi thích Python, không thích Java.
Agent: Mình đã hiểu. Mình sẽ ưu tiên Python khi gợi ý giải pháp lập trình cho bạn.
```

Session 2:

```text
User: Tôi nên học backend framework nào?
Expected memory agent: Gợi ý FastAPI/Django vì user thích Python.
Expected baseline agent: Hỏi lại preference hoặc đưa gợi ý chung chung.
```

#### Conversation 2 — Async confusion episode

Session 1:

```text
User: Tôi bị rối async/await, không hiểu await có block chương trình không.
Agent: Giải thích và lưu episode user confused async/await.
```

Session 2:

```text
User: Giải thích asyncio queue giúp tôi.
Expected memory agent: Nhắc nhẹ async/await và giải thích từng bước.
Expected baseline agent: Giải thích chung, không cá nhân hóa.
```

#### Conversation 3 — Response style preference

Session 1:

```text
User: Tôi thích câu trả lời ngắn, có ví dụ code.
```

Session 2:

```text
User: Giải thích decorator trong Python.
Expected memory agent: Trả lời ngắn, có ví dụ code.
Expected baseline agent: Có thể trả lời dài hoặc không đúng style.
```

---

## 10. Metrics cần báo cáo

### 10.1 Response relevance

Đánh giá câu trả lời có liên quan tới query và memory hay không.

Scale đề xuất: 1–5.

| Score | Ý nghĩa                               |
| ----- | ------------------------------------- |
| 1     | Không liên quan                       |
| 2     | Có liên quan một phần                 |
| 3     | Đáp ứng cơ bản                        |
| 4     | Tốt, có dùng memory phù hợp           |
| 5     | Rất tốt, cá nhân hóa đúng và tự nhiên |

### 10.2 User satisfaction

Đánh giá mức hài lòng giả lập hoặc human evaluation.

Scale: 1–5.

### 10.3 Memory hit rate

Tỷ lệ query cần memory và agent retrieve đúng memory.

```text
memory_hit_rate = successful_memory_hits / memory_required_queries
```

Example:

```text
successful_memory_hits = 8
memory_required_queries = 10
memory_hit_rate = 0.8
```

### 10.4 Context utilization

Đo mức context được dùng hiệu quả.

Có thể tính bằng:

```text
context_utilization = relevant_context_tokens / total_context_tokens
```

### 10.5 Token efficiency

So sánh token dùng bởi memory agent và baseline.

Metrics gợi ý:

```text
tokens_per_successful_answer = total_tokens / successful_answers
```

### 10.6 Token budget breakdown

Report cần breakdown token theo nguồn:

| Source              | Tokens | Percentage |
| ------------------- | -----: | ---------: |
| Current query       |    120 |        10% |
| Short-term memory   |    300 |        25% |
| Redis preferences   |     80 |         7% |
| Episodic memory     |    180 |        15% |
| Semantic memory     |    350 |        29% |
| System prompt/tools |    170 |        14% |

---

## 11. Suggested project structure

```text
lab17-multi-memory-agent/
├── README.md
├── Agents.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py
│   ├── graph.py
│   ├── config.py
│   ├── memory/
│   │   ├── short_term.py
│   │   ├── redis_preferences.py
│   │   ├── episodic_json.py
│   │   ├── semantic_chroma.py
│   │   ├── router.py
│   │   └── context_manager.py
│   ├── agents/
│   │   ├── baseline_agent.py
│   │   └── memory_agent.py
│   └── benchmark/
│       ├── dataset.py
│       ├── evaluator.py
│       ├── run_benchmark.py
│       └── metrics.py
├── memory/
│   ├── episodic_log.jsonl
│   └── chroma/
├── reports/
│   ├── benchmark_report.md
│   └── results.json
└── tests/
    ├── test_memory_router.py
    ├── test_preferences.py
    ├── test_episodic_memory.py
    └── test_context_manager.py
```

---

## 12. LangGraph workflow requirements

Agent nên được implement dưới dạng LangGraph state machine.

### Suggested state

```python
from typing import TypedDict, Any

class AgentState(TypedDict):
    user_id: str
    session_id: str
    messages: list[dict]
    user_query: str
    route_decision: dict
    retrieved_memories: dict
    context_items: list[dict]
    final_context: list[dict]
    response: str
    memory_writes: list[dict]
    metrics: dict
```

### Suggested nodes

```text
START
  -> parse_input
  -> route_memory
  -> retrieve_memory
  -> build_context
  -> generate_response
  -> extract_memory_writes
  -> persist_memory
  -> log_metrics
END
```

### Node responsibilities

#### parse_input

* Normalize user input.
* Attach user_id and session_id.
* Append to short-term memory.

#### route_memory

* Decide which memory backends to query.
* Return route decision with reason.

#### retrieve_memory

* Query Redis, JSON episodic log, Chroma depending on router output.
* Score each memory result.

#### build_context

* Convert retrieved memories into ContextItem.
* Apply priority hierarchy.
* Trim context if needed.

#### generate_response

* Call LLM with final context.
* Require response grounded in retrieved memory.

#### extract_memory_writes

* Detect new preferences.
* Detect episodes worth storing.
* Detect semantic facts worth storing.

#### persist_memory

* Write to Redis / JSON / Chroma.
* Avoid duplicates.

#### log_metrics

* Record token usage, route decision, memory hits, retrieved docs.

---

## 13. Prompting guidelines for the agent

System prompt nên nói rõ:

```text
You are a multi-memory AI agent.
Use memory only when relevant.
Do not invent memories.
If retrieved memory conflicts with the user's current message, prioritize the user's current message.
Use preferences naturally; do not repeatedly say “I remember”.
When the user asks for recommendations, check preference memory.
When the user refers to previous experiences, check episodic memory.
When the user asks conceptual questions, check semantic memory.
Keep responses aligned with the user's preferred style when known.
```

Memory context có thể inject theo format:

```text
Relevant user preferences:
- Likes Python.
- Dislikes Java.

Relevant previous episodes:
- User was confused about async/await and benefited from step-by-step explanation.

Relevant semantic knowledge:
- async/await uses cooperative concurrency through an event loop.
```

---

## 14. Acceptance criteria

Bài lab được xem là hoàn thành khi:

* Có đủ 4 memory backends.
* Agent chạy qua ít nhất 3 sessions và nhớ được preference từ session trước.
* Agent vẫn nhớ preference sau khi restart process.
* Agent recall được ít nhất 1 episode như “user confused async/await”.
* Agent dùng Chroma semantic search cho conceptual query.
* Có memory router hoạt động rõ ràng.
* Có context window manager với auto-trim và priority eviction.
* Có benchmark 10 multi-turn conversations.
* Có report so sánh agent có memory vs không memory.
* Report có các metrics: response relevance, user satisfaction, memory hit rate, context utilization, token efficiency, token budget breakdown.

---

## 15. Official grading rubric

Tổng điểm: **100 điểm**. Nộp source/notebook, data files và `BENCHMARK.md`.

| Hạng mục                                     |    Điểm |
| -------------------------------------------- | ------: |
| 1. Full memory stack: 4 backends/interface   |      25 |
| 2. LangGraph state/router + prompt injection |      30 |
| 3. Save/update memory + conflict handling    |      15 |
| 4. Benchmark 10 multi-turn conversations     |      20 |
| 5. Reflection privacy/limitations            |      10 |
| **Tổng**                                     | **100** |

### 15.1 Full memory stack — 25 điểm

Cần có đủ 4 memory types ở mức interface: short-term, long-term profile/preference, episodic, semantic. Mỗi memory phải có cách lưu/retrieve riêng, không gộp tất cả thành một blob mơ hồ.

Backend được chấp nhận: short-term dùng list/sliding window/conversation buffer; long-term profile dùng Redis/dict/JSON/simple KV store; episodic dùng JSON list/file/log store; semantic dùng Chroma/FAISS/vector search/keyword search fallback.

### 15.2 LangGraph state/router + prompt injection — 30 điểm

Cần có `MemoryState` hoặc state dict tương đương, node/function `retrieve_memory(state)`, router gom memory từ nhiều backends vào state, prompt có section rõ cho profile/episodic/semantic/recent conversation, và có trim/token budget cơ bản.

Code shape mong đợi:

```python
class MemoryState(TypedDict):
    messages: list
    user_profile: dict
    episodes: list[dict]
    semantic_hits: list[str]
    memory_budget: int
```

Không full điểm nếu retrieve memory xong nhưng không inject vào prompt.

### 15.3 Save/update memory + conflict handling — 15 điểm

Cần update ít nhất 2 profile facts, ghi episodic memory khi task hoàn tất hoặc có outcome rõ, ưu tiên fact mới nếu user sửa fact cũ, và không append bừa khiến profile mâu thuẫn.

Test bắt buộc:

```text
User: Tôi dị ứng sữa bò.
User: À nhầm, tôi dị ứng đậu nành chứ không phải sữa bò.
Expected profile: allergy = đậu nành
```

### 15.4 Benchmark 10 multi-turn conversations — 20 điểm

`BENCHMARK.md` phải có đúng 10 multi-turn conversations hoặc tương đương. Mỗi conversation có nhiều turn, không chỉ 1 prompt đơn lẻ. Bắt buộc so sánh `no-memory` và `with-memory`.

Benchmark phải bao phủ: profile recall, conflict update, episodic recall, semantic retrieval, trim/token budget.

Mẫu bảng benchmark:

| # | Scenario                       | No-memory result | With-memory result       | Pass? |
| - | ------------------------------ | ---------------- | ------------------------ | ----- |
| 1 | Recall user name after 6 turns | Không biết       | Linh                     | Pass  |
| 2 | Allergy conflict update        | Sữa bò           | Đậu nành                 | Pass  |
| 3 | Recall previous debug lesson   | Không biết       | Dùng docker service name | Pass  |
| 4 | Retrieve FAQ chunk             | Sai/thiếu        | Đúng chunk               | Pass  |

Không bắt buộc đo latency thật. Có thể dùng word count/character count để ước lượng token/cost.

### 15.5 Reflection privacy/limitations — 10 điểm

Reflection cần trả lời: memory nào giúp agent nhất, memory nào rủi ro nhất nếu retrieve sai, nếu user yêu cầu xóa memory thì xóa ở backend nào, và điều gì làm system fail khi scale.

Bắt buộc đề cập ít nhất 1 rủi ro PII/privacy, memory nào nhạy cảm nhất, deletion/TTL/consent hoặc risk của retrieval sai, và ít nhất 1 limitation kỹ thuật.

### 15.6 Bonus và red flags

Bonus dùng để tie-break: Redis thật chạy ổn, Chroma/FAISS thật chạy ổn, LLM-based extraction có parse/error handling, token counting tốt hơn word count, graph flow demo rõ.

Red flags: chỉ có short-term + profile nhưng tự nhận full stack; name-drop LangGraph nhưng không có state/router; database thật nhưng prompt không inject memory; benchmark chỉ là 10 câu hỏi rời; không có semantic retrieval test; không có conflict update test; lưu PII nhạy cảm nhưng không nhắc consent/TTL/deletion.

### 15.7 Grading band summary

| Mức        |   Điểm | Đặc điểm                                                                 |
| ---------- | -----: | ------------------------------------------------------------------------ |
| Tốt        | 80–100 | Đủ 4 memory types, router rõ, benchmark 10 conversations, reflection tốt |
| Trung bình |  50–79 | Có phần lớn kiến trúc nhưng benchmark hoặc save/update còn yếu           |
| Kém        |   < 50 | Thiếu full stack, thiếu router, hoặc benchmark không đạt yêu cầu         |

| Category                              | Points |
| ------------------------------------- | -----: |
| 4 memory backends implemented         |     25 |
| Memory router correctness             |     15 |
| Context window management             |     15 |
| LangGraph workflow quality            |     15 |
| Benchmark design                      |     10 |
| Metrics and report quality            |     15 |
| Code quality, README, reproducibility |      5 |
| Total                                 |    100 |

---

## 16. Environment setup requirement

Project bắt buộc dùng **uv** và **venv** để quản lý môi trường Python.

### 16.1 Required tooling

Repo phải hỗ trợ setup bằng `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Nếu dùng Windows PowerShell:

```powershell
uv venv
.venv/Scripts/Activate.ps1
uv pip install -r requirements.txt
```

### 16.2 Required files

Repo cần có ít nhất:

```text
requirements.txt
.env.example
README.md
Agents.md
```

Khuyến khích có thêm:

```text
pyproject.toml
uv.lock
```

### 16.3 README requirement

README phải có phần hướng dẫn setup rõ ràng bằng `uv venv`, kích hoạt `.venv`, rồi cài dependencies bằng `uv pip install -r requirements.txt`.

### 16.4 Acceptance criteria for environment

* Không cài package trực tiếp vào global Python environment.
* Không commit thư mục `.venv/` lên GitHub.
* Repo chạy được sau khi clone mới và setup bằng `uv venv`.
* `requirements.txt` phải đủ dependency để chạy agent, benchmark và tests.
* Nếu có `uv.lock`, kết quả setup nên reproducible giữa các máy.

---

## 17. Minimal demo script requirement

Repo nên có một demo chạy được:

```bash
python -m src.main --user-id user_001 --session-id session_1
python -m src.main --user-id user_001 --session-id session_2
```

Demo cần chứng minh:

1. Session 1 lưu preference “thích Python, không thích Java”.
2. Session 2 là process mới nhưng vẫn retrieve preference từ Redis.
3. Agent gợi ý Python solution mà không hỏi lại.
4. Agent recall episode async/await và tự thêm explanation.

---

## 17. Example expected report summary

```markdown
# Benchmark Report — Lab 17 Multi-Memory Agent

## Setup

- Baseline: agent without persistent memory.
- Memory agent: LangGraph agent with short-term, Redis preference, JSON episodic, Chroma semantic memory.
- Dataset: 10 multi-turn conversations, 30 sessions total.

## Results

| Metric | Baseline | Memory Agent |
|---|---:|---:|
| Response relevance | 3.2/5 | 4.5/5 |
| User satisfaction | 3.0/5 | 4.4/5 |
| Memory hit rate | N/A | 0.82 |
| Context utilization | 0.41 | 0.68 |
| Tokens per successful answer | 950 | 780 |

## Analysis

The memory agent performs better on personalization-heavy queries, especially when user preferences and previous learning episodes are relevant. The largest gain appears in recommendation tasks and follow-up conceptual explanations.
```

---

## 18. Important implementation notes

* Memory should improve relevance, not bloat the prompt.
* Do not retrieve all memories every turn.
* Router should be explainable and logged.
* Memory writes should be conservative.
* Current user message always has higher priority than old memory.
* If memory conflicts with new user input, update memory or mark old memory stale.
* Benchmark must include both success and failure cases.
* The final report should discuss trade-offs, not only show positive numbers.
