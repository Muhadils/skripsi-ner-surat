import pandas as pd
import re

# Gunakan path relatif agar bisa jalan di laptop maupun Cloud (Colab/GitHub)
input_excel = 'dataset_surat.xlsx'
output_excel = 'dataset_surat_siap_anotasi.xlsx'

def clean_text(text):
    if pd.isna(text): return ""
    return str(text).replace('\n', ' ')

def extract_entities(text):
    text = clean_text(text)
    
    # 1. NIK (16 digit)
    niks = list(set(re.findall(r'\b\d{16}\b', text)))
    
    # 2. Nama (Huruf Kapital 2-4 kata, filter kata umum)
    forbidden_words = ["PROVINSI", "KECAMATAN", "KABUPATEN", "KELURAHAN", "INDONESIA", "SURAT", "KETERANGAN", "NIK", "NOMOR", "SAKSI", "LUAS", "UTARA", "TIMUR", "SELATAN", "BARAT", "DESA", "PEKERJAAN", "ALAMAT", "JABATAN"]
    nama_matches = re.findall(r'\b[A-Z][A-Z\s\.]{3,}\b', text)
    names = []
    for n in nama_matches:
        n = re.sub(r'\s+', ' ', n).strip()
        if not any(word in n.split() for word in forbidden_words) and 3 < len(n) < 50:
            names.append(n)
    names = list(set(names))

    # 3. Tanggal (Contoh: 26 Agustus 2025 atau 26-08-2025)
    tgl_pattern = r'\b\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b'
    tanggals = list(set(re.findall(tgl_pattern, text, re.IGNORECASE)))

    # 4. Pekerjaan (Kata kunci umum di surat desa)
    pekerjaan_list = ["Petani", "Wiraswasta", "PNS", "Pegawai Negeri Sipil", "IRT", "Ibu Rumah Tangga", "Buruh", "Pelajar", "Mahasiswa", "TNI", "POLRI", "Karyawan Swasta"]
    pekerjaans = []
    for p in pekerjaan_list:
        if re.search(rf'\b{p}\b', text, re.IGNORECASE):
            pekerjaans.append(p)
    
    # 5. Jabatan (Contoh: Lurah, Kepala Desa, Ketua RT)
    jabatan_list = ["Lurah", "Kepala Desa", "Ketua RT", "Ketua RW", "Sekretaris", "Kepala Dusun", "Camat"]
    jabatans = []
    for j in jabatan_list:
        if re.search(rf'\b{j}\b', text, re.IGNORECASE):
            jabatans.append(j)

    # 6. Alamat (Mencari pola setelah kata 'Alamat' atau 'bertempat tinggal di')
    alamat_match = re.search(r'(?:Alamat|tinggal di)\s*[:\s]+([^,.]+)', text, re.IGNORECASE)
    alamats = [alamat_match.group(1).strip()] if alamat_match else []

    # 7. Luas & Harga (Tetap dipertahankan sebagai 'informasi lain')
    luas = list(set(re.findall(r'(\d+[\d\.,]*)\s*(?:m2|meter|M2|METER)', text)))
    harga = list(set(re.findall(r'(?:Rp|RP|rp)\.?\s*([\d\.,]{5,20})', text)))

    return "|".join(niks), "|".join(names), "|".join(alamats), "|".join(pekerjaans), "|".join(tanggals), "|".join(jabatans), "|".join(luas), "|".join(harga)

def main():
    print("Membaca file Excel...")
    df = pd.read_excel(input_excel)
    
    print("Mengekstrak entitas sesuai ruang lingkup Skripsi...")
    
    results = [extract_entities(row['Isi Teks']) for _, row in df.iterrows()]
    
    # Pecah hasil ke kolom masing-masing
    df['ENT_NIK'], df['ENT_NAMA'], df['ENT_ALAMAT'], df['ENT_PEKERJAAN'], \
    df['ENT_TANGGAL'], df['ENT_JABATAN'], df['ENT_LUAS'], df['ENT_HARGA'] = zip(*results)

    # Simpan hasil
    df.to_excel(output_excel, index=False)
    print("-" * 30)
    print(f"Selesai! Dataset diperbarui sesuai Skripsi: {output_excel}")

    print("-" * 30)
    print(f"Selesai! File siap diperiksa: {output_excel}")
    print("Catatan: Hasil otomatis mungkin tidak 100% akurat. Mohon periksa dan lengkapi kolom yang kosong di Excel.")

if __name__ == "__main__":
    main()
