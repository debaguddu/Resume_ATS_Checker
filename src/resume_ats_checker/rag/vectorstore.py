"""RAG vector processing and semantic similarity retrieval pipeline."""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)


def get_embeddings_model() -> OpenAIEmbeddings:
    """Instantiate OpenAIEmbeddings model from settings."""
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    """Split text into semantically coherent chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "•", "-", ". ", " "],
    )
    return splitter.create_documents([text])


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def perform_rag_analysis(
    resume_text: str,
    job_description: str,
    top_k: int = 4
) -> Tuple[List[Dict[str, Any]], float, List[Dict[str, Any]]]:
    """Perform RAG retrieval: match JD requirement chunks against candidate resume chunks.
    
    Returns:
        matches: List of requirement chunks with best matching resume evidence and similarity score.
        average_semantic_score: Mean similarity percentage (0 - 100).
        embedded_chunks: All document chunks with their 1536-dimensional float vector embeddings.
    """
    embeddings_model = get_embeddings_model()

    # 1. Chunk both documents
    resume_docs = chunk_text(resume_text, chunk_size=400, chunk_overlap=50)
    jd_docs = chunk_text(job_description, chunk_size=350, chunk_overlap=40)

    if not resume_docs or not jd_docs:
        return [], 0.0, []

    # 2. Generate embeddings
    resume_texts = [d.page_content for d in resume_docs]
    jd_texts = [d.page_content for d in jd_docs]

    resume_vectors = embeddings_model.embed_documents(resume_texts)
    jd_vectors = embeddings_model.embed_documents(jd_texts)

    # 3. Match each JD requirement chunk to the most relevant resume sections
    matches = []
    scores = []

    for i, jd_vec in enumerate(jd_vectors):
        jd_chunk = jd_texts[i]
        sims = [cosine_similarity(jd_vec, r_vec) for r_vec in resume_vectors]
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        scores.append(best_sim)

        matches.append({
            "requirement_chunk": jd_chunk,
            "best_resume_evidence": resume_texts[best_idx],
            "similarity_score": round(best_sim * 100, 1),
            "status": "Strong Match" if best_sim >= 0.72 else ("Partial Match" if best_sim >= 0.55 else "Missing/Gap"),
        })

    # 4. Prepare embedded chunks for database persistence and vector inspection
    embedded_chunks = []
    for idx, (text_chunk, vec) in enumerate(zip(resume_texts, resume_vectors)):
        embedded_chunks.append({
            "chunk_type": "resume",
            "chunk_index": idx,
            "content": text_chunk,
            "embedding": vec,
        })
    for idx, (text_chunk, vec) in enumerate(zip(jd_texts, jd_vectors)):
        embedded_chunks.append({
            "chunk_type": "job_description",
            "chunk_index": idx,
            "content": text_chunk,
            "embedding": vec,
        })

    avg_score = float(np.mean(scores)) * 100 if scores else 0.0
    return matches, round(avg_score, 1), embedded_chunks

