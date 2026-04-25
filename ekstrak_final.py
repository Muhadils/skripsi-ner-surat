import os
import docx
import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Folder Model Terpisah (Sesuai Ruang Lingkup Skripsi)
MODELS = {
    "PERSON": "./model_ner_person",
    "NIK": "./model_ner_nik",
    "PROFIL": "./model_ner_profil",
    "LUAS_HARGA": "./model_ner_luas_harga"
}

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return clean_text(" ".join([p.text for p in doc.paragraphs if p.text.strip()]))
    except:
        return ""

def load_pipelines():
    pipes = {}
    for name, path in MODELS.items():
        if os.path.exists(path):
            print(f"Memuat model {name}...")
            tokenizer = AutoTokenizer.from_pretrained(path)
            model = AutoModelForTokenClassification.from_pretrained(path)
            pipes[name] = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
        else:
            print(f"Peringatan: Model {name} belum dilatih (Folder {path} tidak ditemukan).")
    return pipes

def extract_all(file_path, pipes):
    text = read_docx(file_path)
    # Fokus pada 1200 karakter pertama
    sample_text = text[:1200]
    
    results = {
        "NAMA": [], "NIK": [], "ALAMAT": [], "PEKERJAAN": [], 
        "JABATAN": [], "TANGGAL": [], "LUAS": [], "HARGA": []
    }
    
    if "PERSON" in pipes:
        for ent in pipes["PERSON"](sample_text):
            results["NAMA"].append(ent['word'])
            
    if "NIK" in pipes:
        for ent in pipes["NIK"](sample_text):
            results["NIK"].append(ent['word'])
            
    if "PROFIL" in pipes:
        for ent in pipes["PROFIL"](sample_text):
            label = ent['entity_group']
            if label == "ALAMAT": results["ALAMAT"].append(ent['word'])
            elif label == "KERJA": results["PEKERJAAN"].append(ent['word'])
            elif label == "TGL": results["TANGGAL"].append(ent['word'])
            elif label == "JABATAN": results["JABATAN"].append(ent['word'])

    if "LUAS_HARGA" in pipes:
        for ent in pipes["LUAS_HARGA"](sample_text):
            if ent['entity_group'] == 'LUAS':
                results["LUAS"].append(ent['word'])
            elif ent['entity_group'] == 'HARGA':
                results["HARGA"].append(ent['word'])
                
    # Unikkan hasil dan bersihkan
    for key in results:
        results[key] = list(set([r.strip() for r in results[key] if len(r.strip()) > 1]))
        
    return results

def main():
    print("="*60)
    print("   SISTEM EKSTRAKSI INFORMASI SURAT ADMINISTRASI DESA")
    print("        (IMPLEMENTASI INDOBERT - MODEL TERPISAH)")
    print("="*60)
    
    pipes = load_pipelines()
    if not pipes:
        print("\nError: Tidak ada model yang bisa dimuat.")
        print("Silakan jalankan skrip pelatihan (train_ner_...) terlebih dahulu.")
        return

    test_folder = "./datasurat"
    if not os.path.exists(test_folder):
        print(f"Error: Folder {test_folder} tidak ditemukan.")
        return

    files = [f for f in os.listdir(test_folder) if f.endswith('.docx')]
    if not files:
        print("Tidak ada file .docx di folder datasurat.")
        return

    # Cek 5 file contoh
    for f in files[:5]:
        path = os.path.join(test_folder, f)
        print(f"\n[ ANALISIS FILE: {f} ]")
        data = extract_all(path, pipes)
        
        print(f"  > Nama       : {', '.join(data['NAMA']) if data['NAMA'] else '-'}")
        print(f"  > NIK        : {', '.join(data['NIK']) if data['NIK'] else '-'}")
        print(f"  > Alamat     : {', '.join(data['ALAMAT']) if data['ALAMAT'] else '-'}")
        print(f"  > Pekerjaan  : {', '.join(data['PEKERJAAN']) if data['PEKERJAAN'] else '-'}")
        print(f"  > Jabatan    : {', '.join(data['JABATAN']) if data['JABATAN'] else '-'}")
        print(f"  > Tanggal    : {', '.join(data['TANGGAL']) if data['TANGGAL'] else '-'}")
        
        lh = data['LUAS'] + data['HARGA']
        print(f"  > Info Lain  : {', '.join(lh) if lh else '-'}")
        print("-" * 60)

if __name__ == "__main__":
    main()
