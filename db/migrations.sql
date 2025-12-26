CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  source TEXT,
  chunk TEXT,
  embedding VECTOR(3072)
);

CREATE INDEX IF NOT EXISTS idx_documents_embedding 
ON documents USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);


