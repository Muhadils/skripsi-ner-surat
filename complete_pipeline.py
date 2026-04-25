#!/usr/bin/env python3
"""
COMPLETE PIPELINE - Extract entities + Generate text otomatis
Menggabungkan NER dan Text Generation dalam satu sistem
"""

import os
import sys
from pathlib import Path
import torch
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from docx import Document
import re

class CompletePipeline:
    """
    End-to-end pipeline: Document Input → NER Extraction → Text Generation → Output
    """
    def __init__(self):
        self.ner_models = {}
        self.load_models()

    def load_models(self):
        """Load all trained NER models"""
        print("\n📦 Loading NER models...")

        models = {
            "PERSON": "./model_ner_person",
            "NIK": "./model_ner_nik",
            "PROFIL": "./model_ner_profil",
            "LUAS_HARGA": "./model_ner_luas_harga"
        }

        for name, path in models.items():
            if os.path.exists(path):
                try:
                    tokenizer = AutoTokenizer.from_pretrained(path)
                    model = AutoModelForTokenClassification.from_pretrained(path)
                    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
                    self.ner_models[name] = ner_pipeline
                    print(f"  ✓ Loaded {name} model")
                except Exception as e:
                    print(f"  ⚠️  Warning: Could not load {name} model: {e}")
            else:
                print(f"  ⚠️  {name} model not found at {path}")

        if not self.ner_models:
            print("  ⚠️  No trained models found. Please run train_all_models.py first")

    def read_docx_document(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])
            return re.sub(r'\s+', ' ', text).strip()
        except Exception as e:
            print(f"Error reading document: {e}")
            return ""

    def extract_entities(self, text, sample_length=1200):
        """Extract entities using trained NER models"""
        # Only process first N characters for efficiency
        text_sample = text[:sample_length]

        entities = {
            "NAMA": [],
            "NIK": [],
            "ALAMAT": [],
            "PEKERJAAN": [],
            "JABATAN": [],
            "TGL": [],
            "LUAS": [],
            "HARGA": []
        }

        # Run PERSON model
        if "PERSON" in self.ner_models:
            for ent in self.ner_models["PERSON"](text_sample):
                if ent['entity_group'] == 'PERSON':
                    entities["NAMA"].append(ent['word'].strip())

        # Run NIK model
        if "NIK" in self.ner_models:
            for ent in self.ner_models["NIK"](text_sample):
                if ent['entity_group'] == 'NIK':
                    entities["NIK"].append(ent['word'].strip())

        # Run PROFIL model
        if "PROFIL" in self.ner_models:
            for ent in self.ner_models["PROFIL"](text_sample):
                label = ent['entity_group']
                if label == "ALAMAT":
                    entities["ALAMAT"].append(ent['word'].strip())
                elif label == "KERJA":
                    entities["PEKERJAAN"].append(ent['word'].strip())
                elif label == "TGL":
                    entities["TGL"].append(ent['word'].strip())
                elif label == "JABATAN":
                    entities["JABATAN"].append(ent['word'].strip())

        # Run LUAS_HARGA model
        if "LUAS_HARGA" in self.ner_models:
            for ent in self.ner_models["LUAS_HARGA"](text_sample):
                label = ent['entity_group']
                if label == 'LUAS':
                    entities["LUAS"].append(ent['word'].strip())
                elif label == 'HARGA':
                    entities["HARGA"].append(ent['word'].strip())

        # Fallback heuristics when models are missing or partial
        fallback_entities = self.rule_based_extract_entities(text)
        for key, values in fallback_entities.items():
            entities[key] = self._merge_unique(entities[key], values)

        # Clean duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _merge_unique(self, existing_values, fallback_values):
        """Merge two lists while keeping original order and removing duplicates."""
        merged = []
        seen = set()
        for value in existing_values + fallback_values:
            normalized = value.strip()
            if normalized and normalized not in seen:
                merged.append(normalized)
                seen.add(normalized)
        return merged

    def rule_based_extract_entities(self, text):
        """Deterministic fallback extraction based on common surat patterns."""
        fallback = {
            "NAMA": [],
            "NIK": [],
            "ALAMAT": [],
            "PEKERJAAN": [],
            "JABATAN": [],
            "TGL": [],
            "LUAS": [],
            "HARGA": []
        }

        compact_text = re.sub(r'\s+', ' ', text)

        # Nama
        name_patterns = [
            r'\b\d+\.\s+([A-Z][A-Z\s]{2,40}?)(?=\s*\()' ,
            r'\b\d+\.\s+([A-Z][A-Z\s]{2,40}?)(?=\s+NIK\b)',
            r'\byang bernama\s+([A-Z][A-Za-z\.\'\-]+(?:\s+[A-Z][A-Za-z\.\'\-]+){0,4})',
            r'(?:Nama|Nama Lengkap)\s*[:\-]\s*([A-Z][A-Za-z\.\'\-]+(?:\s+[A-Z][A-Za-z\.\'\-]+){0,4})',
            r'bernama\s+([A-Z][A-Za-z\.\'\-]+(?:\s+[A-Z][A-Za-z\.\'\-]+){0,4})',
            r'(?:Bapak|Ibu|Tn\.?|Ny\.?)\s+([A-Z][A-Za-z\.\'\-]+(?:\s+[A-Z][A-Za-z\.\'\-]+){0,4})'
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, compact_text, re.IGNORECASE)
            for match in matches:
                candidate = self._clean_entity_candidate(match.strip())
                if candidate and len(candidate) >= 3:
                    fallback["NAMA"].append(candidate)

        # NIK
        for nik in re.findall(r'\b\d{16}\b', compact_text):
            fallback["NIK"].append(nik)

        # Alamat
        alamat_patterns = [
            r'(?:bertempat tinggal terakhir di|bertempat tinggal di|berdomisili di)\s+([^\.\n]+?)(?=\s+(?:yang telah meninggal|yang|pada|berdasarkan|adalah|semasa|dengan|\.))',
            r'(?:bertempat tinggal terakhir di|bertempat tinggal di|berdomisili di)\s+([^\.\n]+?)(?=\s+(?:yang|pada|berdasarkan|adalah|semasa|dengan|\.))',
            r'(?:Alamat|Beralamat|bertempat tinggal di|berdomisili di)\s*[:\-]?\s*([^\.\n]+?)(?=\s+(?:Pekerjaan|Ttl|Tempat|No\.?|RT\.?|RW\.?|Surat|Yang|Adalah|Dengan|Tanggal)\b|\.|$)',
            r'(Jl\.?\s+[^\.\n]+?)(?=\s+(?:Pekerjaan|Ttl|Tempat|Surat|Yang|Adalah|Dengan|Tanggal)\b|\.|$)'
        ]
        for pattern in alamat_patterns:
            matches = re.findall(pattern, compact_text, re.IGNORECASE)
            for match in matches:
                alamat = match.strip().rstrip(',')
                if len(alamat) > 5:
                    fallback["ALAMAT"].append(alamat)

        # Pekerjaan
        kerja_patterns = [
            r'(?:Pekerjaan|Profesi|Sebagai)\s*[:\-]?\s*([A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:Alamat|Beralamat|Tanggal|Tgl|Jabatan|Surat|Dengan|Adalah)\b|\.|$)',
            r'pekerjaan\s+sebagai\s+([A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:di|pada|yang|,|\.)|$)'
        ]
        for pattern in kerja_patterns:
            match = re.search(pattern, compact_text, re.IGNORECASE)
            if match:
                fallback["PEKERJAAN"].append(match.group(1).strip())
                break

        # Jabatan
        jabatan_patterns = [
            r'\b(Kepala [A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:NIP|$|\.|,))',
            r'\b(Lurah [A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:NIP|$|\.|,))',
            r'\b(Camat [A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:NIP|$|\.|,))',
            r'(?:Jabatan|Selaku)\s*[:\-]?\s*([A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:Alamat|Pekerjaan|Tanggal|Tgl|Surat|Dengan|Adalah)\b|\.|$)',
            r'sebagai\s+([A-Za-z][A-Za-z\s/\-]+?)(?=\s+(?:di|pada|yang|,|\.)|$)'
        ]
        for pattern in jabatan_patterns:
            matches = re.findall(pattern, compact_text, re.IGNORECASE)
            for match in matches:
                candidate = match.strip()
                if candidate and len(candidate) >= 3:
                    fallback["JABATAN"].append(candidate)

        # Tanggal
        date_patterns = [
            r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{1,2}-\d{1,2}\b'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, compact_text)
            if matches:
                fallback["TGL"].extend(matches[:3])
                break

        # Luas & harga
        for luas in re.findall(r'\b\d+(?:[\.,]\d+)?\s*(?:m2|m²|meter persegi)\b', compact_text, re.IGNORECASE):
            fallback["LUAS"].append(luas)
        for harga in re.findall(r'Rp\.?\s*\d+(?:[\.\,]\d{3})*(?:,\d+)?', compact_text, re.IGNORECASE):
            fallback["HARGA"].append(harga)

        return fallback

    def _clean_entity_candidate(self, value):
        """Trim noisy trailing words from extracted candidates."""
        cleaned = value.strip().strip(",.;:-")
        cleaned = re.split(
            r'\b(?:dari|yang|memiliki|adalah|bertempat|semasa|pada|dengan|untuk)\b',
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        return cleaned.strip(",.;:-")

    def process_document(self, file_path, output_json=None):
        """Full pipeline: Read → Extract → Output"""
        print(f"\n📄 Processing: {file_path}")

        # 1. Read document
        text = self.read_docx_document(file_path)
        if not text:
            print("❌ Could not read document")
            return None

        print(f"✓ Document loaded ({len(text)} chars)")

        # 2. Extract entities
        entities = self.extract_entities(text)

        # 3. Save results
        result = {
            "source_file": os.path.basename(file_path),
            "extracted_entities": entities,
            "text_preview": text[:500]  # First 500 chars preview
        }

        if output_json:
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✓ Results saved to {output_json}")

        return result

    def batch_process(self, input_folder, output_folder="./extraction_results"):
        """Process multiple documents"""
        os.makedirs(output_folder, exist_ok=True)

        if not os.path.exists(input_folder):
            print(f"❌ Input folder not found: {input_folder}")
            return

        docx_files = list(Path(input_folder).glob("*.docx"))
        if not docx_files:
            print(f"❌ No .docx files found in {input_folder}")
            return

        print(f"\n📦 Found {len(docx_files)} documents to process")

        all_results = []
        for idx, file_path in enumerate(docx_files, 1):
            print(f"\n[{idx}/{len(docx_files)}]", end=" ")

            output_path = os.path.join(
                output_folder,
                f"{file_path.stem}_entities.json"
            )

            result = self.process_document(str(file_path), output_path)
            if result:
                all_results.append(result)

        # Save batch results
        batch_output = os.path.join(output_folder, "batch_results.json")
        with open(batch_output, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Batch processing completed!")
        print(f"📌 Results saved to {output_folder}")

        return all_results


def main():
    """Demo pipeline"""
    print("="*70)
    print("  COMPLETE PIPELINE - NER EXTRACTION + TEXT GENERATION")
    print("="*70)

    pipeline = CompletePipeline()

    # Process sample documents
    input_folder = "./datasurat"
    if os.path.exists(input_folder):
        print(f"\n🔍 Processing documents from: {input_folder}")
        results = pipeline.batch_process(input_folder)

        if results:
            print("\n📋 Sample extraction result:")
            print(json.dumps(results[0]['extracted_entities'], indent=2, ensure_ascii=False))
    else:
        print(f"\n⚠️  Input folder not found: {input_folder}")
        print("    Create ./datasurat folder with .docx files to process")


if __name__ == "__main__":
    main()
