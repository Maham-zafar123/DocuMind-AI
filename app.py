from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.config import APP_NAME, CHUNK_OVERLAP, CHUNK_SIZE, SUPPORTED_TYPES, TOP_K
from src.document_loader import chunk_text, extract_text
from src.gemini_client import generate_text
from src.prompts import (
    COMPARE_PROMPT,
    FLASHCARD_PROMPT,
    QA_PROMPT,
    QUIZ_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)
from src.rag_engine import LocalRAGEngine
from src.report_generator import create_pdf_report

load_dotenv()

st.set_page_config(page_title=APP_NAME, page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")


def init_state():
    if "rag" not in st.session_state:
        st.session_state.rag = LocalRAGEngine()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_output" not in st.session_state:
        st.session_state.last_output = ""
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"


def make_context(results):
    parts = []
    for chunk, score in results:
        parts.append(
            f"Source: {chunk.filename} | Chunk: {chunk.chunk_id} | Relevance: {score:.2f}\n{chunk.text}"
        )
    return "\n\n---\n\n".join(parts)


def get_all_context(limit_chars=12000):
    chunks = st.session_state.rag.chunks
    text = "\n\n".join(
        [f"Source: {c.filename} | Chunk: {c.chunk_id}\n{c.text}" for c in chunks]
    )
    return text[:limit_chars]


def apply_theme(theme: str):
    dark = theme == "Dark"
    bg = "#0f172a" if dark else "#f7f8fc"
    panel = "#111827" if dark else "#ffffff"
    panel2 = "#1f2937" if dark else "#f8fafc"
    text = "#e5e7eb" if dark else "#1f2937"
    muted = "#94a3b8" if dark else "#64748b"
    border = "#334155" if dark else "#e5e7eb"
    accent = "#8b5cf6"
    accent2 = "#ec4899"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg};
            color: {text};
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        [data-testid="stSidebar"] {{
            display: none;
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        .hero {{
            padding: 34px 34px;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(139,92,246,.18), rgba(236,72,153,.12)), {panel};
            border: 1px solid {border};
            box-shadow: 0 18px 45px rgba(15, 23, 42, .08);
            margin-bottom: 22px;
        }}
        .app-title {{
            font-size: 46px;
            line-height: 1.1;
            font-weight: 900;
            margin: 0;
            color: {text};
        }}
        .subtitle {{
            font-size: 18px;
            color: {muted};
            margin-top: 10px;
            margin-bottom: 0;
        }}
        .badge {{
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
            color: white;
            background: linear-gradient(90deg, {accent}, {accent2});
            margin-bottom: 13px;
        }}
        .section-card {{
            padding: 22px 24px;
            border-radius: 22px;
            background: {panel};
            border: 1px solid {border};
            box-shadow: 0 12px 30px rgba(15, 23, 42, .06);
            margin-bottom: 18px;
        }}
        .mini-card {{
            padding: 18px;
            border-radius: 18px;
            background: {panel2};
            border: 1px solid {border};
            min-height: 112px;
        }}
        .mini-card h4 {{
            margin: 0 0 8px 0;
            color: {muted};
            font-size: 14px;
            font-weight: 700;
        }}
        .mini-card p {{
            margin: 0;
            color: {text};
            font-size: 34px;
            font-weight: 800;
        }}
        .support-text {{
            color: {muted};
            font-size: 14px;
        }}
        div[data-testid="stMetric"] {{
            background: {panel};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 16px 18px;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            border-bottom: 1px solid {border};
        }}
        .stTabs [data-baseweb="tab"] {{
            background: {panel};
            border-radius: 12px 12px 0 0;
            padding: 10px 16px;
            border: 1px solid {border};
            border-bottom: none;
        }}
        .stTextInput input, .stTextArea textarea {{
            border-radius: 14px !important;
        }}
        .stButton>button {{
            border-radius: 14px;
            border: 0;
            font-weight: 700;
            background: linear-gradient(90deg, {accent}, {accent2});
            color: white;
            padding: .65rem 1.2rem;
        }}
        .stDownloadButton>button {{
            border-radius: 14px;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Initialize session state first
init_state()

# Extra safety check
if "rag" not in st.session_state:
    st.session_state.rag = LocalRAGEngine()

if "history" not in st.session_state:
    st.session_state.history = []

if "last_output" not in st.session_state:
    st.session_state.last_output = ""

if "theme" not in st.session_state:
    st.session_state.theme = "Light"

# Top controls
left, right = st.columns([0.75, 0.25])


with right:
    selected_theme = st.radio(
        "Theme",
        ["Light", "Dark"],
        horizontal=True,
        label_visibility="collapsed",
        index=0 if st.session_state.theme == "Light" else 1,
    )
    st.session_state.theme = selected_theme
    
apply_theme(st.session_state.theme)

st.markdown(
    """
    <div class="hero">
        <div class="badge">Generative AI + RAG Project</div>
        <h1 class="app-title">🧠 DocuMind AI</h1>
        <p class="subtitle">Upload documents, ask questions, generate summaries, compare files, create quizzes, and export reports.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Setup is now on the main screen instead of hidden sidebar.
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("📤 Upload & Build Knowledge Base")
api_present = bool(os.getenv("GEMINI_API_KEY"))
api_col, upload_col = st.columns([0.28, 0.72])
with api_col:
    if api_present:
        st.success("Gemini API key loaded")
    else:
        st.warning("Add GEMINI_API_KEY in your .env file")
    st.caption("Supported files: PDF, DOCX, PPTX, TXT")
with upload_col:
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        help="Upload one or more documents, then click Build Knowledge Base.",
    )
    build_btn = st.button("Build Knowledge Base", type="primary", width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

if build_btn:
    if not uploaded_files:
        st.error("Please upload at least one document.")
    else:
        all_chunks = []
        with st.spinner("Reading and indexing documents..."):
            for file in uploaded_files:
                try:
                    text = extract_text(file)
                    chunks = chunk_text(file.name, text, CHUNK_SIZE, CHUNK_OVERLAP)
                    all_chunks.extend(chunks)
                except Exception as exc:
                    st.error(f"Could not process {file.name}: {exc}")
            if all_chunks:
                st.session_state.rag.build_index(all_chunks)
                st.success(f"Knowledge base created with {len(all_chunks)} chunks.")
            else:
                st.error("No readable text found in uploaded files.")

stats = st.session_state.rag.stats()
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("📊 Project Dashboard")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="mini-card"><h4>Uploaded Files</h4><p>{stats["file_count"]}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="mini-card"><h4>Text Chunks</h4><p>{stats["chunk_count"]}</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="mini-card"><h4>Questions Asked</h4><p>{len(st.session_state.history)}</p></div>', unsafe_allow_html=True)

if stats["files"]:
    st.markdown("#### 📁 Indexed Files")
    files_df = pd.DataFrame({"File Name": stats["files"]})
    st.dataframe(files_df, width="stretch", hide_index=True)
else:
    st.info("No files indexed yet. Upload documents above and build the knowledge base.")
st.markdown('</div>', unsafe_allow_html=True)

main_tab, summary_tab, compare_tab, quiz_tab, flash_tab, report_tab = st.tabs([
    "💬 Ask Questions", "📑 Summarize", "⚖️ Compare", "📝 Quiz", "🎴 Flashcards", "📄 Report"
])

with main_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Ask anything about your uploaded documents")
    question = st.text_input("Your question", placeholder="Example: What is the GPA mentioned in the resume?")
    ask_col, clear_col = st.columns([0.75, 0.25])
    with ask_col:
        ask_btn = st.button("Get Answer", width="stretch")
    with clear_col:
        if st.button("Clear History", width="stretch"):
            st.session_state.history = []
            st.session_state.last_output = ""
            st.success("History cleared.")
    if ask_btn:
        if not st.session_state.rag.is_ready():
            st.error("Please upload documents and build the knowledge base first.")
        elif not question.strip():
            st.error("Please enter a question.")
        else:
            results = st.session_state.rag.search(question, TOP_K)
            if not results:
                st.warning("No relevant text found. Try a different question.")
            else:
                context = make_context(results)
                prompt = QA_PROMPT.format(question=question, context=context)
                with st.spinner("Gemini is analyzing the documents..."):
                    answer = generate_text(prompt, SYSTEM_PROMPT)
                st.session_state.last_output = answer
                st.session_state.history.append({"question": question, "answer": answer})
                st.markdown("### Answer")
                st.markdown(answer)
                with st.expander("Retrieved Sources"):
                    rows = [
                        {"File": c.filename, "Chunk": c.chunk_id, "Relevance": round(score, 3), "Text": c.text[:300]}
                        for c, score in results
                    ]
                    st.dataframe(pd.DataFrame(rows), width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with summary_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Generate document summaries")
    style = st.selectbox("Summary style", ["short", "detailed", "bullet-point", "executive"])
    if st.button("Generate Summary", width="stretch"):
        if not st.session_state.rag.is_ready():
            st.error("Build the knowledge base first.")
        else:
            prompt = SUMMARY_PROMPT.format(style=style, context=get_all_context())
            with st.spinner("Creating summary..."):
                output = generate_text(prompt, SYSTEM_PROMPT)
            st.session_state.last_output = output
            st.markdown(output)
    st.markdown('</div>', unsafe_allow_html=True)

with compare_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Compare uploaded documents")
    if st.button("Compare Documents", width="stretch"):
        if not st.session_state.rag.is_ready():
            st.error("Build the knowledge base first.")
        elif stats["file_count"] < 2:
            st.error("Upload at least two documents for comparison.")
        else:
            prompt = COMPARE_PROMPT.format(context=get_all_context())
            with st.spinner("Comparing documents..."):
                output = generate_text(prompt, SYSTEM_PROMPT)
            st.session_state.last_output = output
            st.markdown(output)
    st.markdown('</div>', unsafe_allow_html=True)

with quiz_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Generate quiz from documents")
    num_questions = st.slider("Number of questions", 3, 15, 5)
    if st.button("Generate Quiz", width="stretch"):
        if not st.session_state.rag.is_ready():
            st.error("Build the knowledge base first.")
        else:
            prompt = QUIZ_PROMPT.format(num_questions=num_questions, context=get_all_context())
            with st.spinner("Generating quiz..."):
                output = generate_text(prompt, SYSTEM_PROMPT)
            st.session_state.last_output = output
            st.markdown(output)
    st.markdown('</div>', unsafe_allow_html=True)

with flash_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Create revision flashcards")
    if st.button("Generate Flashcards", width="stretch"):
        if not st.session_state.rag.is_ready():
            st.error("Build the knowledge base first.")
        else:
            prompt = FLASHCARD_PROMPT.format(context=get_all_context())
            with st.spinner("Generating flashcards..."):
                output = generate_text(prompt, SYSTEM_PROMPT)
            st.session_state.last_output = output
            st.markdown(output)
    st.markdown('</div>', unsafe_allow_html=True)

with report_tab:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Download latest AI output as PDF")
    if st.session_state.last_output:
        st.text_area("Latest output", st.session_state.last_output, height=250)
        if st.button("Create PDF Report", width="stretch"):
            path = create_pdf_report("DocuMind AI Report", st.session_state.last_output)
            with open(path, "rb") as f:
                st.download_button("Download PDF", f, file_name=Path(path).name, mime="application/pdf")
    else:
        st.info("Generate an answer, summary, comparison, quiz, or flashcards first.")
    st.markdown('</div>', unsafe_allow_html=True)
