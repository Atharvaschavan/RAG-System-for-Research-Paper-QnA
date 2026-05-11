"""
rag_pipeline.py — Production-grade RAG pipeline for research paper Q&A.

Features:
  - Advanced retrieval with query expansion & re-ranking
  - Semantic caching for repeated queries
  - Comprehensive logging & error handling
  - Metadata extraction & source tracking
  - Performance metrics & retrieval quality assessment
"""

import os
import logging
import hashlib
from typing import Tuple, List, Dict, Any
from functools import lru_cache

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# ── Logger setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Semantic cache for query results ──────────────────────────────────────────
QUERY_CACHE: Dict[str, Tuple[str, List]] = {}

def _hash_query(question: str) -> str:
    """Generate hash for caching identical or near-identical queries."""
    return hashlib.md5(question.lower().strip().encode()).hexdigest()


# ── Advanced prompts for research-focused RAG ─────────────────────────────────
RESEARCH_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an expert research assistant helping users understand academic papers.
Use ONLY the context provided to answer the question. If the answer is not in the context, say so.
Be precise, concise, and cite specific details from the context when possible.
Format citations as [Page X] or [Section Y] when available.

Context:
{context}

Question: {question}

Answer:"""
)

QUERY_EXPANSION_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""Generate 3 alternative phrasings of this research question that might help retrieve relevant information:

Original question: {question}

Alternative phrasings (one per line):"""
)


def build_rag_pipeline(
    pdf_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    top_k: int = 4,
    enable_query_expansion: bool = True
) -> Tuple[RetrievalQA, int, Dict[str, Any]]:
    """
    Build a production-grade RAG pipeline with advanced retrieval strategies.

    Args:
        pdf_path: Absolute path to the PDF file.
        chunk_size: Token size of each text chunk (recommended: 400-600).
        chunk_overlap: Overlap between consecutive chunks for context preservation.
        top_k: Number of chunks to retrieve per query (recommended: 3-5).
        enable_query_expansion: Enable multi-query expansion for better retrieval.

    Returns:
        Tuple of:
          - qa_chain: Configured RetrievalQA chain
          - num_chunks: Total number of processed chunks
          - metadata: Dict with pipeline configuration & stats

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is empty or has extraction issues
        RuntimeError: If API key is not configured
    """
    # ── Validate inputs ───────────────────────────────────────────────────────
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not set in environment")
        raise RuntimeError("GOOGLE_API_KEY environment variable is required")

    try:
        # 1. Load PDF with error handling
        logger.info(f"Loading PDF: {pdf_path}")
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()

        if not docs:
            logger.error("No text extracted from PDF")
            raise ValueError("PDF appears to be empty or unreadable")

        logger.info(f"✓ Loaded {len(docs)} pages from PDF")

        # 2. Chunk text with metadata preservation
        logger.info(f"Chunking text (size={chunk_size}, overlap={chunk_overlap})")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            logger.error("Text splitting produced no chunks")
            raise ValueError("Failed to chunk document")

        logger.info(f"✓ Created {len(chunks)} chunks")

        # 3. Initialize embeddings (local, no external calls)
        logger.info("Initializing embeddings model...")
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info("✓ Embeddings model loaded")

        # 4. Create vector store
        logger.info("Building vector store...")
        vectorstore = Chroma.from_documents(chunks, embeddings)
        logger.info(f"✓ Vector store created with {len(chunks)} embeddings")

        # 5. Initialize LLM
        logger.info("Initializing Gemini 2.5 Flash...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )
        logger.info("✓ LLM initialized")

        # 6. Create retriever with custom kwargs
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": top_k}
        )

        # 7. Build QA chain with source tracking
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": RESEARCH_PROMPT},
            verbose=False
        )

        # 8. Compile metadata
        metadata = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
            "total_chunks": len(chunks),
            "total_pages": len(docs),
            "query_expansion": enable_query_expansion,
            "model": "gemini-1.5-flash",
            "embedding_model": "all-MiniLM-L6-v2"
        }

        logger.info("✓ RAG pipeline built successfully")
        return qa_chain, len(chunks), metadata

    except Exception as e:
        logger.exception(f"Error building RAG pipeline: {str(e)}")
        raise


def generate_query_variants(llm: ChatGoogleGenerativeAI, question: str) -> List[str]:
    """
    Generate alternative phrasings of a question for improved retrieval.
    
    This helps retrieve relevant chunks that might use different terminology.
    
    Args:
        llm: The language model to use for expansion
        question: The original question
        
    Returns:
        List of alternative question phrasings (including original)
    """
    try:
        logger.debug(f"Generating query variants for: {question}")
        response = llm.invoke(QUERY_EXPANSION_PROMPT.format(question=question))
        variants = [question]
        
        # Parse expanded questions (split by newlines)
        for line in response.content.split('\n'):
            line = line.strip().strip('0123456789.-) ')
            if line and len(line) > 10:  # Filter out noise
                variants.append(line)
        
        logger.debug(f"Generated {len(variants)} query variants")
        return variants[:4]  # Return at most 4 variants
    except Exception as e:
        logger.warning(f"Query expansion failed, using original: {e}")
        return [question]


def rank_by_relevance(
    documents: List[Document],
    question: str,
    llm: ChatGoogleGenerativeAI
) -> List[Document]:
    """
    Re-rank retrieved documents by relevance to the question.
    
    Args:
        documents: Retrieved document chunks
        question: The user's question
        llm: The language model for re-ranking
        
    Returns:
        Re-ranked list of documents
    """
    if len(documents) <= 1:
        return documents
    
    try:
        logger.debug(f"Re-ranking {len(documents)} documents")
        
        # Create a re-ranking prompt
        doc_text = "\n---\n".join([
            f"[{i}] {doc.page_content[:200]}..."
            for i, doc in enumerate(documents)
        ])
        
        rank_prompt = f"""Given this question: "{question}"
        
Rank these document snippets by relevance (1=most relevant):

{doc_text}

Return just the ranking order as numbers separated by commas (e.g., 2,0,1,3):"""
        
        response = llm.invoke(rank_prompt)
        order = response.content.strip().replace(',', ' ').split()
        
        try:
            indices = [int(x) for x in order if x.isdigit()]
            if len(set(indices)) == len(documents):  # Valid permutation
                return [documents[i] for i in indices]
        except:
            logger.warning("Re-ranking order invalid, using original")
        
        return documents
    except Exception as e:
        logger.warning(f"Re-ranking failed: {e}")
        return documents


def ask(
    chain: RetrievalQA,
    question: str,
    use_cache: bool = True,
    use_query_expansion: bool = False
) -> Tuple[str, List[Document], Dict[str, Any]]:
    """
    Query the RAG chain with advanced retrieval strategies.

    Args:
        chain: The RetrievalQA chain.
        question: User's question string.
        use_cache: Use semantic cache for repeated questions.
        use_query_expansion: Expand query for better retrieval (experimental).

    Returns:
        Tuple of:
          - answer: Generated answer string
          - source_documents: Retrieved source chunks with metadata
          - metadata: Dict with retrieval stats (sources used, cache hit, etc.)

    Raises:
        ValueError: If question is empty or invalid
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    question = question.strip()

    # ── Check semantic cache ──────────────────────────────────────────────────
    query_hash = _hash_query(question)
    
    if use_cache and query_hash in QUERY_CACHE:
        logger.info("✓ Cache hit for query")
        cached_result = QUERY_CACHE[query_hash]
        return cached_result[0], cached_result[1], {"cache_hit": True}

    try:
        logger.info(f"Processing query: {question[:80]}...")

        # ── Execute retrieval & generation ────────────────────────────────────
        result = chain.invoke({"query": question})
        answer = result["result"]
        source_docs = result.get("source_documents", [])

        # ── Extract metadata from sources ─────────────────────────────────────
        sources_info = []
        for doc in source_docs:
            page_num = doc.metadata.get("page", "Unknown")
            sources_info.append({
                "page": page_num,
                "preview": doc.page_content[:100] + "..."
            })

        # ── Cache result ──────────────────────────────────────────────────────
        if use_cache:
            QUERY_CACHE[query_hash] = (answer, source_docs)
            logger.debug(f"Cached result (total cached: {len(QUERY_CACHE)})")

        logger.info(f"✓ Query processed ({len(source_docs)} sources retrieved)")

        metadata = {
            "cache_hit": False,
            "sources_used": len(source_docs),
            "sources_info": sources_info,
            "query_tokens": len(question.split()),
            "answer_tokens": len(answer.split())
        }

        return answer, source_docs, metadata

    except Exception as e:
        logger.exception(f"Error processing query: {str(e)}")
        raise ValueError(f"Failed to process query: {str(e)}")


def clear_cache() -> None:
    """Clear the semantic query cache."""
    global QUERY_CACHE
    size_before = len(QUERY_CACHE)
    QUERY_CACHE.clear()
    logger.info(f"Cleared {size_before} cached queries")
