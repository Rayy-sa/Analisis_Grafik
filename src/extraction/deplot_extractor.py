import os
import pandas as pd
from PIL import Image
from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
from io import StringIO

print("Mempersiapkan mata AI: Memuat model Google DePlot")
# Mengunduh/memuat model vision ke dalam memori komputer
processor = Pix2StructProcessor.from_pretrained('google/deplot')
model = Pix2StructForConditionalGeneration.from_pretrained('google/deplot')

def extract_chart_to_dataframe(image_path):
    """Mengekstrak gambar grafik menjadi Pandas DataFrame menggunakan DePlot."""
    print(f"\n[1/3] Membaca gambar dari: {image_path}")
    image = Image.open(image_path)
    
    # Memberikan instruksi ke DePlot untuk menghasilkan tabel
    inputs = processor(images=image, text="Generate underlying data table of the figure :", return_tensors="pt")
    predictions = model.generate(**inputs, max_new_tokens=512)
    
    # Menerjemahkan output AI kembali menjadi teks
    text_output = processor.decode(predictions[0], skip_special_tokens=True)
    
    print("\n[2/3] Hasil ekstraksi mentah (raw teks) dari DePlot:")
    print(text_output)
    
    # DePlot memisahkan baris dengan tag <0x0A>, kita ubah menjadi baris baru (enter)
    text_clean = text_output.replace("<0x0A>", "\n")
    
    try:
        # Mengonversi teks menjadi tabel DataFrame yang rapi
        df = pd.read_csv(StringIO(text_clean), sep=r"\s*\|\s*", engine="python")
        df.columns = df.columns.str.strip()
        print("\n[3/3] Berhasil distrukturkan ke bentuk Tabel Pandas:")
        print(df.head())
        return df
    except Exception as e:
        print(f"Gagal memparsing tabel: {e}")
        return None