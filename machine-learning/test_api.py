import requests
import os
import json

# Konfigurasi URL
BASE_URL = "http://localhost:5000"
# Tentukan gambar tes
TEST_IMAGE_PATH = os.path.join("imgtest", "aseupan.jpg") 

def print_separator(title):
    print("\n" + "="*50)
    print(f"🧪 {title}")
    print("="*50)

def test_1_analyze():
    print_separator("TES 1: ANALISA GAMBAR (Vision + Knowledge)")
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Error: Gambar tes tidak ditemukan di {TEST_IMAGE_PATH}")
        return None

    url = f"{BASE_URL}/analyze"
    try:
        with open(TEST_IMAGE_PATH, 'rb') as img:
            print(f"📤 Mengirim gambar: {TEST_IMAGE_PATH}...")
            files = {'image': img}
            response = requests.post(url, files=files)
        
        # LOGIKA KETAT: Hanya terima 200 OK
        if response.status_code == 200:
            data = response.json()
            print("✅ SUKSES! Hasil Analisa:")
            print(json.dumps(data, indent=2))
            return data['data'] # Kembalikan data valid
        elif response.status_code == 404:
            print("⛔ UNKNOWN: Motif tidak dikenali (Sesuai harapan untuk motif asing).")
            return None
        else:
            print(f"❌ GAGAL ({response.status_code}):", response.text)
            return None
    except Exception as e:
        print(f"❌ Error Koneksi: {e}")
        return None

def test_2_storyteller(motif_data):
    print_separator("TES 2: GENERATE CERITA (LLM)")
    
    # CEGAH JALAN KALAU DATA KOSONG
    if not motif_data:
        print("⚠️ SKIP: Tes dilewati karena Analisa Gagal/Unknown.")
        return

    url = f"{BASE_URL}/compose-story"
    payload = {
        "motif_name": motif_data['motif_name'],
        "context_data": motif_data['philosophical_context'],
        "source": motif_data['source'],
        "language": "Sunda"
    }

    print(f"📤 Mengirim prompt untuk motif: {payload['motif_name']}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            print("✅ SUKSES! Cerita Terbuat:")
            print("-" * 20)
            print(res_json['story'])
            print("-" * 20)
        else:
            print(f"❌ GAGAL ({response.status_code}):", response.text)
    except Exception as e:
        print(f"❌ Error Koneksi: {e}")

def test_3_poster(motif_data):
    print_separator("TES 3: GENERATE POSTER")
    
    # CEGAH JALAN KALAU DATA KOSONG (PERBAIKAN UTAMA)
    if not motif_data:
        print("⛔ SKIP: Poster TIDAK DIBUAT karena motif tidak valid/unknown.")
        print("   (Ini perilaku yang BENAR. Sistem menolak memproses motif asing).")
        return

    if not os.path.exists(TEST_IMAGE_PATH): return

    url = f"{BASE_URL}/generate-poster"
    
    # Ambil data asli dari hasil analisa
    title = motif_data['motif_name']
    category = motif_data['category']

    print(f"🎨 Membuat poster untuk '{title}'...")

    try:
        with open(TEST_IMAGE_PATH, 'rb') as img:
            files = {'image': img}
            data = {'title': title, 'category': category}
            response = requests.post(url, files=files, data=data)

        if response.status_code == 200:
            res_json = response.json()
            print("✅ SUKSES! Poster jadi di:")
            print(res_json['poster_url'])
        else:
            print(f"❌ GAGAL ({response.status_code}):", response.text)

    except Exception as e:
        print(f"❌ Error Koneksi: {e}")

if __name__ == "__main__":
    try:
        requests.get(BASE_URL)
        print("🚀 Server terdeteksi online!")
        
        # ALUR DATA YANG BENAR
        hasil_analisa = test_1_analyze()     # Langkah 1
        test_2_storyteller(hasil_analisa)    # Langkah 2 (Cuma jalan kalau 1 sukses)
        test_3_poster(hasil_analisa)         # Langkah 3 (Cuma jalan kalau 1 sukses)
        
    except requests.exceptions.ConnectionError:
        print("\n⛔ ERROR FATAL: Server Flask belum jalan!")