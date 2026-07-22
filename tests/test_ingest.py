from pathlib import Path

from langchain_core.documents import Document

from app.rag.ingest import load_documents, split_documents


def test_load_and_split_sample_doc():
  path = Path("data/sample_docs/healthcare_handbook.txt")
  docs = load_documents(path)
  assert len(docs) >= 1
  assert "HIPAA" in docs[0].page_content

  chunks = split_documents(docs)
  assert len(chunks) > 1
  assert all(isinstance(c, Document) for c in chunks)
