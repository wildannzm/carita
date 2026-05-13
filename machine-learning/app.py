from flask import Flask, request, jsonify, send_from_directory
import os, uuid
from dotenv import load_dotenv

# Import Semua Service
from services.vision import predict_image
from services.storyteller import generate_story
from services.knowledge import get_motif_data
from services.designer import create_smart_poster # <--- Pastikan ini ada

load_dotenv()
app = Flask(__name__)

def infer_category_from_motif(motif_id):
    motif_lower = (motif_id or "").lower()
    if motif_lower.startswith("batik_"):
        return "Batik"
    if motif_lower.startswith("anyaman_"):
        return "Anyaman"
    if motif_lower.startswith("tenun_"):
        return "Tenun"
    if motif_lower.startswith("motif_"):
        return "Motif"
    return "Umum"

# Konfigurasi Folder
UPLOAD_FOLDER = 'temp_uploads'
POSTER_FOLDER = 'static_posters'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(POSTER_FOLDER, exist_ok=True)

@app.route('/')
def home(): return "CARITA AI Service Ready! 🚀"

# --- ENDPOINT 1: ANALYZE (VISION) ---
@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files: return jsonify({"error": "No image"}), 400
    file = request.files['image']
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
    file.save(path)

    # 1. Vision AI
    res = predict_image(path)
    
    # Hapus file temp gambar asli (tapi simpan path untuk poster jika perlu nanti)
    # Untuk efisiensi, di flow nyata biasanya frontend kirim gambar lagi ke endpoint poster
    # Jadi kita hapus saja di sini biar bersih.
    os.remove(path) 

    if not res: 
        return jsonify({
            "status": "unknown",
            "message": "Maaf, motif tidak terdeteksi sebagai ciri khas Majalengka."
        }), 404
    
    motif_id = res['motif_id']
    brain = get_motif_data(motif_id)
    
    if brain.get('is_sacred'):
        return jsonify({
            "status": "blocked", 
            "warning": "⚠️ Motif Sakral Terdeteksi! Tidak dapat dikomersialkan."
        })

    raw_category = brain.get('category', 'Umum')
    category = raw_category
    if not raw_category or raw_category.strip().lower() in ["umum", "general", "unknown"]:
        category = infer_category_from_motif(motif_id)

    return jsonify({
        "status": "success",
        "data": {
            "motif_id": motif_id,
            "motif_name": motif_id.replace("_", " ").title(), 
            "confidence": res['confidence'],
            "philosophical_context": brain.get('text', 'Deskripsi belum tersedia.'),
            "category": category,
            "source": brain.get('source', 'Tim Riset')
        }
    })

# --- ENDPOINT 2: COMPOSE STORY (LLM) ---
@app.route('/compose-story', methods=['POST'])
def compose():
    d = request.json
    if not d or 'motif_name' not in d: return jsonify({"error": "Data tidak lengkap"}), 400

    name = d.get('motif_name')
    ctx = d.get('context_data', '')
    src = d.get('source', '')
    lang = d.get('language', 'Indonesia')

    story = generate_story(name, ctx, src, lang)
    return jsonify({"status": "success", "story": story})

# --- ENDPOINT 3: GENERATE POSTER (DESIGNER) ---
@app.route('/generate-poster', methods=['POST'])
def generate_poster_endpoint():
    # Cek File
    if 'image' not in request.files: return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    
    # Cek Data Teks
    title = request.form.get('title', 'Karya Majalengka')
    category = request.form.get('category', 'Umum')

    # Simpan Sementara
    in_path = os.path.join(UPLOAD_FOLDER, f"raw_poster_{uuid.uuid4()}.jpg")
    file.save(in_path)
    
    # Nama File Output
    out_filename = f"poster_{uuid.uuid4()}.jpg"
    
    try:
        # Jalankan AI Designer
        result_path = create_smart_poster(in_path, title, category, out_filename)
        
        # Hapus file mentah
        os.remove(in_path)
        
        if result_path:
            # Buat URL Publik
            # Contoh: http://localhost:5000/static_posters/poster_123.jpg
            poster_url = f"{request.host_url}static_posters/{out_filename}"
            return jsonify({"status": "success", "poster_url": poster_url})
        else:
            return jsonify({"error": "Gagal membuat poster"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- AKSES FILE POSTER ---
# Ini penting supaya URL poster bisa dibuka di browser
@app.route('/static_posters/<path:filename>')
def serve_poster(filename):
    return send_from_directory(POSTER_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)