"""Re-embed all document chunks with bge-small-en-v1.5 (384-dim)."""
from app.database.session import get_session
from app.database.models.document_chunk import DocumentChunk
from app.retrieval.dense import embed_texts
from sqlalchemy import select

BATCH = 64

with get_session() as session:
    chunks = session.execute(select(DocumentChunk)).scalars().all()
    print(f"Re-embedding {len(chunks)} chunks...")
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i: i + BATCH]
        texts = [c.text for c in batch]
        embeddings = embed_texts(texts)
        for chunk, emb in zip(batch, embeddings):
            chunk.embedding = emb
        session.commit()
        print(f"  {min(i + BATCH, len(chunks))}/{len(chunks)}")

print("Done.")
