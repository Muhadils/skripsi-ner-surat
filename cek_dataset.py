import json

def check_json_alignment(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Memeriksa {len(data)} sampel...")
    count_found = 0
    
    for i, sample in enumerate(data[:10]): # Cek 10 sampel pertama
        text = sample['text']
        entities = sample['entities']
        
        if not entities: continue
        
        print(f"\n[ Sampel {i} ]")
        for ent in entities:
            start = ent['start']
            end = ent['end']
            label = ent['label']
            
            # Ambil potongan teks berdasarkan offset
            snippet = text[start:end]
            print(f"  - Label: {label:10} | Offset: {start}:{end} | Teks Terambil: '{snippet}'")
            count_found += 1
            
    if count_found == 0:
        print("\nPERINGATAN: Tidak ada entitas yang ditemukan di 10 sampel pertama atau offset salah!")

if __name__ == "__main__":
    check_json_alignment('dataset_ner.json')
