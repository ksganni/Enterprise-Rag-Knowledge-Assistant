from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import settings

COLLECTION_NAME = "document_knowledge_base"


class FastEmbedEmbeddings(Embeddings):
  def __init__(self, model_name: str):
    from fastembed import TextEmbedding

    self._model = TextEmbedding(model_name=model_name)

  def embed_documents(self, texts: list[str]) -> list[list[float]]:
    return [vec.tolist() for vec in self._model.embed(texts)]

  def embed_query(self, text: str) -> list[float]:
    return next(self._model.embed([text])).tolist()


@lru_cache(maxsize=1)
def get_embeddings() -> FastEmbedEmbeddings:
  return FastEmbedEmbeddings(model_name=settings.embedding_model)


def get_vectorstore() -> Chroma:
  return Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=get_embeddings(),
    persist_directory=settings.chroma_persist_dir,
  )


def add_documents(chunks: list[Document]) -> int:
  if not chunks:
    return 0
  store = get_vectorstore()
  store.add_documents(chunks)
  return len(chunks)


def search_documents(
  query: str,
  k: int | None = None,
  source: str | None = None,
) -> list[Document]:
  store = get_vectorstore()
  filter_by = {"source": source} if source else None
  return store.similarity_search(
    query,
    k=k or settings.top_k,
    filter=filter_by,
  )


def _chroma_collection():
  import chromadb

  client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
  return client.get_or_create_collection(name=COLLECTION_NAME)


def count_indexed_chunks() -> int:
  try:
    return _chroma_collection().count()
  except Exception:
    return 0


def delete_document(source: str) -> int:
  """Delete chunks belonging to one source file."""
  try:
    collection = _chroma_collection()
    data = collection.get(where={"source": source})
    ids = data.get("ids") or []
    if ids:
      collection.delete(ids=ids)
    return len(ids)
  except Exception:
    return 0


def list_documents() -> dict[str, int]:
  try:
    data = _chroma_collection().get(include=["metadatas"])
  except Exception:
    return {}

  counts: dict[str, int] = {}
  for meta in data.get("metadatas") or []:
    if not meta:
      continue
    name = meta.get("source", "unknown")
    counts[name] = counts.get(name, 0) + 1
  return counts
