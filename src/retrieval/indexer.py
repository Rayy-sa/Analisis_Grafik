import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Memuat kredensial DB dari .env
load_dotenv()

# Inisialisasi Model Embedding lokal
print("Memuat model embedding")
model = SentenceTransformer('BAAI/bge-m3')
EMBEDDING_DIM = model.get_embedding_dimension()

def connect_db():
    """Membuat koneksi ke PostgreSQL."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5433"),
        database=os.environ.get("DB_NAME", "financial_rag"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "postgres")
    )

def setup_database():
    """Mengaktifkan pgvector dan membuat tabel jika belum ada."""
    conn = connect_db()
    cur = conn.cursor()
    # Aktifkan ekstensi vektor
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS financial_docs (
            id SERIAL PRIMARY KEY,
            source_file VARCHAR(255),
            chart_title VARCHAR(255),
            content TEXT,
            embedding vector({EMBEDDING_DIM})
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database RAG siap.")

def table_aware_chunking(df, source_file, chart_title="Diagram Finansial"):
    """
    Mengubah DataFrame menjadi list of strings.
    Setiap baris diubah menjadi kalimat deskriptif yang menyertakan header kolom.
    """
    chunks = []
    headers = df.columns.tolist()
    
    # Contoh kalimat: "Pada tabel [Judul], untuk [Header1] bernilai [Data1], [Header2] bernilai [Data2]."
    for index, row in df.iterrows():
        # Kolom pertama biasanya adalah kategori (Tahun, Nama Perusahaan, dll)
        main_entity = row[headers[0]] 
        
        chunk_text = f"Berdasarkan {chart_title} (Sumber: {source_file}): "
        chunk_text += f"Untuk kategori {headers[0]} yaitu '{main_entity}', "
        
        # Gabungkan data kolom lainnya
        details = []
        for col in headers[1:]:
            val = row[col]
            if pd.notna(val): # Abaikan data kosong (NaN)
                details.append(f"nilai {col} adalah {val}")
        
        chunk_text += ", ".join(details) + "."
        chunks.append(chunk_text)
        
    return chunks

def index_to_vector_db(df, source_file, chart_title="Diagram"):
    """Melakukan chunking, embedding, dan insert ke pgvector."""
    # 1. Chunking
    text_chunks = table_aware_chunking(df, source_file, chart_title)
    
    if not text_chunks:
        print(f"Tidak ada teks valid untuk di-index dari {source_file}")
        return
        
    # 2. Embedding (Mengubah teks menjadi vektor angka)
    print(f"Membuat vektor untuk {len(text_chunks)} baris dari {source_file}...")
    embeddings = model.encode(text_chunks).tolist()
    
    # 3. Simpan ke Database
    conn = connect_db()
    cur = conn.cursor()
    
    # Siapkan data untuk bulk insert
    insert_data = [
        (source_file, chart_title, text_chunk, embedding) 
        for text_chunk, embedding in zip(text_chunks, embeddings)
    ]
    
    query = """
        INSERT INTO financial_docs (source_file, chart_title, content, embedding)
        VALUES %s
    """
    
    execute_values(cur, query, insert_data)
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Berhasil menyimpan {len(text_chunks)} baris ke vector database.")

# ==========================================
# TEST SKRIP (Hanya berjalan jika dieksekusi langsung)
# ==========================================
if __name__ == "__main__":
    # 1. Siapkan DB
    # (Pastikan Anda sudah menginstal PostgreSQL dan ekstensi pgvector di PC Anda)
    try:
        setup_database()
        
        # 2. Simulasi Data Bersih (Dari hasil validator.py sebelumnya)
        data = {
            'Tahun': ['2021', '2022', '2023'],
            'Pendapatan (Juta $)': [150.5, 200.0, 250.7],
            'Laba Bersih (%)': [12.5, 14.0, 18.2]
        }
        df_clean = pd.DataFrame(data)
        
        # 3. Proses Indexing
        index_to_vector_db(df_clean, source_file="Laporan_Q3_Simulasi.png", chart_title="Tren Pendapatan Tahunan")
        
    except Exception as e:
        print(f"Terjadi kesalahan saat koneksi DB: {e}")
        print("Pastikan PostgreSQL berjalan, pgvector terinstal, dan kredensial di .env benar.")