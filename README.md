# 📄 Research Paper Q&A – Production-Grade RAG System

> **Retrieval-Augmented Generation for Academic Papers**
> 
> Upload any research PDF and ask natural-language questions using advanced RAG techniques, powered by **Gemini 1.5 Flash**, **ChromaDB**, and **LangChain**.

---

## ✨ Key Features

### 🚀 Advanced RAG
- **Semantic Search**: Vector similarity matching with local embeddings
- **Semantic Caching**: Avoid redundant LLM calls for repeated queries
- **Source Attribution**: Precise citations with page numbers
- **Context Preservation**: Overlapping text chunks for continuity

### 🎯 Production Quality
- **Comprehensive Error Handling**: User-friendly error messages & logging
- **Performance Tracking**: Query latency and cache hit metrics
- **Input Validation**: Safe processing of malformed PDFs
- **Robust Retrieval**: 4 sources by default (configurable)

### 💅 Professional UI
- **Responsive Layout**: Two-column design (upload + chat)
- **Real-time Feedback**: Loading states, success/error messages
- **Chat History**: Full conversation context with metadata
- **Suggested Prompts**: Quick exploration templates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Frontend (app.py)                 │
│  - File upload & validation                                 │
│  - Chat interface with history                              │
│  - Real-time metrics & feedback                             │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│            RAG Pipeline (rag_pipeline.py)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. PDF Loading (PyMuPDF) & Validation               │  │
│  │ 2. Text Chunking (RecursiveCharacterTextSplitter)   │  │
│  │ 3. Embedding (all-MiniLM-L6-v2 - Local)             │  │
│  │ 4. Vector Storage (ChromaDB)                        │  │
│  │ 5. Retrieval & Re-ranking                           │  │
│  │ 6. LLM Generation (Gemini 1.5 Flash)                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                   External Services                          │
│  ├─ Google Generative AI (Gemini 1.5 Flash)                │
│  └─ HuggingFace Hub (for-on-demand model weights)           │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

| Stage | Component | Purpose |
|-------|-----------|---------|
| **Input** | PyMuPDF | Extract text from PDFs while preserving structure |
| **Chunking** | LangChain TextSplitter | Break documents into semantically coherent chunks |
| **Embedding** | all-MiniLM-L6-v2 | Convert text to 384-dim vectors (local, no API calls) |
| **Storage** | ChromaDB | In-memory vector database with fast similarity search |
| **Retrieval** | LangChain Retriever | Fetch top-k semantically similar chunks |
| **Generation** | Gemini 1.5 Flash | Generate contextual answers with citations |

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **LLM** | Gemini 1.5 Flash | Fast, free API, excellent context understanding |
| **Embeddings** | all-MiniLM-L6-v2 | Lightweight (~50MB), runs locally, 384-dim vectors |
| **Vector DB** | ChromaDB | Lightweight, in-memory, perfect for prototypes |
| **PDF Parsing** | PyMuPDF | Fast, accurate text extraction |
| **Orchestration** | LangChain | Simplified LLM + retriever pipelines |
| **UI** | Streamlit | Rapid prototyping, minimal DevOps overhead |

---

## 📋 Prerequisites

- **Python 3.10+**
- **Google API Key** (free tier: [aistudio.google.com](https://aistudio.google.com))
- **System**: Windows/Mac/Linux with 2GB+ RAM

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone <repo-url>
cd RA_LLM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY=your_key_here
```

Get a free API key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run the App

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 📖 Usage Guide

### Basic Workflow

1. **Enter API Key** → Configuration panel (sidebar)
2. **Upload PDF** → Left panel, drag or click
3. **Wait for Processing** → ~30 seconds for embedding
4. **Ask Questions** → Right panel, type naturally
5. **Review Sources** → Click "Sources" expander for citations

### Customization

**Sidebar Controls:**
- **Chunk Size**: 200-1000 tokens (higher = more context, slower processing)
- **Chunk Overlap**: 0-200 tokens (higher = smoother retrieval)
- **Retrieved Chunks (k)**: 1-10 (higher = more sources, slower LLM)

### Example Queries

```
"What is the main contribution of this paper?"
"How does this compare to previous methods?"
"What datasets are used for evaluation?"
"What are the key limitations?"
"Summarize the methodology in 3 bullet points"
```

---

## 🎓 How It Works

### Retrieval-Augmented Generation (RAG)

1. **User Question** → "What methodology is used?"
2. **Embedding** → Convert question to 384-dim vector
3. **Similarity Search** → Find 4 most similar document chunks
4. **Context** → Feed question + chunks to Gemini
5. **Generation** → LLM generates answer with citations
6. **Output** → User sees answer + source chunks

### Performance

- **First Query**: ~8-12 seconds (embedding + retrieval + LLM)
- **Cached Query**: <1 second (semantic cache hit)
- **Memory Usage**: ~500MB-1GB (chromadb + models)

---

## 📊 Features in Detail

### ✅ Production Features

| Feature | Implementation |
|---------|-----------------|
| **Error Handling** | Try-catch with user-friendly messages |
| **Logging** | Structured logs for debugging |
| **Input Validation** | PDF file checks, empty query handling |
| **Caching** | Semantic query cache (MD5-based) |
| **Metrics** | Query time, sources used, cache status |
| **Session State** | Persistent within user session |

### 🔐 Security

- **No Data Storage**: PDFs processed in-memory only
- **API Key Protection**: Stored only in `.env`, never logged
- **Local Embeddings**: No text sent to external embedding service

### 🚀 Scalability

Currently designed for:
- **Single 200-page PDF** per session
- **Multiple queries** per PDF
- **Streamlit single-user** environment

For **multi-user/large-scale** deployment, consider:
- FastAPI + async workers
- Persistent vector database (Pinecone, Weaviate)
- PDF indexing service

---

## 📁 Project Structure

```
RA_LLM/
├── app.py              # Streamlit UI (500+ lines, production-grade)
├── rag_pipeline.py     # Core RAG logic (300+ lines, with caching)
├── requirements.txt    # Pinned dependencies
├── .env                # API key (not committed)
└── README.md          # This file
```

### Key Functions

**`rag_pipeline.py`:**
- `build_rag_pipeline()` → Creates RAG chain from PDF
- `ask()` → Queries chain with caching
- `generate_query_variants()` → Experimental query expansion
- `rank_by_relevance()` → Re-ranks retrieved chunks
- `clear_cache()` → Clears semantic cache

**`app.py`:**
- PDF upload & validation
- Chat interface with history
- Session state management
- Error handling & user feedback

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Upload small PDF (5 pages) → Works
- [ ] Upload large PDF (100+ pages) → Works
- [ ] Ask same question twice → Cache hit shows
- [ ] Ask malformed question → Error handled gracefully
- [ ] Invalid API key → Clear error message
- [ ] Source citations → Page numbers correct

### Example Test PDF

Use any research paper:
- [arXiv.org](https://arxiv.org/) → Download PDF
- [Papers with Code](https://paperswithcode.com/) → Easy access

---

## 🚢 Deployment

### Local Deployment
```bash
streamlit run app.py --server.port 8501
```

### Docker
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### Cloud Platforms

**Streamlit Cloud** (Recommended for demos)
```bash
git push to GitHub
Deploy via streamlit.app
```

**Railway/Heroku**
- Add `Procfile`: `web: streamlit run app.py`
- Set `GOOGLE_API_KEY` as environment variable

**AWS/GCP/Azure**
- Container deployment (ECS/Cloud Run)
- Persistent vector database
- Multi-worker setup

---

## 🔮 Future Enhancements

### Short-term (MVP+)
- [ ] Multi-document comparison (compare papers)
- [ ] Query expansion using LLM
- [ ] Custom prompts for different use cases
- [ ] Export conversation to PDF

### Medium-term
- [ ] Persistent storage (database backend)
- [ ] Multi-user authentication
- [ ] Advanced analytics dashboard
- [ ] PDF annotation + highlights

### Long-term
- [ ] Multi-modal (table/chart extraction)
- [ ] Citation network visualization
- [ ] Collaborative annotation
- [ ] Integration with Zotero/Mendeley

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. **Better chunking strategies** (hierarchical, semantic)
2. **Re-ranking algorithms** (LLM-based, learned ranking)
3. **Multi-PDF support** (vector DB management)
4. **UI enhancements** (dark mode toggle, keyboard shortcuts)
5. **Deployment scripts** (Docker, AWS templates)

**To contribute:**
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License – Feel free to use this project for commercial/academic purposes.

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://python.langchain.com/) – RAG orchestration
- [Streamlit](https://streamlit.io/) – UI framework
- [Google Generative AI](https://ai.google.dev/) – LLM API
- [ChromaDB](https://www.trychroma.com/) – Vector database
- [Sentence Transformers](https://www.sbert.net/) – Embeddings

---

## 💡 Tips & Troubleshooting

### Issue: "API Key not found"
**Solution:** Ensure `.env` file exists with `GOOGLE_API_KEY=...`

### Issue: "PDF could not be parsed"
**Solution:** Try a different PDF. Some scanned PDFs (images) may fail.

### Issue: "Slow responses"
**Solution:** Reduce `Chunk Size` or `Retrieved Chunks (k)` in sidebar

### Issue: "Out of memory"
**Solution:** Reduce PDF file size or chunk size

---

## 📞 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check inline code comments
- **Examples**: See suggested questions in app

---

## 🎯 Roadmap

**Current Version:** v2.0 (Production-Ready)

- ✅ Core RAG pipeline
- ✅ Error handling & logging
- ✅ Caching & performance
- ✅ Professional UI
- ⏳ Multi-document support (v2.1)
- ⏳ Advanced retrieval (v2.2)

---

**Made with ❤️ for researchers and knowledge workers**

**Last Updated:** May 2026 | Python 3.10+ | Streamlit 1.31+

---

## ✅ Features

- 📤 **PDF Upload** — drag-and-drop any research paper
- 🧩 **Smart Chunking** — configurable chunk size & overlap
- 🔍 **Semantic Search** — top-k retrieval with cosine similarity
- 🤖 **Gemini-Powered Answers** — context-aware generation
- 📚 **Source Attribution** — see exactly which passages were used
- 💬 **Chat History** — multi-turn Q&A in one session
- ⚙️ **Sidebar Controls** — tune chunk size, overlap, and retrieval k

---

## 🛠️ Advanced Usage

You can also use the pipeline programmatically:

```python
from rag_pipeline import build_rag_pipeline, ask

chain, n_chunks = build_rag_pipeline("paper.pdf", chunk_size=500, chunk_overlap=50, top_k=4)
answer, sources = ask(chain, "What is the main contribution?")
print(answer)
```
