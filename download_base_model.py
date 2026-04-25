from transformers import AutoTokenizer, AutoModel
import os
import shutil

model_name = "indobenchmark/indobert-lite-base-p2"
save_path = "./indobert-base-local"

def fix_and_download():
    print(f"--- MEMPERBAIKI & MENDOWNLOAD MODEL {model_name} ---")
    
    # Hapus folder lama yang mungkin rusak agar bersih
    if os.path.exists(save_path):
        print("Membersihkan folder lama...")
        shutil.rmtree(save_path)
    
    os.makedirs(save_path, exist_ok=True)
    
    try:
        print("Sedang mengambil model dari server (Sabar, ini mendownload data besar)...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        # Simpan backbone saja supaya checkpoint lokal tetap netral terhadap jumlah label task.
        model = AutoModel.from_pretrained(model_name)
        
        print("Menyimpan model ke folder lokal...")
        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)
        
        # Tambahan: Pastikan file tokenizer tidak kosong
        if os.path.exists(os.path.join(save_path, "tokenizer_config.json")):
            print("\nBERHASIL! Model sudah lengkap di folder lokal.")
            print("Sekarang Anda bisa menjalankan: python train_ner_person.py")
        else:
            print("\nPERINGATAN: Download selesai tapi ada file yang kurang. Coba jalankan lagi skrip ini.")
            
    except Exception as e:
        print(f"\nGAGAL: {e}")
        print("\nSaran: Kemungkinan internet Anda membatasi akses (Error 429).")
        print("Tunggu 5-10 menit, lalu jalankan lagi skrip ini.")

if __name__ == "__main__":
    fix_and_download()
