import os
import zipfile
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

def download_kaggle_dataset():
    # Pastikan kredensial terbaca
    if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
        print("Error: Kredensial Kaggle tidak ditemukan di file .env")
        return

    # Import kaggle setelah environment variable diset
    import kaggle

    dataset_name = "varadsrivastava/financial-chart-ocr"
    download_path = "data/raw"

    print(f"Mulai mengunduh dataset: {dataset_name}...")
    
    # Mengunduh dan mengekstrak otomatis
    kaggle.api.dataset_download_files(
        dataset_name, 
        path=download_path, 
        unzip=True
    )
    
    print(f"Selesai! Dataset berhasil diunduh dan diekstrak ke folder: {download_path}")

if __name__ == "__main__":
    download_kaggle_dataset()