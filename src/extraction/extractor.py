import cv2
import numpy as np
import pandas as pd
from PIL import Image
from io import StringIO

_processor = None
_model = None


def get_deplot():
    """Muat DePlot sekali, saat pertama kali dipakai — bukan saat import."""
    global _processor, _model
    if _processor is None or _model is None:
        from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration

        print("Mempersiapkan Sistem: Memuat model Google DePlot")
        _processor = Pix2StructProcessor.from_pretrained("google/deplot")
        _model = Pix2StructForConditionalGeneration.from_pretrained("google/deplot")
    return _processor, _model

def clean_image_with_opencv(image_path):
    """OpenCV membersihkan noise pada gambar."""
    print(f"\n[1/3] OpenCV sedang membersihkan gambar: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Gambar tidak ditemukan.")
        
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Deteksi warna (Saturasi) dan teks hitam
    mask_colors = cv2.inRange(hsv, np.array([0, 40, 50]), np.array([180, 255, 255]))
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 100]))
    combined_mask = cv2.bitwise_or(mask_colors, mask_black)
    
    # Penebalan garis
    kernel = np.ones((2,2), np.uint8)
    thick_mask = cv2.dilate(combined_mask, kernel, iterations=1)
    
    # Terapkan mask ke kanvas putih
    white_bg = np.ones_like(image) * 255
    cleaned_cv_image = np.where(thick_mask[:, :, None] == 255, image, white_bg)
    
    return cleaned_cv_image

def extract_with_deplot(cv_image_array):
    """DePlot membaca gambar yang sudah bersih dari OpenCV."""
    print("[2/3] DePlot mengekstrak tabel dari gambar bersih...")
    
    # Konversi matriks OpenCV (BGR) menjadi PIL Image (RGB) agar bisa dibaca DePlot
    # Ini membuat proses berjalan sangat cepat di dalam RAM tanpa perlu save ke hardisk
    rgb_image = cv2.cvtColor(cv_image_array, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    
    processor, model = get_deplot()
    inputs = processor(
        images=pil_image,
        text="Generate underlying data table of the figure :",
        return_tensors="pt",
    )
    predictions = model.generate(**inputs, max_new_tokens=512)
    text_output = processor.decode(predictions[0], skip_special_tokens=True)
    text_clean = text_output.replace("<0x0A>", "\n")
    
    try:
        df = pd.read_csv(StringIO(text_clean), sep=r"\s*\|\s*", engine="python")
        df.columns = df.columns.str.strip()
        print("[3/3] Sukses! Data berhasil diekstrak:")
        print(df.head())
        return df
    except Exception as e:
        print(f"Gagal memparsing tabel: {e}")
        return None

def process_chart_pipeline(image_path):
    """Fungsi Utama menggabungkan seluruh proses secara otomatis."""
    # 1. Bersihkan dengan OpenCV
    cleaned_image = clean_image_with_opencv(image_path)
    
    # 2. Ekstrak dengan DePlot
    df_result = extract_with_deplot(cleaned_image)
    
    return df_result

if __name__ == "__main__":
    # Cara pakainya sekarang sangat sederhana!
    # Cukup berikan gambar aslinya, biarkan OpenCV dan DePlot bekerja sama di belakang layar.
    gambar_asli = r"D:/latihan/analisis grafik\data/gambar_uji2.png"
    
    df_final = process_chart_pipeline(gambar_asli)
    
    print("\n=== HASIL AKHIR PIPELINE ===")
    print(df_final)