import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import docx
import os

# 1. Konfigurasi
# Ganti ke "./model_ner_person" jika ingin menguji model khusus Nama
model_path = "./model_ner_person" 

def main():
    if not os.path.exists(model_path):
        print(f"Peringatan: Folder model '{model_path}' tidak ditemukan.")
        print("Mencoba menggunakan model lama './model_ner_indobert'...")
        path_to_use = "./model_ner_indobert"
    else:
        path_to_use = model_path

    if not os.path.exists(path_to_use):
        print(f"Error: Tidak ada model yang ditemukan di {path_to_use}")
        return

    print(f"Memuat model dari {path_to_use}...")
    tokenizer = AutoTokenizer.from_pretrained(path_to_use)
    model = AutoModelForTokenClassification.from_pretrained(path_to_use)
    
    nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

    test_folder = "./datasurat"
    # Ambil 3 file secara acak dari folder datasurat
    all_files = [f for f in os.listdir(test_folder) if f.endswith('.docx')]
    files_to_test = all_files[:3]

    print("\n" + "="*50)
    print("--- HASIL EKSTRAKSI NER ---")
    print("="*50)
    
    for file_name in files_to_test:
        file_path = os.path.join(test_folder, file_name)
        print(f"\n[ FILE: {file_name} ]")
        
        raw_text = read_docx_full(file_path)
        # Ambil 1000 karakter pertama (biasanya data penting ada di sini)
        text_to_test = raw_text[:1000] 
        
        final_ents = nlp_ner(text_to_test)
        if not final_ents:
            print("  - Tidak ada entitas yang terdeteksi.")
        else:
            for ent in final_ents:
                print(f"  - {ent['entity_group']:8}: {ent['word']} (Confidence: {ent['score']:.2%})")
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
