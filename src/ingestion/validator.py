import pandas as pd
import io

def parse_deplot_output(raw_text):
    """Mengubah teks mentah DePlot menjadi Pandas DataFrame."""
    clean_text = raw_text.replace("<0x0A>", "\n").replace(" | ", ",")
    try:
        df = pd.read_csv(io.StringIO(clean_text), skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
        return df
    except Exception as e:
        print(f"Error parsing: {e}")
        return None

def validate_financial_table(df):
    """Memvalidasi dan membersihkan tabel dari halusinasi OCR."""
    if df is None or df.empty:
        return False, "Tabel kosong", df
    
    if len(df.columns) < 2:
        return False, "Kolom kurang dari 2", df
    
    numeric_columns = 0
    for col in df.columns[1:]:
        df_temp = df[col].astype(str).str.replace(r'[$,%]', '', regex=True)
        converted = pd.to_numeric(df_temp, errors='coerce')
        if converted.notna().sum() > 0:
            df[col] = converted
            numeric_columns += 1
            
    if numeric_columns == 0:
        return False, "Tidak ada data angka numerik", df
    
    for col in df.columns:
        if any(word in col.lower() for word in ['%', 'percent', 'persen']):
            if df[col].sum() > 105:
                return False, f"Total {col} melebihi 100% ({df[col].sum()}%)", df

    return True, "Data valid", df


# Blok ini hanya berjalan jika file dieksekusi langsung (python src/ingestion/validator.py)
# Jika file ini di-import dari indexer.py, blok ini akan diabaikan.
if __name__ == "__main__":
    print("Vakidasi Tabel Finansial dari Output DePlot")
    
    sample_text = "Tahun | Pendapatan (Juta $) <0x0A> 2021 | 150.5 <0x0A> 2022 | 200.0"
    df = parse_deplot_output(sample_text)
    
    is_valid, reason, df_clean = validate_financial_table(df)
    
    print(f"\nStatus: {is_valid} ({reason})")
    print("Tabel Bersih:")
    print(df_clean.to_string()) # Menggunakan to_string() agar rapi seperti display() di terminal