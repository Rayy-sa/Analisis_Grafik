import os
import psycopg2
from rank_bm25 import BM25Okapi
import numpy as np
from dotenv import load_dotenv

load_dotenv()

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("BAAI/bge-m3")
    return _model

def connect_db():
    """Membuat koneksi ke PostgreSQL (Docker)."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5433"),
        database=os.environ.get("DB_NAME", "financial_rag"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "postgres")
    )

def dense_vector_search(query_text, top_n=5):
    """Mencari dokumen berdasarkan kemiripan makna (Vector)."""
    query_embedding = get_embedding_model().encode(query_text).tolist()
    
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, source_file, chart_title, content 
        FROM financial_docs 
        ORDER BY embedding <=> %s::vector 
        LIMIT %s
    """, (query_embedding, top_n))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{"id": r[0], "source": r[1], "title": r[2], "content": r[3]} for r in results]

def sparse_keyword_search(query_text, top_n=5):
    """Mencari dokumen berdasarkan kecocokan kata kunci eksak (BM25)."""
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id, source_file, chart_title, content FROM financial_docs")
    all_docs = cur.fetchall()
    cur.close()
    conn.close()
    
    if not all_docs:
        return []
        
    corpus = [{"id": r[0], "source": r[1], "title": r[2], "content": r[3]} for r in all_docs]
    tokenized_corpus = [doc['content'].lower().split() for doc in corpus]
    
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query_text.lower().split()
    
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_n]
    
    results = [corpus[i] for i in top_indices if scores[i] > 0]
    return results

def reciprocal_rank_fusion(dense_results, sparse_results, k=60):
    """Menggabungkan hasil Dense dan Sparse menggunakan RRF."""
    rrf_scores = {}
    
    for rank, doc in enumerate(dense_results):
        doc_id = doc['id']
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = {'data': doc, 'score': 0.0}
        rrf_scores[doc_id]['score'] += 1.0 / (k + rank + 1)
        
    for rank, doc in enumerate(sparse_results):
        doc_id = doc['id']
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = {'data': doc, 'score': 0.0}
        rrf_scores[doc_id]['score'] += 1.0 / (k + rank + 1)
        
    sorted_fused = sorted(rrf_scores.values(), key=lambda x: x['score'], reverse=True)
    return [item['data'] for item in sorted_fused]

def execute_hybrid_search(query_text, top_n_final=3):
    """Orkestrasi utama: Panggil vektor, panggil keyword, lalu gabungkan."""
    dense_hits = dense_vector_search(query_text, top_n=5)
    sparse_hits = sparse_keyword_search(query_text, top_n=5)
    
    final_results = reciprocal_rank_fusion(dense_hits, sparse_hits)
    return final_results[:top_n_final]

if __name__ == "__main__":
    print("Mencoba Hybrid Search...")
    hasil = execute_hybrid_search("Berapa nilai pendapatan pada tahun 2022?")
    for doc in hasil:
        print(doc['content'])