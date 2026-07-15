import streamlit as st
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from importlib import import_module

st.set_page_config(
    page_title="SRM CampusGPT",
    page_icon="🎓",
    layout="wide"
)

rag_module = import_module("app.generator.rag_pipeline")
ask_rag = rag_module.ask_rag

MODEL_OPTIONS = {
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Llama 3.3 70B (Groq)": "llama-3.3-70b",
    "DeepSeek R1 14B": "ollama:deepseek-r1:14b",
    "Gemma 4 E2B": "ollama:gemma4:e2b",
    "Llama 3 8B": "ollama:llama3:8b",
    "Mistral": "ollama:mistral:latest",
    "Phi-3 Mini": "ollama:phi3:mini",
    "Gemma 2 2B": "ollama:gemma2:2b"
}

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("🎓 SRM CampusGPT")
    st.caption("AI Knowledge Assistant")
    
    st.divider()
    
    st.subheader("Model Selection")
    selected_model_name = st.selectbox(
        "Choose Model",
        list(MODEL_OPTIONS.keys()),
        index=0
    )
    selected_model = MODEL_OPTIONS[selected_model_name]
    
    st.divider()
    
    st.subheader("Settings")
    detailed = st.toggle("Detailed Answers", value=True)
    show_sources = st.toggle("Show Sources", value=True)
    show_docs = st.toggle("Show Documents", value=False)
    show_debug = st.toggle("Debug Mode", value=False)
    
    st.divider()
    
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main content
st.title("SRM CampusGPT")
st.write("Ask any question about SRM Institute")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
question = st.chat_input("Ask anything about SRM...")

num_predict = 2500 if detailed else 1200

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.chat_message("user"):
        st.write(question)
    
    with st.chat_message("assistant"):
        try:
            with st.spinner("Processing..."):
                result = ask_rag(
                    question=question,
                    model_name=selected_model,
                    num_predict=num_predict
                )
            
            answer = result.get("answer", "No answer generated.")
            confidence = result.get("confidence", 0)
            docs_info = result.get("docs_info", [])
            retrieved_docs = result.get("documents", [])
            response_time = result.get("response_time", 0)
            
            st.write(answer)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Model", selected_model_name)
            with col2:
                st.metric("Confidence", f"{confidence}%")
            with col3:
                st.metric("Sources", len(docs_info))
            with col4:
                st.metric("Response Time", f"{response_time}s")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.write(traceback.format_exc())

# Show sources if enabled
if question and 'result' in locals() and show_sources and docs_info:
    st.divider()
    st.subheader("Sources")
    
    for idx, source in enumerate(docs_info[:10], start=1):
        source_name = source.get("source", "unknown")
        chunk_id = str(source.get("chunk_id", "unknown"))[:30]  # ✅ FIXED: Convert to string first
        
        with st.expander(f"Source {idx} - {source_name}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Source", source_name)
            with col2:
                distance = source.get("distance", 0)
                st.metric("Distance", round(distance, 4))
            with col3:
                st.metric("Chunk ID", chunk_id)

# Show documents if enabled
if question and 'result' in locals() and show_docs and retrieved_docs:
    st.divider()
    st.subheader("Retrieved Documents")
    
    for idx, doc in enumerate(retrieved_docs, start=1):
        if isinstance(doc, str):  # ✅ FIXED: Type check
            with st.expander(f"Document {idx}"):
                st.code(doc[:5000])

# Debug mode
if question and 'result' in locals() and show_debug:
    st.divider()
    st.subheader("Debug")
    
    debug_info = {
        "question": question,
        "model": selected_model_name,
        "confidence": result.get("confidence", 0),
        "sources": len(result.get("docs_info", [])),
        "documents": len(result.get("documents", [])),
        "response_time": result.get("response_time", 0),
        "confidence_label": result.get("confidence_label", "Unknown")
    }
    
    st.json(debug_info)