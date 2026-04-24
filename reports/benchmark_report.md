# Benchmark Report - Lab 17 Multi-Memory Agent

## Setup

- Baseline: agent without persistent memory.
- Memory agent: LangGraph workflow with short-term, preference, episodic, and semantic memory.
- Dataset: 10 scripted multi-turn conversations.

## Aggregate Results

| Metric | Baseline | Memory Agent |
|---|---:|---:|
| Response relevance | 2.0/5 | 4.4/5 |
| User satisfaction | 2.0/5 | 4.4/5 |
| Memory hit rate | 0.0 | 0.8 |
| Context utilization | 0.25 | 0.28 |
| Tokens per successful answer | 51.2 | 57.4 |

## Conversation Results

| # | Scenario | No-memory result | With-memory result | Pass? |
|---|---|---|---|---|
| 1 | Programming preference recall | Bạn có thể bắt đầu với FastAPI, Django, Node.js Express hoặc Spring tùy mục tiêu học backend. | Dựa trên preference đã lưu (thích Python; không thích Java), Mình gợi ý FastAPI nếu bạn muốn học nhanh và xây API gọn, hoặc Django nếu cần stack đầy đủ. | Pass |
| 2 | Async confusion episode recall | Async/await giúp xử lý bất đồng bộ. `await` tạm dừng cho đến khi tác vụ hoàn thành. | Có một episode liên quan: User was confused about: Tôi bị rối async await, không hiểu await có block chương trình không.. Knowledge liên quan: Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác. Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác. | Pass |
| 3 | Response style preference | Decorator là một kỹ thuật để bọc thêm hành vi quanh một hàm. | Decorator là hàm bọc một hàm khác để thêm hành vi. Ví dụ: `@log` trên hàm `hello()` để in log trước khi gọi hàm. | Pass |
| 4 | Conflict update allergy | Mình đang dựa vào đoạn hội thoại hiện tại để tiếp tục trả lời. | Dựa trên preference đã lưu (dị ứng đậu nành), Thông tin đang lưu cho thấy bạn dị ứng đậu nành. | Pass |
| 5 | AI agents learning preference | Mình đang dựa vào đoạn hội thoại hiện tại để tiếp tục trả lời. | Dựa trên preference đã lưu (đang học AI Agents and LangGraph), Vì bạn đang học AI Agents và LangGraph, nên đi tiếp vào memory systems, tool calling và evaluation. | Pass |
| 6 | Semantic retrieval for async concept | Async/await giúp xử lý bất đồng bộ. `await` tạm dừng cho đến khi tác vụ hoàn thành. | Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác. | Pass |
| 7 | Mixed recommendation | Bạn có thể bắt đầu với FastAPI, Django, Node.js Express hoặc Spring tùy mục tiêu học backend. | Dựa trên preference đã lưu (thích Python), Mình gợi ý FastAPI nếu bạn muốn học nhanh và xây API gọn, hoặc Django nếu cần stack đầy đủ. | Pass |
| 8 | Episode plus semantic explanation | Async/await giúp xử lý bất đồng bộ. `await` tạm dừng cho đến khi tác vụ hoàn thành. | Có một episode liên quan: User was confused about: Tôi không hiểu tại sao await không block.. Knowledge liên quan: Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác. Async/await không block toàn bộ chương trình; nó tạm dừng coroutine hiện tại để event loop chạy việc khác. | Pass |
| 9 | Trim and budget pressure | Bạn có thể bắt đầu với FastAPI, Django, Node.js Express hoặc Spring tùy mục tiêu học backend. | Dựa trên preference đã lưu (không thích Java), Knowledge liên quan: Mình sẽ trả lời dựa trên query hiện tại và bộ nhớ liên quan để giữ câu trả lời đúng trong ngữ cảnh. Mình gợi ý FastAPI nếu bạn muốn học nhanh và xây API gọn, hoặc Django nếu cần stack đầy đủ. | Pass |
| 10 | Preference recall after sessions | Mình đang dựa vào đoạn hội thoại hiện tại để tiếp tục trả lời. | Dựa trên preference đã lưu (thích Python; thích câu trả lời ngắn, có ví dụ), Vì bạn đã hợp với Python, hãy bắt đầu với scripting, `requests`, file processing và task scheduling nhỏ. | Pass |

## Token Budget Breakdown - Memory Agent

| Source | Tokens | Percentage |
|---|---:|---:|
| current_query | 138 | 4.8% |
| episodic | 45 | 1.57% |
| preferences | 580 | 20.18% |
| semantic | 122 | 4.24% |
| short_term | 789 | 27.45% |
| system_prompt | 1200 | 41.75% |

## Reflection

- Preference memory gives the most visible personalization gain in recommendation tasks.
- Episodic memory is the riskiest if retrieved incorrectly because it can overfit a stale learning issue.
- Deletion must clear Redis or fallback preference storage, the JSON episodic log, and the Chroma or fallback semantic store.
- Privacy risk: stable preferences and allergy-like profile facts can become sensitive if stored without consent and TTL.
- Scaling limitation: rule-based routing and local token estimation are explainable, but weaker than model-based retrieval planning.