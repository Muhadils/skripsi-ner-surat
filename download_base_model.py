from transformers import AutoTokenizer, AutoModelForTokenClassification
import os

model_name = "indobenchmark/indobert-lite-base-p2"
save_path = "./indobert-base-local"

def download():
    print(f"Mencoba mengunduh model {model_name}...")
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=9)
        
        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)
        print(f"BERHASIL! Model disimpan di {save_path}")
    except Exception as e:
        print(f"Gagal mengunduh: {e}")
        print("Saran: Tunggu 5-10 menit lalu coba lagi, atau gunakan koneksi internet lain.")

if __name__ == "__main__":
    download()
