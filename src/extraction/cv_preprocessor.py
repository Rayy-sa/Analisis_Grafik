import cv2
import numpy as np
import os

def clean_chart_keep_all_colors(image_path, output_path):
    """
    Menggunakan OpenCV untuk mendeteksi SEMUA warna garis pada grafik
    tanpa perlu mendefinisikan warna spesifik (merah/biru/dll).
    """
    print(f"[OpenCV] Memproses semua warna pada gambar: {image_path}")
    
    # 1. Baca gambar
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Gambar tidak ditemukan. Pastikan path gambar benar.")
        
    # 2. Konversi ke ruang warna HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 3. DETEKSI SEMUA WARNA (Universal Color Detector)
    # Filter berdasarkan Saturasi (S). 
    # Angka 40 membuang warna putih/abu-abu (latar & grid).
    # Value (V) di atas 50 membuang bayangan gelap.
    lower_color = np.array([0, 40, 50])
    upper_color = np.array([180, 255, 255])
    mask_colors = cv2.inRange(hsv, lower_color, upper_color)
    
    # 4. DETEKSI TEKS HITAM (Sumbu X, Y, dan Judul)
    # Teks hitam tidak punya warna (Saturasi rendah) tapi sangat gelap (Value rendah)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 100]) # V di bawah 100
    mask_black = cv2.inRange(hsv, lower_black, upper_black)
    
    # 5. Gabungkan kedua detektor
    # (Ambil semua yang berwarna ATAU semua teks hitam)
    combined_mask = cv2.bitwise_or(mask_colors, mask_black)
    
    # 6. Tebalkan sedikit agar DePlot lebih mudah membaca
    kernel = np.ones((2,2), np.uint8)
    thick_mask = cv2.dilate(combined_mask, kernel, iterations=1)
    
    # 7. Buat kanvas putih bersih
    white_bg = np.ones_like(image) * 255
    
    # 8. Terapkan mask ke gambar asli
    # Jika piksel terdeteksi (255), ambil warna aslinya. Jika tidak, jadikan putih.
    final_result = np.where(thick_mask[:, :, None] == 255, image, white_bg)
    
    # Simpan hasil
    cv2.imwrite(output_path, final_result)
    print(f"[OpenCV] Gambar bersih universal berhasil disimpan di: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Ganti input dengan gambar spaghetti chart Anda
    input_img = r"D:/latihan/analisis grafik/data/gambar_uji2.png"
    output_img = r"D:/latihan/analisis grafik/data/processed_all_colors.jpg"
    
    clean_chart_keep_all_colors(input_img, output_img)