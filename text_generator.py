#!/usr/bin/env python3
"""
TEXT GENERATION SYSTEM using IndoBART
Skripsi Nurfadilah Rahman - Pembuatan Teks Otomatis
"""

import json
import torch
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re

class SuratAutomatisGenerator:
    """
    Generate surat administrasi otomatis dari extracted entities
    """
    def __init__(self, model_name="indobenchmark/indobart"):
        print("Initializing IndoBART model...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.generator = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device="cpu"  # Use CPU for compatibility
            )
            print(f"✓ Model loaded: {model_name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not load {model_name}: {e}")
            print("   Will use template-based generation instead")
            self.generator = None

    def extract_entities_from_text(self, text):
        """
        Extract entities dari teks surat
        Menggunakan regex patterns dan simple matching
        """
        entities = {
            "nama": self._extract_nama(text),
            "nik": self._extract_nik(text),
            "alamat": self._extract_alamat(text),
            "pekerjaan": self._extract_pekerjaan(text),
            "tanggal": self._extract_tanggal(text),
            "jabatan": self._extract_jabatan(text),
        }
        return entities

    def _extract_nama(self, text):
        """Extract nama orang dari teks"""
        # Pola: nama di antara kalimat
        patterns = [
            r'bernama\s+([A-Z][a-z\s]+)',
            r'(?:Bapak|Ibu|Tn\.?|Ny\.?)\s+([A-Z][a-z\s]+?)(?:\s+(?:dari|bin|binti|bin|alias|atau))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Nama Lengkap"

    def _extract_nik(self, text):
        """Extract NIK (16 digit nomor)"""
        match = re.search(r'\b(\d{16})\b', text)
        return match.group(1) if match else "0000000000000000"

    def _extract_alamat(self, text):
        """Extract alamat dari teks"""
        patterns = [
            r'(?:bertempat tinggal|bertempat|domisili|alamat)(?:\s+di)?\s+([A-Za-z\s,\.]+?)(?:\s+(?:Kel\.|Kec\.|Kab\.|yang|dengan))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Alamat, Kelurahan, Kecamatan, Kabupaten"

    def _extract_pekerjaan(self, text):
        """Extract pekerjaan/profesi"""
        patterns = [
            r'(?:pekerjaan|profesi|sebagai)\s+([A-Za-z\s]+?)(?:\s+(?:dengan|dari|yang))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Pekerjaan/Profesi"

    def _extract_tanggal(self, text):
        """Extract tanggal dari teks"""
        match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', text)
        if match:
            return f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return "01 Januari 2025"

    def _extract_jabatan(self, text):
        """Extract jabatan/posisi"""
        patterns = [
            r'(?:sebagai|jabatan)\s+([A-Za-z\s]+?)(?:\s+(?:dari|di|yang))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Jabatan"

    def generate_surat_keterangan_domisili(self, entities):
        """Generate Surat Keterangan Domisili"""
        template = f"""Surat Keterangan Domisili

Yang bertanda tangan di bawah ini Lurah Tadokkong, Kecamatan Lembang, Kabupaten Pinrang, Provinsi Sulawesi Selatan, dengan ini menerangkan bahwa:

Nama                    : {entities.get('nama', 'Nama Lengkap')}
Nomor Induk Kependudukan: {entities.get('nik', '0000000000000000')}
Jenis Kelamin          : [Laki-laki/Perempuan]
Alamat                 : {entities.get('alamat', 'Alamat, Kelurahan, Kecamatan, Kabupaten')}
Pekerjaan              : {entities.get('pekerjaan', 'Pekerjaan/Profesi')}

Adalah benar penduduk yang bertempat tinggal di wilayah kelurahan Tadokkong, Kecamatan Lembang, Kabupaten Pinrang, Provinsi Sulawesi Selatan.

Surat keterangan ini diberikan untuk keperluan: [Sebutkan Keperluan]

Demikian surat keterangan ini dibuat dengan sebenar-benarnya dan dapat dipergunakan sebagai mana mestinya.

Diberikan di: Tadokkong
Tanggal: {entities.get('tanggal', '01 Januari 2025')}

Lurah Tadokkong
[Tanda Tangan dan Stempel]
[Nama Lengkap Lurah]
NIP. [Nomor Induk Pegawai]"""
        return template

    def generate_surat_keterangan_usaha(self, entities):
        """Generate Surat Keterangan Usaha"""
        template = f"""Surat Keterangan Usaha

Yang bertanda tangan di bawah ini Lurah Tadokkong, Kecamatan Lembang, Kabupaten Pinrang, menerangkan bahwa:

Nama                    : {entities.get('nama', 'Nama Lengkap')}
Nomor Induk Kependudukan: {entities.get('nik', '0000000000000000')}
Alamat                 : {entities.get('alamat', 'Alamat')}
Pekerjaan/Usaha        : {entities.get('pekerjaan', 'Jenis Usaha')}

Adalah benar memiliki usaha di Kelurahan Tadokkong, Kecamatan Lembang, Kabupaten Pinrang dan layak diberikan surat keterangan usaha untuk keperluan: [Sebutkan Keperluan]

Surat keterangan ini berlaku selama 1 (satu) tahun apabila diperlukan dapat diperpanjang kembali.

Demikian surat keterangan ini dibuat dengan sebenar-benarnya untuk dapat dipergunakan sebagaimana mestinya.

Diberikan di: Tadokkong
Tanggal: {entities.get('tanggal', '01 Januari 2025')}

Lurah Tadokkong
[Tanda Tangan dan Stempel]
[Nama Lengkap Lurah]
NIP. [Nomor Induk Pegawai]"""
        return template

    def generate_surat_permohonan_pengantar(self, entities):
        """Generate Surat Pengantar/Permohonan"""
        template = f"""Surat Pengantar

Kepada Yth. [Instansi Tujuan]
di Tempat

Dengan hormat, yang bertanda tangan di bawah ini Lurah Tadokkong dengan ini menerangkan bahwa:

Nama                    : {entities.get('nama', 'Nama Lengkap')}
Nomor Induk Kependudukan: {entities.get('nik', '0000000000000000')}
Jenis Kelamin          : [Laki-laki/Perempuan]
Alamat                 : {entities.get('alamat', 'Alamat')}

Adalah benar penduduk Kelurahan Tadokkong, Kecamatan Lembang, Kabupaten Pinrang, Sulawesi Selatan dan untuk keperluan:

[Sebutkan Maksud dan Tujuan]

Oleh karena itu kami mohon bantuan dan kerja sama Bapak/Ibu dalam memberikan pelayanan kepada yang bersangkutan sebagaimana mestinya.

Atas perhatian dan bantuan Bapak/Ibu diucapkan terimakasih.

Diberikan di: Tadokkong
Tanggal: {entities.get('tanggal', '01 Januari 2025')}

Lurah Tadokkong
[Tanda Tangan dan Stempel]
[Nama Lengkap Lurah]
NIP. [Nomor Induk Pegawai]"""
        return template

    def save_to_docx(self, text, filename):
        """Save generated text to DOCX file"""
        doc = Document()

        # Add content
        for line in text.split('\n'):
            p = doc.add_paragraph(line)
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(6)

        doc.save(filename)
        print(f"✓ Saved to {filename}")

    def process_surat(self,surat_type, entities):
        """Process and generate specific surat type"""
        if surat_type == "domisili":
            return self.generate_surat_keterangan_domisili(entities)
        elif surat_type == "usaha":
            return self.generate_surat_keterangan_usaha(entities)
        elif surat_type == "pengantar":
            return self.generate_surat_permohonan_pengantar(entities)
        else:
            return "Tipe surat tidak dikenal"


def main():
    """Demo usage"""
    print("="*70)
    print("  SISTEM GENERASI SURAT ADMINISTRASI OTOMATIS")
    print("="*70)

    # Initialize generator
    generator = SuratAutomatisGenerator()

    # Example entities (biasanya dari NER extraction)
    example_entities = {
        "nama": "Nurfadilah Rahman",
        "nik": "7315076512800001",
        "alamat": "Tuppu, Kel. Tadokkong, Kec. Lembang, Kab. Pinrang",
        "pekerjaan": "Mahasiswa/Karyawan",
        "tanggal": "25 April 2026",
        "jabatan": "Operator",
    }

    # Generate different types of surats
    surat_types = ["domisili", "usaha", "pengantar"]

    for surat_type in surat_types:
        print(f"\n📄 Generating: Surat Keterangan {surat_type.upper()}")
        surat_text = generator.process_surat(surat_type, example_entities)

        # Print preview
        print("\n" + "="*70)
        print(surat_text[:500] + "...")
        print("="*70)

        # Save to DOCX
        output_file = f"./hasil_surat_{surat_type}.docx"
        generator.save_to_docx(surat_text, output_file)

    print("\n✅ Generation completed!")
    print("📦 Check hasil_surat_*.docx files for generated documents")


if __name__ == "__main__":
    main()
