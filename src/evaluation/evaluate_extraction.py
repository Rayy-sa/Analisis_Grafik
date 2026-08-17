import pandas as pd
import numpy as np

def calculate_mape(y_true, y_pred):
    """
    Menghitung Mean Absolute Percentage Error (MAPE).
    Menambahkan epsilon kecil (1e-8) untuk mencegah error pembagian dengan nol.
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100

def run_evaluation():
    print("=== EVALUASI AKURASI EKSTRAKSI DEPLOT ===")
    
    # 1. GROUND TRUTH (Kunci Jawaban Mutlak dari Gambar)
    # Ini adalah data yang Anda ketik/masukkan secara manual sebagai standar kebenaran.
    data_ground_truth = {
        'Year': [2013, 2014, 2015, 2016],
        'Otomotif': [10.0, 9.0, 8.0, 9.0], 
        'Jasa Keuangan': [5.0, 5.0, 3.0, 5.0],
        'Alat Berat & Pertambangan': [5.0, 5.0, 3.0, 5.0], 
        'Segmen Lainnya': [3.0, 3.4, 1.5, 2.8] # Nilai asli untuk Segmen Lainnya
    }
    df_gt = pd.DataFrame(data_ground_truth).set_index('Year')
    
    # 2. HASIL EKSTRAKSI (Output dari DePlot)
    # Ini mensimulasikan hasil yang salah tangkap oleh model DePlot Anda sebelumnya.
    data_extracted = {
        'Year': [2013, 2014, 2015, 2016],
        'Otomotif': [10.00, 8.90, 8.30, 10.88],
        'Jasa Keuangan': [5.0, 5.0, 3.0, 1.6],
        'Alat Berat & Pertambangan': [8.01, 7.31, 6.18, 6.31],
        'Segmen Lainnya': [4.69, 5.01, 1.92, 2.23] # DePlot melenceng di sini
    }
    df_pred = pd.DataFrame(data_extracted).set_index('Year')
    
    # 3. PROSES PERHITUNGAN MAPE
    print("\nMenghitung tingkat error (MAPE) per kategori...")
    mape_results = {}
    
    for column in df_gt.columns:
        if column in df_pred.columns:
            # Ambil nilai per kolom
            actual_values = df_gt[column]
            predicted_values = df_pred[column]
            
            # Hitung MAPE
            error_rate = calculate_mape(actual_values, predicted_values)
            mape_results[column] = error_rate
            
            print(f"- {column}: {error_rate:.2f}% Error")
        else:
            print(f"- {column}: Kolom tidak ditemukan di hasil ekstraksi!")
            
    # 4. KESIMPULAN
    rata_rata_error = np.mean(list(mape_results.values()))
    print("-" * 40)
    print(f"RATA-RATA ERROR KESELURUHAN: {rata_rata_error:.2f}%")
    
    # Logika ambang batas toleransi (Threshold)
    threshold = 5.0 
    print(f"\n[Status Evaluasi - Threshold {threshold}%]")
    if rata_rata_error <= threshold:
        print("✅ Ekstraksi LULUS. Model sangat akurat membaca grafik.")
    else:
        print("❌ Ekstraksi GAGAL. Tingkat halusinasi visual / kesalahan baca terlalu tinggi.")
        print("Saran: Gunakan gambar dengan label data eksplisit atau tingkatkan kualitas pra-pemrosesan gambar (OpenCV).")

if __name__ == "__main__":
    run_evaluation()