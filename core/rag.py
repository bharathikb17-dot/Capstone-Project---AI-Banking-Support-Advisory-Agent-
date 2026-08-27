"""Retrieval-Augmented Generation utilities (idiomatic LangChain).

Loads the banking knowledge base from PDF documents, splits it with a LangChain
text splitter, embeds it, and indexes it in a FAISS vector store. Retrieval uses
cosine relevance so it degrades gracefully to "no relevant info" below a floor.
Works with both real embeddings and the offline `MockEmbeddings`.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import KB_DIR
from core.llm import get_embeddings


@dataclass
class Chunk:
    source: str
    text: str


def load_documents() -> List[Document]:
    """Load the PDF KB and split it into overlapping LangChain documents."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    docs: List[Document] = []
    for path in sorted(KB_DIR.glob("*.pdf")):
        text = "\n".join(page.page_content for page in PyPDFLoader(str(path)).load())
        for piece in splitter.split_text(text):
            docs.append(Document(page_content=piece, metadata={"source": path.name}))
    return docs


def list_chunks() -> List[Chunk]:
    """Backward-compatible view of the indexed chunks (for UI stats)."""
    return [Chunk(d.metadata.get("source", ""), d.page_content) for d in load_documents()]


@lru_cache(maxsize=1)
def get_vector_store() -> FAISS:
    return FAISS.from_documents(
        load_documents(),
        get_embeddings(),
        distance_strategy=DistanceStrategy.COSINE,
    )


def get_retriever(k: int = 3) -> VectorStoreRetriever:
    """Idiomatic LangChain retriever for use in LCEL chains."""
    return get_vector_store().as_retriever(search_kwargs={"k": k})


RELEVANCE_FLOOR = 0.05  # below this we treat retrieval as "no relevant info found"


def retrieve(query: str, k: int = 3) -> List[Tuple[Chunk, float]]:
    with warnings.catch_warnings():
        # Offline mock embeddings can yield cosine relevance outside [0,1]; harmless here.
        warnings.simplefilter("ignore", UserWarning)
        results = get_vector_store().similarity_search_with_relevance_scores(query, k=k)
    return [
        (Chunk(doc.metadata.get("source", ""), doc.page_content), score)
        for doc, score in results
        if score >= RELEVANCE_FLOOR
    ]


def format_context(results: List[Tuple[Chunk, float]]) -> str:
    if not results:
        return ""
    return "\n\n".join(f"[{c.source}] {c.text}" for c, _ in results)


def format_documents(docs: List[Document]) -> str:
    """Format retriever output for the LCEL RAG chain."""
    if not docs:
        return ""
    return "\n\n".join(f"[{d.metadata.get('source', '')}] {d.page_content}" for d in docs)
