def build_chart_analysis_prompt(table_data):
    """
    Menghasilkan prompt yang meminta LLM untuk mendeskripsikan 
    pola, tren, dan wawasan (insight) dari data sebuah grafik.
    """
    prompt = f"""
    Anda adalah analis data finansial senior yang ahli membaca tren pasar.
    Di bawah ini adalah representasi tabel dari sebuah gambar grafik yang berhasil diekstrak.
    
    DATA GRAFIK:
    {table_data}
    
    TUGAS ANDA:
    1. Tangkap dan deskripsikan pola atau tren utama dari grafik tersebut (misal: tren naik/turun, perbandingan antar kategori, atau lonjakan tajam).
    2. Identifikasi titik tertinggi (puncak) dan titik terendah dari data jika ada.
    3. Berikan satu paragraf kesimpulan atau 'insight' singkat yang berguna bagi pengambil keputusan.
    
    PERATURAN:
    - JANGAN mengarang angka. Gunakan HANYA angka yang ada di "DATA GRAFIK".
    - Jelaskan seolah-olah Anda sedang mempresentasikan gambar grafik tersebut kepada direktur perusahaan.
    - Gunakan bahasa Indonesia yang profesional dan mudah dipahami.
    
    ANALISIS ANDA:
    """
    return prompt