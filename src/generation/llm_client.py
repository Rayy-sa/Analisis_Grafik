import json
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "gemma4:12b" 

def create_strict_prompt(user_query, retrieved_contexts):
    """
    Menyusun prompt yang memaksa LLM untuk HANYA menggunakan konteks yang diberikan.
    """
    context_text = "\n\n".join([
        f"- [Sumber: {doc['source']}, Tabel: {doc['title']}]\n  Konteks: {doc['content']}"
        for doc in retrieved_contexts
    ])
    
    prompt = f"""
    Anda adalah asisten analis finansial yang ahli dan ketat.
    Tugas Anda adalah menjawab pertanyaan HANYA berdasarkan DATA yang diberikan di bawah ini.
    
    PERATURAN PENTING:
    1. JANGAN mengarang data, memprediksi, atau menggunakan informasi di luar konteks.
    2. Jika jawaban dari pertanyaan tidak ada di dalam data konteks, katakan dengan jelas: "Data tidak tersedia di grafik/tabel yang saya baca."
    3. Selalu sebutkan sumber laporan (nama file) yang Anda kutip.
    
    DATA KONTEKS:
    {context_text}
    
    PERTANYAAN PENGGUNA: 
    {user_query}
    
    JAWABAN ANDA:
    """
    return prompt

def generate_answer(prompt):
    """Mengirim prompt ke lokal LLM via Ollama API."""
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0 # Temperature 0 untuk meminimalisir halusinasi
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', 'Error: Tidak ada respon dari LLM')
    except Exception as e:
        return f"Error menghubungi Ollama: {e}. Pastikan Ollama menyala dan model '{MODEL_NAME}' sudah terinstal."


def generate_answer_stream(prompt):
    """Stream token dari Ollama (NDJSON)."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.0},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            chunk = json.loads(line)
            piece = chunk.get("response", "")
            if piece:
                yield piece
            if chunk.get("done"):
                break

# ==========================================
# TEST PIPELINE (END-TO-END)
# ==========================================
if __name__ == "__main__":
    print("\n--- Pipeline RAG Finansial V2.0 ---")
    
    # 1. Pertanyaan
    pertanyaan = "Berapa persen laba bersih pada tahun 2023 berdasarkan simulasi laporan?"
    print(f"\nUser: {pertanyaan}")
    
    # 2. Retrieval (Hybrid Search)
    print("\n[Proses] Menjalankan pencarian konteks (Vector + BM25)...")
    from src.retrieval.search import execute_hybrid_search

    konteks = execute_hybrid_search(pertanyaan, top_n_final=2)
    
    if not konteks:
         print("Sistem gagal menemukan dokumen yang relevan.")
    else:
        # 3. Penyusunan Prompt
        final_prompt = create_strict_prompt(pertanyaan, konteks)
        
        # 4. Generasi ke LLM
        print(f"[Proses] Menghubungi model {MODEL_NAME} via API lokal...")
        jawaban = generate_answer(final_prompt)
        
        print("\n=== JAWABAN LLM ===")
        print(jawaban)
        print("===================\n")