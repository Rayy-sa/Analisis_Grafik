import os
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Mempersiapkan RAGAS Evaluator Lokal...")

# 1. Konfigurasi "LLM as a Judge" menggunakan Ollama lokal Anda
# Kita atur temperature=0 agar Juri sangat objektif dan tidak berkreasi
local_llm = ChatOllama(model="gemma4:12b", temperature=0)

# 2. Konfigurasi model Embedding yang sama dengan Indexer Anda
local_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

def run_evaluation():
    # 3. Siapkan "Golden Dataset" (Simulasi satu tanya-jawab dari sistem Anda)
    # RAGAS membutuhkan format spesifik: question, answer, contexts, dan ground_truth
    data = {
        "question": ["Berapa persen laba bersih pada tahun 2023 berdasarkan simulasi laporan?"],
        "answer": ["Berdasarkan Tren Pendapatan Tahunan (Sumber: Laporan_Q3_Simulasi.png), laba bersih pada tahun 2023 adalah 18.2%."],
        "contexts": [[
            "Berdasarkan Tren Pendapatan Tahunan (Sumber: Laporan_Q3_Simulasi.png): Untuk kategori Tahun yaitu '2023', nilai Pendapatan (Juta $) adalah 250.7, nilai Laba Bersih (%) adalah 18.2."
        ]],
        "ground_truth": ["18.2%"] # Jawaban absolut yang seharusnya
    }
    
    # Ubah ke format HuggingFace Dataset yang dibaca oleh RAGAS
    dataset = Dataset.from_dict(data)
    
    print("\nMenjalankan evaluasi metrik (ini mungkin memakan waktu beberapa menit karena model 30B sedang 'berpikir')...")
    
    # 4. Proses Evaluasi
    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=local_llm,
        embeddings=local_embeddings
    )
    
    print("\n=== HASIL EVALUASI RAGAS ===")
    
    # RAGAS mengembalikan objek result yang bisa diubah ke DataFrame Pandas
    df_result = result.to_pandas()
    
    # Menampilkan skor rata-rata
    print(f"Faithfulness (Bebas Halusinasi) : {result['faithfulness']:.4f}")
    print(f"Answer Relevancy (Ketepatan)    : {result['answer_relevancy']:.4f}")
    print(f"Context Precision               : {result['context_precision']:.4f}")
    print(f"Context Recall                  : {result['context_recall']:.4f}")
    
    print("\nDetail per baris data:")
    print(df_result[['question', 'faithfulness', 'answer_relevancy']].to_string())

if __name__ == "__main__":
    run_evaluation()