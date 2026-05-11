"""
app.py — Production-grade Streamlit UI for Research Paper Q&A

Features:
  - Responsive two-column layout (upload + chat)
  - Advanced error handling & user feedback
  - Performance tracking & metrics
  - Semantic query caching
  - Source citation with page numbers
  - Suggested questions for exploration
"""

import streamlit as st
import tempfile
import os
import time
import logging
from dotenv import load_dotenv
from rag_pipeline import build_rag_pipeline, ask, clear_cache

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Paper Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Google Font ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---- Background ---- */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    border-right: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(12px);
}

/* ---- Title ---- */
h1 {
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
    font-size: 2.4rem !important;
}

h3 { color: #e2e8f0 !important; }

/* ---- Cards ---- */
.answer-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-top: 1rem;
    backdrop-filter: blur(8px);
    animation: fadeIn 0.4s ease;
    line-height: 1.6;
}

.source-card {
    background: rgba(255,255,255,0.04);
    border-left: 3px solid #a78bfa;
    border-radius: 0 12px 12px 0;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.5;
}

.error-card {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 12px;
    padding: 1rem;
    color: #fecaca;
}

.success-card {
    background: rgba(52,211,153,0.15);
    border: 1px solid rgba(52,211,153,0.4);
    border-radius: 12px;
    padding: 1rem;
    color: #86efac;
}

/* ---- Metric pills ---- */
.metric-pill {
    display: inline-block;
    background: rgba(167,139,250,0.15);
    border: 1px solid rgba(167,139,250,0.4);
    color: #a78bfa;
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.8rem;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-weight: 500;
}

.stat-badge {
    display: inline-block;
    background: rgba(96, 165, 250, 0.1);
    border: 1px solid rgba(96, 165, 250, 0.3);
    color: #60a5fa;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.4rem;
}

/* ---- Buttons ---- */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s;
}
.stButton > button:hover { 
    opacity: 0.85;
    transform: translateY(-1px);
}
.stButton > button:disabled {
    opacity: 0.5;
}

/* ---- Input boxes ---- */
.stTextInput > div > div > input,
.stTextArea textarea {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(167,139,250,0.4) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}

/* ---- File uploader ---- */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.04) !important;
    border: 2px dashed rgba(167,139,250,0.4) !important;
    border-radius: 16px !important;
}

/* ---- Divider ---- */
hr { border-color: rgba(255,255,255,0.1); }

/* ---- Fade-in animation ---- */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---- Chat history ---- */
.chat-user {
    background: rgba(99,102,241,0.2);
    border-radius: 12px 12px 4px 12px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    text-align: right;
    color: #e0e7ff;
    font-weight: 500;
}
.chat-bot {
    background: rgba(255,255,255,0.06);
    border-radius: 12px 12px 12px 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    color: #e2e8f0;
    border-left: 3px solid #a78bfa;
}

/* ---- Expander ---- */
.streamlit-expanderHeader { color: #e2e8f0 !important; }

/* ---- Info/Warning boxes ---- */
.stInfo, .stWarning, .stError { border-radius: 12px !important; }

</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "chain" not in st.session_state:
    st.session_state.chain = None
    st.session_state.pipeline_metadata = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "num_chunks" not in st.session_state:
    st.session_state.num_chunks = 0
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""
if "query_count" not in st.session_state:
    st.session_state.query_count = 0


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.divider()

    # API Key input with validation
    api_key_input = st.text_input(
        "🔑 Google API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Get your free key at https://aistudio.google.com"
    )
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input
        st.markdown('<span class="metric-pill">✅ API Key Set</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="metric-pill">⚠️ No API Key</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🎛️ Retrieval Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.slider(
            "Chunk Size",
            200, 1000, 500, 50,
            help="Larger chunks = more context but slower"
        )
    with col2:
        top_k = st.slider(
            "Retrieved Chunks (k)",
            1, 10, 4, 1,
            help="More chunks = better coverage but slower"
        )
    
    chunk_overlap = st.slider(
        "Chunk Overlap",
        0, 200, 50, 10,
        help="Overlap for better context continuity"
    )

    st.divider()
    st.markdown("### 📋 Session Statistics")
    
    if st.session_state.chain:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div style="text-align:center;"><span class="metric-pill">{st.session_state.num_chunks}</span><br/><small style="color:#94a3b8;">Chunks</small></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="text-align:center;"><span class="metric-pill">{len(st.session_state.chat_history)}</span><br/><small style="color:#94a3b8;">Q&As</small></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div style="text-align:center;"><span class="metric-pill">{st.session_state.query_count}</span><br/><small style="color:#94a3b8;">Total Queries</small></div>', unsafe_allow_html=True)
        
        st.divider()
        st.markdown(f"**📄 Loaded:** {st.session_state.pdf_name}")
        
        col_clear, col_cache = st.columns(2)
        with col_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.chain = None
                st.session_state.pipeline_metadata = None
                st.session_state.chat_history = []
                st.session_state.num_chunks = 0
                st.session_state.pdf_name = ""
                st.session_state.query_count = 0
                st.rerun()
        with col_cache:
            if st.button("🔄 Clear Cache", use_container_width=True):
                clear_cache()
                st.toast("Cache cleared!", icon="✅")
    else:
        st.info("👆 Upload a PDF to begin")

    st.divider()
    st.markdown("""
    ### 📚 Built With
    - **LLM:** Gemini 2.5 Flash
    - **Embeddings:** all-MiniLM-L6-v2
    - **Vector DB:** ChromaDB
    - **Framework:** LangChain
    - **UI:** Streamlit
    
    <small style='color:#64748b;'>v2.0 - Production Ready</small>
    """, unsafe_allow_html=True)


# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("# 📄 Research Paper Q&A")
st.markdown(
    "*Upload any research PDF and ask questions using RAG + Gemini 2.5 Flash*",
    help="RAG = Retrieval-Augmented Generation"
)
st.divider()

col_upload, col_chat = st.columns([1, 1.6], gap="large")

# ── Left: Upload ───────────────────────────────────────────────────────────────
with col_upload:
    st.markdown("### 📤 Upload Paper")
    
    uploaded = st.file_uploader(
        "Drop a PDF here or click to browse",
        type="pdf",
        label_visibility="collapsed"
    )

    if uploaded:
        # Check if new file
        if uploaded.name != st.session_state.pdf_name or st.session_state.chain is None:
            if not os.environ.get("GOOGLE_API_KEY"):
                st.error("⚠️ **API Key Required**\n\nPlease enter your Google API Key in the Configuration panel on the left.")
            else:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    f.write(uploaded.read())
                    tmp_path = f.name

                try:
                    with st.spinner("🔄 **Processing PDF...**\n\n⏳ Parsing, chunking, and embedding... (~30s)"):
                        chain, num_chunks, metadata = build_rag_pipeline(
                            tmp_path,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            top_k=top_k,
                        )
                        
                        st.session_state.chain = chain
                        st.session_state.pipeline_metadata = metadata
                        st.session_state.num_chunks = num_chunks
                        st.session_state.pdf_name = uploaded.name
                        st.session_state.chat_history = []
                        st.session_state.query_count = 0
                        
                        # Success feedback
                        st.success("✅ **PDF ready!**")
                        st.toast(f"Loaded {uploaded.name} with {num_chunks} chunks", icon="📄")
                        
                except FileNotFoundError as e:
                    st.error(f"❌ **File Error**\n\n{str(e)}")
                except ValueError as e:
                    st.error(f"❌ **PDF Processing Error**\n\nCouldn't extract text from this PDF. Try a different file.\n\n*Details: {str(e)}*")
                except RuntimeError as e:
                    st.error(f"❌ **Configuration Error**\n\n{str(e)}")
                except Exception as e:
                    logger.exception("Unexpected error during PDF processing")
                    st.error(f"❌ **Unexpected Error**\n\n{str(e)}")
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

    # Show status if PDF loaded
    if st.session_state.chain:
        st.markdown("""
        <div class='success-card'>
        ✅ <b>Ready to Answer Questions</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='margin-top:0.8rem;'>
        <span class="stat-badge">{st.session_state.num_chunks} chunks</span>
        <span class="stat-badge">Top-{top_k} retrieval</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("### 💡 Suggested Questions")
        
        suggestions = [
            "What is the main contribution?",
            "What datasets were used?",
            "What are the key limitations?",
            "How does this compare to baselines?",
            "What future work is proposed?",
        ]
        
        for i, suggestion in enumerate(suggestions):
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state["prefill_question"] = suggestion
                st.rerun()
    else:
        st.info("💡 **Getting Started**\n\n1. Enter API key (sidebar)\n2. Upload a PDF\n3. Ask questions!", icon="ℹ️")


# ── Right: Chat ────────────────────────────────────────────────────────────────
with col_chat:
    st.markdown("### 💬 Ask a Question")

    # Chat history display with sources
    if st.session_state.chat_history:
        st.markdown("#### Conversation History")
        
        for i, entry in enumerate(st.session_state.chat_history):
            st.markdown(f'<div class="chat-user">👤 <b>Q {i+1}:</b> {entry["question"]}</div>', unsafe_allow_html=True)
            
            # Answer
            st.markdown(f'<div class="answer-card"><b>🤖 Answer:</b><br/>{entry["answer"]}</div>', unsafe_allow_html=True)
            
            # Source details
            with st.expander(
                f"📚 **Sources** ({len(entry['sources'])} chunks) · "
                f"<span style='color:#94a3b8;font-weight:400;'>⏱️ {entry.get('time', '?')}s</span>",
                expanded=False
            ):
                for j, doc in enumerate(entry["sources"], 1):
                    page = doc.metadata.get("page", "Unknown")
                    preview = doc.page_content[:250]
                    
                    st.markdown(
                        f'<div class="source-card">'
                        f'<b>Source {j} · Page {page}</b><br/>'
                        f'{preview}{"..." if len(doc.page_content) > 250 else ""}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        
        st.divider()

    # Input section
    prefill = st.session_state.pop("prefill_question", "")
    question = st.text_input(
        "Ask anything about the paper:",
        value=prefill,
        placeholder="e.g., What methodology is used? How do results compare?",
        key="question_input",
        label_visibility="collapsed"
    )

    ask_btn = st.button(
        "🚀 Ask",
        disabled=(not st.session_state.chain),
        use_container_width=True,
        type="primary"
    )

    # Process query
    if ask_btn and question.strip():
        if not st.session_state.chain:
            st.error("⚠️ No PDF loaded. Please upload a paper first.")
        else:
            with st.spinner("🧠 **Retrieving context and generating answer...**"):
                try:
                    t0 = time.time()
                    answer, sources, meta = ask(
                        st.session_state.chain,
                        question.strip(),
                        use_cache=True,
                        use_query_expansion=False
                    )
                    elapsed = round(time.time() - t0, 2)

                    # Add to history
                    st.session_state.chat_history.append({
                        "question": question.strip(),
                        "answer": answer,
                        "sources": sources,
                        "time": elapsed,
                        "cache_hit": meta.get("cache_hit", False),
                    })
                    
                    st.session_state.query_count += 1
                    
                    # Visual feedback
                    if meta.get("cache_hit"):
                        st.toast("⚡ Answer from cache!", icon="⚡")
                    
                    st.rerun()

                except ValueError as e:
                    st.error(f"❌ **Question Error**\n\n{str(e)}")
                except Exception as e:
                    logger.exception("Error during query processing")
                    st.error(f"❌ **Error Processing Question**\n\nPlease try again or rephrase your question.\n\n*Details: {str(e)}*")

    elif not st.session_state.chain and ask_btn:
        st.warning("👆 Upload a PDF on the left to enable the Q&A interface.")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#64748b;font-size:0.85rem;padding:1rem;'>
Made with ❤️ using LangChain, ChromaDB, and Streamlit · 
<a href='https://github.com/' style='color:#a78bfa;text-decoration:none;'>View on GitHub</a>
</div>
""", unsafe_allow_html=True)
