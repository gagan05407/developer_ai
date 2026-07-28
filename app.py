import os
import time
from pathlib import Path
import streamlit as st
import config
from vectorstore import ingest_pdf
from graph import graph
import memory

# Page Configuration
st.set_page_config(
    page_title="Developer AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-load Persistent LTM Chat History on Launch
if "messages" not in st.session_state:
    st.session_state.messages = memory.load_chat_history("default_session")
if "current_agent" not in st.session_state:
    st.session_state.current_agent = "None"
if "last_tool_used" not in st.session_state:
    st.session_state.last_tool_used = "None"
if "retrieved_chunks" not in st.session_state:
    st.session_state.retrieved_chunks = []
if "last_reasoning_trace" not in st.session_state:
    st.session_state.last_reasoning_trace = []
if "last_citations" not in st.session_state:
    st.session_state.last_citations = []

# Title Header
st.title("🤖 Developer AI Assistant")
st.caption("Production-Grade Multi-Agent System with Persistent LTM (SQLite), Reasoning Traces, Streaming, Web Search & Citations")

# Sidebar Configuration
with st.sidebar:
    st.header("📂 Document Management")
    uploaded_files = st.file_uploader(
        "Upload PDF Files for RAG Indexing",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select PDFs to index into ChromaDB vector database"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            save_path = config.UPLOADS_DIR / uploaded_file.name
            if not save_path.exists():
                save_path.write_bytes(uploaded_file.getbuffer())
                with st.spinner(f"Indexing '{uploaded_file.name}' into ChromaDB..."):
                    try:
                        chunks_count = ingest_pdf(str(save_path))
                        st.success(f"Indexed '{uploaded_file.name}' ({chunks_count} chunks stored).")
                    except Exception as e:
                        st.error(f"Failed to index '{uploaded_file.name}': {e}")

    st.divider()

    # System Status Telemetry
    st.header("📊 System State & Telemetry")
    
    # Active Agent Indicator
    st.subheader("🤖 Active Agent")
    agent_badges = {
        "general": ("🟢", "General Agent"),
        "docs": ("📘", "Documentation Agent"),
        "debug": ("🐞", "Debug Agent"),
        "None": ("⚪", "None")
    }
    badge_icon, badge_label = agent_badges.get(st.session_state.current_agent, ("⚪", st.session_state.current_agent))
    st.markdown(f"### {badge_icon} **{badge_label}**")

    # Executed Tools Indicator
    st.subheader("🛠️ Executed Tools")
    st.info(f"Last Tool Used: `{st.session_state.last_tool_used}`")

    # Persistent Long-Term Memory (LTM) Inspector
    st.subheader("💾 Long-Term Memory (LTM)")
    user_facts = memory.load_user_facts()
    if user_facts:
        with st.expander("Saved User Profile Facts", expanded=True):
            for k, v in user_facts.items():
                st.markdown(f"- **{k}**: `{v}`")
    else:
        st.caption("No persistent user facts saved yet.")

    # Reasoning Trace Inspector
    st.subheader("💭 Agent Reasoning Trace")
    if st.session_state.last_reasoning_trace:
        with st.expander("Inspect Step Traces", expanded=True):
            for step in st.session_state.last_reasoning_trace:
                st.markdown(f"- `{step}`")
    else:
        st.caption("No reasoning trace yet.")

    # Retrieved Chunks & Sources Inspector
    st.subheader("📌 Sources & Citations")
    if st.session_state.last_citations:
        for cit in st.session_state.last_citations:
            with st.expander(f"{cit.get('label', '[Source]')} - {cit.get('source', 'Unknown')}"):
                st.text(cit.get('content', ''))
    elif st.session_state.retrieved_chunks:
        for idx, chunk in enumerate(st.session_state.retrieved_chunks, 1):
            with st.expander(f"Chunk {idx}"):
                st.text(chunk)
    else:
        st.caption("No sources retrieved yet.")

    st.divider()

    # Clear Session History Button
    if st.button("🗑️ Clear Active Session Chat", use_container_width=True):
        st.session_state.messages = []
        memory.clear_chat_history("default_session")
        st.session_state.current_agent = "None"
        st.session_state.last_tool_used = "None"
        st.session_state.retrieved_chunks = []
        st.session_state.last_reasoning_trace = []
        st.session_state.last_citations = []
        st.rerun()

    # Reset Entire Persistent LTM Button
    if st.button("🔥 Reset Entire Persistent LTM", use_container_width=True):
        memory.clear_all_ltm()
        st.session_state.messages = []
        st.session_state.current_agent = "None"
        st.session_state.last_tool_used = "None"
        st.session_state.retrieved_chunks = []
        st.session_state.last_reasoning_trace = []
        st.session_state.last_citations = []
        st.rerun()

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg and msg["trace"]:
            with st.expander("💭 Agent Reasoning Trace"):
                for step in msg["trace"]:
                    st.markdown(f"- `{step}`")

# Chat Input Handler
user_query = st.chat_input("Ask a question, request code debugging, or query uploaded docs...")

if user_query:
    # Save User Turn to SQLite Persistent LTM & Session
    memory.save_chat_message("default_session", "user", user_query, agent="user")
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("user"):
        st.markdown(user_query)

    # Process through LangGraph Multi-Agent Workflow
    with st.chat_message("assistant"):
        with st.spinner("Processing through Multi-Agent Graph with Persistent LTM..."):
            try:
                result = graph.invoke({
                    "question": user_query,
                    "messages": st.session_state.messages,
                    "user_facts": {},
                    "route": "",
                    "retrieved_docs": [],
                    "tool_used": "",
                    "reasoning_trace": [],
                    "citations": [],
                    "answer": ""
                })

                route = result.get("route", "general")
                tool_used = result.get("tool_used", "None")
                retrieved_docs = result.get("retrieved_docs", [])
                reasoning_trace = result.get("reasoning_trace", [])
                citations = result.get("citations", [])
                raw_answer = result.get("answer", "")

                # Update State Telemetry
                st.session_state.current_agent = route
                st.session_state.last_tool_used = tool_used
                st.session_state.retrieved_chunks = retrieved_docs
                st.session_state.last_reasoning_trace = reasoning_trace
                st.session_state.last_citations = citations

                # Format Agent Badge Prefix
                if route == "docs":
                    badge_prefix = "📘 **Documentation Agent**\n\n"
                elif route == "debug":
                    badge_prefix = "🐞 **Debug Agent**\n\n"
                else:
                    badge_prefix = "🟢 **General Agent**\n\n"

                full_text = badge_prefix + raw_answer

                # Streaming Token Output Generator
                def response_generator(text: str):
                    for word in text.split(" "):
                        yield word + " "
                        time.sleep(0.02)

                formatted_response = st.write_stream(response_generator(full_text))

                # Display Reasoning Trace expander under message
                if reasoning_trace:
                    with st.expander("💭 Agent Reasoning Trace"):
                        for step in reasoning_trace:
                            st.markdown(f"- `{step}`")

            except Exception as e:
                formatted_response = f"❌ **Error executing Graph**: {e}"
                st.markdown(formatted_response)

    # Save Assistant Response to Session State
    st.session_state.messages.append({
        "role": "assistant",
        "content": formatted_response,
        "agent": route,
        "trace": reasoning_trace
    })