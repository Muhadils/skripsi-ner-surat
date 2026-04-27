#!/usr/bin/env python3
"""
FLASK WEB APPLICATION - Sistem Generasi Surat Otomatis
Skripsi Nurfadilah Rahman - NLP & NER untuk Pembuatan Teks Otomatis
"""

from flask import Flask, render_template_string, request, send_file, jsonify
import os
import sys
from pathlib import Path
from text_generator import SuratAutomatisGenerator
import json
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize generator
generator = SuratAutomatisGenerator()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Generasi Surat Otomatis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 14px;
            opacity: 0.9;
        }

        .content {
            padding: 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }

        input[type="text"],
        input[type="date"],
        select,
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            font-family: inherit;
        }

        input[type="text"]:focus,
        input[type="date"]:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 600px) {
            .form-row {
                grid-template-columns: 1fr;
            }
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }

        button {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }

        .btn-secondary:hover {
            background: #e0e0e0;
        }

        .btn-small {
            padding: 8px 16px;
            font-size: 13px;
        }

        .preview-section {
            margin-top: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
            display: none;
        }

        .preview-section.active {
            display: block;
        }

        .preview-content {
            background: white;
            padding: 20px;
            border-radius: 5px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            font-family: 'Courier New', monospace;
        }

        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
        }

        .alert.show {
            display: block;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            padding: 20px;
        }

        .spinner {
            border: 3px solid #f0f0f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .instructions {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 3px;
            font-size: 13px;
        }

        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 Sistem Generasi Surat Otomatis</h1>
            <p>Natural Language Processing & Named Entity Recognition</p>
            <p style="font-size: 12px; margin-top: 5px;">Skripsi Nurfadilah Rahman - Universitas Muhammadiyah Makassar</p>
        </div>

        <div class="content">
            <div class="instructions">
                <strong>📋 Petunjuk Penggunaan:</strong>
                <p>1. Pilih jenis surat yang ingin dibuat</p>
                <p>2. Isi data-data yang diperlukan dengan lengkap</p>
                <p>3. Klik "Preview" untuk melihat hasil draft</p>
                <p>4. Klik "Download DOCX" untuk mengunduh dokumen siap cetak</p>
            </div>

            <div class="alert" id="alert"></div>

            <form id="suratForm">
                <div class="form-group">
                    <label for="suratType">Jenis Surat *</label>
                    <select id="suratType" required onchange="updateFormFields()">
                        <option value="">-- Pilih Jenis Surat --</option>
                        <option value="domisili">Surat Keterangan Domisili</option>
                        <option value="usaha">Surat Keterangan Usaha</option>
                        <option value="pengantar">Surat Pengantar/Permohonan</option>
                    </select>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="nama">Nama Lengkap *</label>
                        <input type="text" id="nama" name="nama" placeholder="Contoh: Nurfadilah Rahman" required>
                    </div>
                    <div class="form-group">
                        <label for="nik">NIK (Nomor Identitas) *</label>
                        <input type="text" id="nik" name="nik" placeholder="Contoh: 7315076512800001" required>
                    </div>
                </div>

                <div class="form-group">
                    <label for="alamat">Alamat Lengkap *</label>
                    <input type="text" id="alamat" name="alamat" placeholder="Contoh: Tuppu, Kel. Tadokkong, Kec. Lembang, Kab. Pinrang" required>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="pekerjaan">Pekerjaan/Profesi *</label>
                        <input type="text" id="pekerjaan" name="pekerjaan" placeholder="Contoh: Mahasiswa, Karyawan, Petani" required>
                    </div>
                    <div class="form-group">
                        <label for="tanggal">Tanggal Surat *</label>
                        <input type="date" id="tanggal" name="tanggal" required>
                    </div>
                </div>

                <div class="form-group" id="jabatanGroup" style="display: none;">
                    <label for="jabatan">Jabatan</label>
                    <input type="text" id="jabatan" name="jabatan" placeholder="Contoh: Direktur, Manager, Staf">
                </div>

                <div class="button-group">
                    <button type="button" class="btn-primary btn-small" onclick="previewSurat()">👁️ Preview</button>
                    <button type="button" class="btn-primary btn-small" onclick="downloadSurat()">⬇️ Download DOCX</button>
                    <button type="reset" class="btn-secondary btn-small">🔄 Reset</button>
                </div>
            </form>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Sedang memproses...</p>
            </div>

            <div class="preview-section" id="previewSection">
                <h3>📋 Preview Surat</h3>
                <div class="preview-content" id="previewContent"></div>
            </div>
        </div>

        <div class="footer">
            <p>© 2026 - Skripsi Nurfadilah Rahman | Program Studi Informatika | Universitas Muhammadiyah Makassar</p>
        </div>
    </div>

    <script>
        // Set default date to today
        document.getElementById('tanggal').valueAsDate = new Date();

        function updateFormFields() {
            const suratType = document.getElementById('suratType').value;
            const jabatanGroup = document.getElementById('jabatanGroup');

            if (suratType === 'usaha') {
                jabatanGroup.style.display = 'block';
            } else {
                jabatanGroup.style.display = 'none';
            }
        }

        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert show alert-${type}`;
            setTimeout(() => alert.classList.remove('show'), 5000);
        }

        function formatDate(dateString) {
            const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
            const date = new Date(dateString);
            return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
        }

        function previewSurat() {
            const suratType = document.getElementById('suratType').value;
            if (!suratType) {
                showAlert('❌ Pilih jenis surat terlebih dahulu!', 'error');
                return;
            }

            const entities = {
                'nama': document.getElementById('nama').value,
                'nik': document.getElementById('nik').value,
                'alamat': document.getElementById('alamat').value,
                'pekerjaan': document.getElementById('pekerjaan').value,
                'tanggal': formatDate(document.getElementById('tanggal').value),
                'jabatan': document.getElementById('jabatan').value
            };

            // Validate
            if (!entities.nama || !entities.nik || !entities.alamat) {
                showAlert('❌ Isi semua field yang diperlukan!', 'error');
                return;
            }

            document.getElementById('loading').style.display = 'block';

            fetch('/api/preview', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'surat_type': suratType, 'entities': entities})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('previewContent').textContent = data.content;
                    document.getElementById('previewSection').classList.add('active');
                    showAlert('✅ Preview berhasil dibuat!', 'success');
                } else {
                    showAlert('❌ ' + (data.error || 'Gagal membuat preview'), 'error');
                }
            })
            .catch(e => showAlert('❌ Error: ' + e, 'error'))
            .finally(() => document.getElementById('loading').style.display = 'none');
        }

        function downloadSurat() {
            const suratType = document.getElementById('suratType').value;
            if (!suratType) {
                showAlert('❌ Pilih jenis surat terlebih dahulu!', 'error');
                return;
            }

            const entities = {
                'nama': document.getElementById('nama').value,
                'nik': document.getElementById('nik').value,
                'alamat': document.getElementById('alamat').value,
                'pekerjaan': document.getElementById('pekerjaan').value,
                'tanggal': formatDate(document.getElementById('tanggal').value),
                'jabatan': document.getElementById('jabatan').value
            };

            if (!entities.nama || !entities.nik || !entities.alamat) {
                showAlert('❌ Isi semua field yang diperlukan!', 'error');
                return;
            }

            document.getElementById('loading').style.display = 'block';

            fetch('/api/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'surat_type': suratType, 'entities': entities})
            })
            .then(r => r.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Surat_${suratType}_${new Date().getTime()}.docx`;
                a.click();
                showAlert('✅ File berhasil diunduh!', 'success');
            })
            .catch(e => showAlert('❌ Error download: ' + e, 'error'))
            .finally(() => document.getElementById('loading').style.display = 'none');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/preview', methods=['POST'])
def api_preview():
    """Generate preview surat"""
    try:
        data = request.json
        surat_type = data.get('surat_type')
        entities = data.get('entities', {})

        content = generator.process_surat(surat_type, entities)
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def api_download():
    """Download surat as DOCX"""
    try:
        data = request.json
        surat_type = data.get('surat_type')
        entities = data.get('entities', {})

        # Generate content
        content = generator.process_surat(surat_type, entities)

        # Create polished DOCX format
        output = generator.create_docx_bytes(content)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f'Surat_{surat_type}.docx'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    print("="*70)
    print("  FLASK APP - SISTEM GENERASI SURAT OTOMATIS")
    print("="*70)
    print("\n🚀 Starting server...")
    print("📱 Open browser: http://localhost:5000")
    print("⚙️  Press Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
