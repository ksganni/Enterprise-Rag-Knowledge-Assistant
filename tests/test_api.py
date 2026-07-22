import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["CHROMA_PERSIST_DIR"] = "./data/test_chroma"
os.environ["UPLOAD_DIR"] = "./data/test_uploads"
os.environ["LLM_PROVIDER"] = "none"
os.environ["GEMINI_API_KEY"] = ""

from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path):
  chroma_dir = tmp_path / "chroma"
  upload_dir = tmp_path / "uploads"
  chroma_dir.mkdir()
  upload_dir.mkdir()

  os.environ["CHROMA_PERSIST_DIR"] = str(chroma_dir)
  os.environ["UPLOAD_DIR"] = str(upload_dir)

  from app import config

  config.settings.chroma_persist_dir = str(chroma_dir)
  config.settings.upload_dir = str(upload_dir)

  return TestClient(app)


def test_health(client):
  response = client.get("/health")
  assert response.status_code == 200
  body = response.json()
  assert body["status"] == "ok"
  assert body["documents_indexed"] == 0


def test_upload_txt_and_ask(client):
  sample = Path("data/sample_docs/healthcare_handbook.txt")
  with sample.open("rb") as f:
    upload = client.post(
      "/upload",
      files={"file": ("healthcare_handbook.txt", f, "text/plain")},
    )

  assert upload.status_code == 200
  assert upload.json()["chunks_added"] > 0

  ask = client.post(
    "/ask",
    json={
      "question": "What is the remote work policy for non-clinical staff?",
      "document": "healthcare_handbook.txt",
    },
  )
  assert ask.status_code == 200
  body = ask.json()
  assert "remote" in body["answer"].lower() or len(body["sources"]) > 0
  assert body["used_llm"] is False
  assert len(body["sources"]) > 0


def test_reject_bad_file_type(client):
  response = client.post(
    "/upload",
    files={"file": ("notes.exe", b"bad", "application/octet-stream")},
  )
  assert response.status_code == 400


def test_delete_document(client):
  sample = Path("data/sample_docs/healthcare_handbook.txt")
  with sample.open("rb") as f:
    upload = client.post(
      "/upload",
      files={"file": ("healthcare_handbook.txt", f, "text/plain")},
    )
  assert upload.status_code == 200
  assert upload.json()["chunks_added"] > 0

  deleted = client.delete("/documents/healthcare_handbook.txt")
  assert deleted.status_code == 200
  assert deleted.json()["filename"] == "healthcare_handbook.txt"
  assert deleted.json()["chunks_removed"] > 0

  docs = client.get("/documents")
  assert docs.status_code == 200
  assert docs.json() == []
