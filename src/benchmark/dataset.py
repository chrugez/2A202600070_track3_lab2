from __future__ import annotations


def build_dataset() -> list[dict]:
    return [
        {
            "id": 1,
            "scenario": "Programming preference recall",
            "sessions": [
                ["Tôi thích Python, không thích Java."],
                ["Tôi nên học framework backend nào?"],
            ],
            "expected_keywords": ["Python", "FastAPI"],
        },
        {
            "id": 2,
            "scenario": "Async confusion episode recall",
            "sessions": [
                ["Tôi bị rối async await, không hiểu await có block chương trình không."],
                ["Lần trước tôi bị rối phần async gì đó, giải thích asyncio queue giúp tôi."],
            ],
            "expected_keywords": ["event loop", "không block"],
        },
        {
            "id": 3,
            "scenario": "Response style preference",
            "sessions": [
                ["Tôi thích câu trả lời ngắn, có ví dụ code."],
                ["Giải thích decorator trong Python."],
            ],
            "expected_keywords": ["Decorator", "ví dụ"],
        },
        {
            "id": 4,
            "scenario": "Conflict update allergy",
            "sessions": [
                ["Tôi dị ứng sữa bò."],
                ["À nhầm, tôi dị ứng đậu nành chứ không phải sữa bò."],
                ["Hãy nhắc lại dị ứng của tôi."],
            ],
            "expected_keywords": ["đậu nành"],
        },
        {
            "id": 5,
            "scenario": "AI agents learning preference",
            "sessions": [
                ["Tôi đang học AI Agents và LangGraph."],
                ["Tôi nên học chủ đề nào tiếp theo?"],
            ],
            "expected_keywords": ["LangGraph", "AI"],
        },
        {
            "id": 6,
            "scenario": "Semantic retrieval for async concept",
            "sessions": [
                ["Giải thích async await trong Python."],
                ["Await có block cả chương trình không?"],
            ],
            "expected_keywords": ["không block", "coroutine"],
        },
        {
            "id": 7,
            "scenario": "Mixed recommendation",
            "sessions": [
                ["Tôi thích Python, đang học backend."],
                ["Tôi nên học framework nào tiếp theo và tại sao?"],
            ],
            "expected_keywords": ["Python", "FastAPI"],
        },
        {
            "id": 8,
            "scenario": "Episode plus semantic explanation",
            "sessions": [
                ["Tôi không hiểu tại sao await không block."],
                ["Lần trước tôi từng rối ở async, giải thích lại cho tôi theo từng bước."],
            ],
            "expected_keywords": ["từng bước", "không block"],
        },
        {
            "id": 9,
            "scenario": "Trim and budget pressure",
            "sessions": [
                [
                    "Tôi sẽ gửi rất nhiều context để test token budget.",
                    "Đây là ghi chú 1 về Python và backend.",
                    "Đây là ghi chú 2 về Java mà tôi không thích.",
                    "Đây là ghi chú 3 về async await.",
                    "Đây là ghi chú 4 về FastAPI.",
                ],
                ["Tổng hợp cho tôi framework phù hợp nhất."],
            ],
            "expected_keywords": ["FastAPI", "Python"],
        },
        {
            "id": 10,
            "scenario": "Preference recall after sessions",
            "sessions": [
                ["Tôi thích Python và tôi muốn trả lời ngắn."],
                ["Nếu học automation thì nên bắt đầu từ đâu?"],
            ],
            "expected_keywords": ["Python", "automation"],
        },
    ]
