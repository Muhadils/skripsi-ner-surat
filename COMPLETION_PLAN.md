# 📋 PLAN PENYELESAIAN SKRIPSI NER SURAT

## Status Saat Ini
- ✅ Skripsi: Ditulis lengkap (BAB I-III lengkap, BAB IV intro)
- ✅ Dataset: 170 dokumen, sudah di-prepare ke JSON
- ✅ Base Model: IndoBERT sudah di-download locally
- ❌ Models: Belum terlatih (PERSON, NIK, PROFIL, LUAS_HARGA)
- ❌ Text Generation: Belum ada IndoBART integration
- ❌ Interface: Belum ada

## Tasks yang Perlu Dikerjakan

### 1. FIX BUGS (DONE ✅)
- [x] Fix `uji_model_ner.py`: Add `read_docx_full()` function

### 2. TRAIN ALL NER MODELS
- [ ] Train PERSON NER model
- [ ] Train NIK NER model  
- [ ] Train PROFIL NER model (ALAMAT, KERJA, TGL, JABATAN)
- [ ] Train LUAS_HARGA NER model
- [ ] Evaluate semua model

### 3. CREATE TEXT GENERATION SYSTEM
- [ ] Download/prepare IndoBART model
- [ ] Create generator script using trained NER + IndoBART
- [ ] Create template-based generation
- [ ] Integration test

### 4. CREATE USER INTERFACE
- [ ] Create Flask web app OR CLI tool
- [ ] Input form untuk entity/data
- [ ] Output generated text
- [ ] Download hasil (DOCX/PDF)

### 5. COMPLETE THESIS
- [ ] BAB IV.B: Results & Analysis
- [ ] Evaluation metrics (Precision, Recall, F1-Score)
- [ ] Discussion
- [ ] Conclusion

## Resources Needed
- RAM: 8GB (available)
- GPU: Not available (akan pakai CPU, lebih lambat)
- Time: ~2-3 jam untuk training dan testing

## Execution Order
1. Fix bugs → Train models → Test extraction
2. Setup IndoBART → Create generator
3. Build interface
4. Run experiments & collect results → Write BAB IV
