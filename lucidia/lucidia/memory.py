import os
import uuid
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except Exception:
    chromadb = None
    SentenceTransformer = None

class Memory:
    def __init__(self, persist_dir='lucidia_memory'):
        self.persist_dir = persist_dir
        self.client = chromadb.Client() if chromadb else None
        self.embed = SentenceTransformer('all-mpnet-base-v2') if SentenceTransformer else None
        if self.client:
            self.col = self.client.get_or_create_collection('lucidia')
    def add(self, text, metadata=None):
        if not self.client or not self.embed:
            raise RuntimeError("Install chromadb and sentence-transformers to enable memory.")
        eid = str(uuid.uuid4())
        emb = self.embed.encode([text]).tolist()
        self.col.add(ids=[eid], documents=[text], metadatas=[metadata or {}], embeddings=emb)
    def query(self, query_text, n=5):
        if not self.client or not self.embed:
            return []
        emb = self.embed.encode([query_text]).tolist()
        res = self.col.query(query_embeddings=emb, n_results=n)
        return res
