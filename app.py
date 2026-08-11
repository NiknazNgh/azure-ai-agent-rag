from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.config import load_settings
from src.foundry_rag import FoundryRAGClient


ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / ".rag_resources.json"

st.set_page_config(
    page_title="Operations Intelligence RAG Agent",
    page_icon="🤖",
    layout="centered",
)

st.title("Operations Intelligence RAG Agent")
st.caption(
    "Microsoft Foundry + Python + File Search | Retrieval-grounded demo using synthetic operations data"
)

if not STATE_FILE.exists():
    st.error("Resources are not initialized. Run `python scripts/ingest.py` first.")
    st.stop()

state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
settings = load_settings()

@st.cache_resource
def get_client() -> FoundryRAGClient:
    return FoundryRAGClient(
        settings.project_endpoint,
        settings.model_deployment_name,
    )

client = get_client()

with st.sidebar:
    st.subheader("Demo knowledge base")
    for filename in state.get("documents", []):
        st.write(f"• {filename}")

    st.divider()
    st.write(f"**Model deployment:** `{state['model_deployment_name']}`")

    if st.button("New conversation"):
        st.session_state.pop("conversation_id", None)
        st.session_state.pop("messages", None)
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

examples = [
    "Does the July 2026 energy increase require a formal investigation?",
    "What caused the July energy increase?",
    "If energy increases 24% next month, what action is required?",
]

st.write("**Try a grounded question:**")
selected = st.selectbox("Example", ["Choose an example..."] + examples, label_visibility="collapsed")

prompt = st.chat_input("Ask about the monthly report, policy, or SOP...")
if not prompt and selected != "Choose an example...":
    prompt = selected

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving evidence and reasoning..."):
            answer, conversation_id = client.ask(
                agent_name=state["agent_name"],
                question=prompt,
                conversation_id=st.session_state.get("conversation_id"),
            )
            st.session_state.conversation_id = conversation_id
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
