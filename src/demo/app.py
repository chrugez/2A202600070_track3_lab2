from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app_service import AgentService


st.set_page_config(page_title="Lab 17 Multi-Memory Demo", layout="wide")
st.title("Lab 17 Multi-Memory Agent Demo")

if "service" not in st.session_state:
    st.session_state.service = AgentService()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Session")
    user_id = st.text_input("User ID", value="user_001")
    session_id = st.text_input("Session ID", value="session_1")
    mode = st.selectbox("Agent Mode", options=["memory", "baseline"], index=0)
    if st.button("Reset current chat view"):
        st.session_state.chat_history = []

left, right = st.columns([2, 1])

with left:
    for role, content in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(content)
    prompt = st.chat_input("Nhập câu hỏi...")
    if prompt:
        st.session_state.chat_history.append(("user", prompt))
        result = st.session_state.service.run_agent_turn(user_id, session_id, prompt, mode)
        st.session_state.last_result = result
        st.session_state.chat_history.append(("assistant", result["response"]))
        st.rerun()

with right:
    st.subheader("Memory panel")
    result = st.session_state.get("last_result")
    if result:
        st.markdown("**Router decision**")
        st.json(result["route_decision"])
        st.markdown("**Retrieved memories**")
        st.json(result["retrieved_memories"])
        st.markdown("**Pending or applied writes**")
        st.json(result["memory_writes"])
        st.markdown("**Metrics**")
        st.json(result["metrics"])
    else:
        st.info("Chưa có lượt hội thoại nào.")
