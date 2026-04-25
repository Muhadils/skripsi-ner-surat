import os
import pandas as pd
from docx import Document

# Konfigurasi Path
folder_path = r'c:\Users\Lenovo\Downloads\program_dilla\datasurat'
output_excel = r'c:\Users\Lenovo\Downloads\program_dilla\dataset_surat.xlsx'

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error membaca {file_path}: {e}")
        return ""

def main():
    data = []
    
    # Cek apakah folder ada
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} tidak ditemukan!")
        return

    print("Sedang memproses file surat...")
    
    # Loop semua file di folder datasurat
    for filename in os.listdir(folder_path):
        if filename.endswith('.docx'):
            file_path = os.path.join(folder_path, filename)
            
            # Ekstrak teks
            text_content = extract_text_from_docx(file_path)
            
            # Tebak Jenis Surat sederhana dari nama file
            jenis_surat = "Lainnya"
            fn_lower = filename.lower()
            if "ajb" in fn_lower: jenis_surat = "AJB"
            elif "hibah" in fn_lower: jenis_surat = "HIBAH"
            elif "jual beli" in fn_lower: jenis_surat = "JUAL BELI"
            elif "ahli waris" in fn_lower: jenis_surat = "AHLI WARIS"
            elif "keterangan" in fn_lower or "ket." in fn_lower: jenis_surat = "KETERANGAN"
            elif "pernyataan" in fn_lower: jenis_surat = "PERNYATAAN"
            elif "perjanjian" in fn_lower: jenis_surat = "PERJANJIAN"

            data.append({
                'Nama File': filename,
                'Jenis Surat': jenis_surat,
                'Isi Teks': text_content
            })
            print(f"Berhasil: {filename}")

    # Simpan ke Excel menggunakan Pandas
    df = pd.DataFrame(data)
    df.to_excel(output_excel, index=False)
    
    print("-" * 30)
    print(f"Selesai! {len(data)} surat telah disimpan ke: {output_excel}")

if __name__ == "__main__":
    main()
