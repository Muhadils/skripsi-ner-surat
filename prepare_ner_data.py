import pandas as pd
import json
import re

def prepare_ner_dataset(excel_path, json_output):
    df = pd.read_excel(excel_path)
    training_data = []

    chunk_size = 1500 # Karakter, kira-kira 300-400 token
    overlap = 300

    for _, row in df.iterrows():
        full_text = str(row['Isi Teks'])
        
        # Cari semua entitas di seluruh teks dulu
        all_entities = []
        entity_cols = {
            'ENT_NAMA': 'PERSON',
            'ENT_NIK': 'NIK',
            'ENT_ALAMAT': 'ALAMAT',
            'ENT_PEKERJAAN': 'KERJA',
            'ENT_TANGGAL': 'TGL',
            'ENT_JABATAN': 'JABATAN',
            'ENT_LUAS': 'LUAS',
            'ENT_HARGA': 'HARGA'
        }

        for col, label in entity_cols.items():
            value_str = row[col]
            if pd.isna(value_str): continue
            
            # Pecah berdasarkan tanda pipa '|' yang dibuat oleh auto_annotate baru
            values = str(value_str).split("|")
            for value in values:
                value = value.strip()
                if value != "" and value.lower() != 'nan' and len(value) > 1:
                    for match in re.finditer(re.escape(value), full_text):
                        all_entities.append({
                            "start": match.start(),
                            "end": match.end(),
                            "label": label
                        })
        
        # FILTER: Hapus duplikat dan hindari tumpang tindih (pilih yang terpanjang)
        all_entities = sorted(all_entities, key=lambda x: (x['start'], -(x['end'] - x['start'])))
        final_entities = []
        last_end = -1
        for ent in all_entities:
            if ent['start'] >= last_end:
                final_entities.append(ent)
                last_end = ent['end']
        all_entities = final_entities
        if len(full_text) <= chunk_size:
            training_data.append({"text": full_text, "entities": all_entities})
        else:
            start_idx = 0
            while start_idx < len(full_text):
                end_idx = start_idx + chunk_size
                chunk_text = full_text[start_idx:end_idx]
                
                # Sesuaikan entitas untuk chunk ini
                chunk_entities = []
                for ent in all_entities:
                    if ent['start'] >= start_idx and ent['end'] <= end_idx:
                        chunk_entities.append({
                            "start": ent['start'] - start_idx,
                            "end": ent['end'] - start_idx,
                            "label": ent['label']
                        })
                
                # Hanya simpan chunk jika ada entitas atau secara acak (untuk negative samples)
                if chunk_entities or (len(chunk_text) > 100 and start_idx % 3000 == 0):
                    training_data.append({
                        "text": chunk_text,
                        "entities": chunk_entities
                    })
                
                start_idx += (chunk_size - overlap)

    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=4)
    
    print(f"Dataset NER berhasil dibuat: {json_output}")

if __name__ == "__main__":
    input_file = 'dataset_surat_siap_anotasi.xlsx'
    output_file = 'dataset_ner.json'
    prepare_ner_dataset(input_file, output_file)
