import os
from complete_pipeline import CompletePipeline

TEST_FOLDER = "./datasurat"
MAX_FILES = 3


def format_entities_for_display(entities):
    """Format entity dictionary to readable output."""
    ordered_keys = ["NAMA", "NIK", "ALAMAT", "PEKERJAAN", "JABATAN", "TGL", "LUAS", "HARGA"]
    lines = []
    for key in ordered_keys:
        values = entities.get(key, [])
        if values:
            lines.append(f"  - {key:10}: {', '.join(values[:5])}")
    if not lines:
        lines.append("  - Tidak ada entitas yang terdeteksi.")
    return lines

def main():
    if not os.path.exists(TEST_FOLDER):
        print(f"Error: Folder data tidak ditemukan: {TEST_FOLDER}")
        return

    print("Memuat pipeline NER lengkap...")
    ner_pipeline = CompletePipeline()

    all_files = sorted([f for f in os.listdir(TEST_FOLDER) if f.endswith(".docx")])
    files_to_test = all_files[:MAX_FILES]

    if not files_to_test:
        print("Error: Tidak ada file .docx untuk diuji.")
        return

    print("\n" + "="*50)
    print("--- HASIL EKSTRAKSI NER (MULTI-MODEL) ---")
    print("="*50)

    for file_name in files_to_test:
        file_path = os.path.join(TEST_FOLDER, file_name)
        print(f"\n[ FILE: {file_name} ]")

        result = ner_pipeline.process_document(file_path)
        if not result:
            print("  - Gagal memproses dokumen.")
            continue

        for line in format_entities_for_display(result.get("extracted_entities", {})):
            print(line)

    print("\n" + "="*50)


if __name__ == "__main__":
    main()
