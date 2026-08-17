import os
import sys
import json
import urllib.request
from pathlib import Path

# Memastikan Python bisa mengenali struktur folder kita
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mengimpor modul ekstraktor (DePlot) dan pembuat prompt kita
from src.extraction.deplot_extractor import extract_chart_to_dataframe
from src.generation.prompts import build_chart_analysis_prompt

MODEL_NAME = "gemma4:12b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def ask_gemma(prompt):
    """Fungsi untuk mengirim prompt ke Gemma via Ollama."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3} # Sedikit kreativitas untuk merangkai kalimat naratif
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '')
    except Exception as e:
        return f"Error Ollama: {e}"

if __name__ == "__main__":
    print("\n=== PENGUJIAN: ANALISIS POLA GRAFIK ===")
    
    # 1. Tentukan gambar yang ingin diuji (Pastikan gambar ini ada di folder 'data')
    nama_gambar = "gambar_uji2.png" 
    path_gambar = os.path.join(str(PROJECT_ROOT), "data", nama_gambar)
    
    if not os.path.exists(path_gambar):
        print(f"\n[Error] Gambar tidak ditemukan di: {path_gambar}")
        print("Silakan taruh gambar grafik di folder 'data' dengan nama tersebut.")
        sys.exit()
        
    # 2. Ekstrak Gambar menjadi Tabel (menggunakan DePlot)
    df_extracted = extract_chart_to_dataframe(path_gambar)
    
    if df_extracted is not None:
        # Ubah DataFrame menjadi teks Markdown yang rapi agar mudah dibaca oleh Gemma
        data_teks = df_extracted.to_markdown(index=False)
        
        # 3. Masukkan data tersebut ke dalam Prompts.py kita
        print(f"\n[Proses] Menganalisis pola dan menyusun deskripsi menggunakan {MODEL_NAME}...")
        prompt_final = build_chart_analysis_prompt(data_teks)
        
        # 4. Minta Gemma mendeskripsikan polanya
        hasil_analisis = ask_gemma(prompt_final)
        
        print("\n" + "="*50)
        print("📊 DESKRIPSI & ANALISIS GRAFIK")
        print("="*50)
        print(hasil_analisis)
        print("="*50 + "\n")