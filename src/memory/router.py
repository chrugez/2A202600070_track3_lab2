from __future__ import annotations


from src.utils import normalize_text


class MemoryRouter:
    def route(self, user_query: str, session_context: list[dict]) -> dict:
        lowered = normalize_text(user_query)
        use_short_term = any(
            phrase in lowered
            for phrase in ["y tren", "cai tren", "vua noi", "doan do", "y thu", "follow up", "nhu tren"]
        )
        use_preferences = any(
            phrase in lowered
            for phrase in [
                "goi y",
                "nen hoc",
                "phu hop",
                "ca nhan hoa",
                "khuyen",
                "de xuat",
                "framework nao",
                "nhac lai",
                "di ung",
                "automation",
                "bat dau tu dau",
            ]
        )
        use_episodic = any(
            phrase in lowered
            for phrase in ["lan truoc", "truoc day", "hom no", "toi tung", "bi roi", "nho lai", "giai thich lai"]
        )
        use_semantic = any(
            phrase in lowered
            for phrase in ["giai thich", "la gi", "khai niem", "concept", "fact", "tai sao", "how", "what is"]
        )
        if use_preferences and any(term in lowered for term in ["framework", "chu de", "tai sao", "automation"]):
            use_semantic = True
        if session_context and len(session_context) > 1:
            use_short_term = use_short_term or "?" not in lowered
        if use_preferences and use_semantic:
            reason = "Recommendation query benefits from user preferences and conceptual knowledge."
        elif use_episodic and use_semantic:
            reason = "The user refers to a previous learning event and asks for explanation."
        elif use_short_term:
            reason = "The user appears to refer to the current session context."
        elif use_preferences:
            reason = "The user requests a personalized recommendation."
        elif use_episodic:
            reason = "The user refers to a previous experience."
        elif use_semantic:
            reason = "The user asks for factual or conceptual knowledge."
        else:
            use_short_term = True
            reason = "Default to recent context when the query is otherwise ambiguous."
        return {
            "use_short_term": use_short_term,
            "use_preferences": use_preferences,
            "use_episodic": use_episodic,
            "use_semantic": use_semantic,
            "reason": reason,
        }
