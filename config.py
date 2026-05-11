"""
config.py — Configuration management for Research Paper Q&A

Centralized configuration for pipeline parameters, model choices, and defaults.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

# ── Environment ───────────────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ── RAG Pipeline Configuration ────────────────────────────────────────────────
@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    
    # PDF Processing
    pdf_loader: str = "pymupdf"  # Options: pymupdf, pdfplumber
    
    # Text Chunking
    chunk_size: int = 500  # tokens
    chunk_overlap: int = 50  # tokens
    separators: list = None  # None = use defaults
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_device: str = "cpu"  # Options: cpu, cuda, mps
    
    # Vector Database
    vectorstore_type: str = "chromadb"  # Options: chromadb, pinecone
    persist_directory: str = None  # None = in-memory
    
    # Retrieval
    retriever_type: str = "similarity"  # Options: similarity, mmr, bm25
    top_k: int = 4  # Number of chunks to retrieve
    search_score_threshold: float = 0.0  # 0.0 = no filtering
    
    # LLM
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.2  # Lower = more deterministic
    llm_max_tokens: int = 1024
    llm_timeout: int = 60  # seconds
    
    # Caching
    enable_query_cache: bool = True
    cache_max_size: int = 1000  # queries
    cache_ttl: int = 3600  # seconds (1 hour)
    
    # Experimental
    enable_query_expansion: bool = False
    enable_reranking: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model,
            "retriever": f"{self.retriever_type} (k={self.top_k})",
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "caching_enabled": self.enable_query_cache,
            "query_expansion": self.enable_query_expansion,
            "reranking": self.enable_reranking,
        }


# ── Streamlit UI Configuration ────────────────────────────────────────────────
@dataclass
class UIConfig:
    """Configuration for Streamlit UI"""
    
    # Layout
    layout: str = "wide"
    
    # Sidebar
    sidebar_expanded: bool = True
    
    # Chat
    show_chat_history: bool = True
    max_history_display: int = 10
    
    # Suggestions
    suggested_questions: list = None
    
    # Display
    show_source_preview: bool = True
    source_preview_length: int = 250
    show_metrics: bool = True
    show_performance_badge: bool = True
    
    # Theme
    theme: str = "dark"  # Options: dark, light, auto
    primary_color: str = "#a78bfa"
    
    def __post_init__(self):
        if self.suggested_questions is None:
            self.suggested_questions = [
                "What is the main contribution?",
                "What datasets were used?",
                "What are the key limitations?",
                "How does this compare to baselines?",
                "What future work is proposed?",
            ]


# ── Default Configurations ────────────────────────────────────────────────────
DEFAULT_RAG_CONFIG = RAGConfig()
DEFAULT_UI_CONFIG = UIConfig()


# ── Environment-specific Overrides ────────────────────────────────────────────
def load_config_from_env() -> RAGConfig:
    """Load RAG configuration from environment variables"""
    config = RAGConfig()
    
    # Override from env if set
    config.chunk_size = int(os.getenv("CHUNK_SIZE", config.chunk_size))
    config.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", config.chunk_overlap))
    config.top_k = int(os.getenv("TOP_K", config.top_k))
    config.llm_temperature = float(os.getenv("LLM_TEMPERATURE", config.llm_temperature))
    config.enable_query_cache = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    config.enable_query_expansion = os.getenv("ENABLE_QUERY_EXPANSION", "false").lower() == "true"
    
    return config


if __name__ == "__main__":
    # Print current configuration
    config = load_config_from_env()
    print("RAG Configuration:")
    for k, v in config.to_dict().items():
        print(f"  {k}: {v}")
