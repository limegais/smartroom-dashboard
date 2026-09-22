# Dokumentasi Lengkap: Sistem Optimasi, Switching Algoritma & Notifikasi Telegram
**Smart Room IoT & Machine Learning Optimization System**

---

## 📌 1. Pendahuluan & Arsitektur Fitur

Sistem **Smart Room** menggunakan dua algoritma kecerdasan buatan / metaheuristik — **Genetic Algorithm (GA)** dan **Particle Swarm Optimization (PSO)** — untuk mengontrol dua perangkat utama secara otomatis dan efisien:
1. **Air Conditioner (AC)**: Memaksimalkan kenyamanan termal (suhu & kelembaban) serta meminimalkan konsumsi daya listrik.
2. **Lampu (Lamp)**: Memaksimalkan kenyamanan pencahayaan (Lux) sesuai keberadaan penghuni serta meminimalkan konsumsi energi.

Fitur **Switching Algoritma** memungkinkan pengguna (*operator/admin*) untuk menukar atau memilih algoritma optimasi yang digunakan oleh masing-masing perangkat secara *real-time* tanpa menghentikan sistem.

---

## 🎛️ 2. Matriks Kombinasi Algoritma

Sistem menyediakan 4 kombinasi metode optimasi yang dapat dipilih melalui antarmuka dashboard:

| Kunci Konfigurasi (`config`) | Algoritma AC (`ac_algo`) | Algoritma Lampu (`lamp_algo`) | Deskripsi Mode |
| :--- | :--- | :--- | :--- |
| **`ga_pso`** *(Default)* | **GA** | **PSO** | Mode standar: GA mengoptimasi AC, PSO mengoptimasi Lampu |
| **`pso_ga`** | **PSO** | **GA** | Mode tukar: PSO mengoptimasi AC, GA mengoptimasi Lampu |
| **`ga_ga`** | **GA** | **GA** | Mode seragam GA: GA mengoptimasi AC & Lampu |
| **`pso_pso`** | **PSO** | **PSO** | Mode seragam PSO: PSO mengoptimasi AC & Lampu |

---

## 🔬 3. Detail Cara Kerja Algoritma pada Masing-Masing Perangkat

### 3.1. GA pada AC (`run_ga_optimization`)
* **Tujuan**: Menemukan kombinasi variabel AC yang memberikan kenyamanan termal maksimal dengan konsumsi energi paling efisien.
* **Kromosom 4D**: `[Suhu (16–30°C), Kecepatan Fan (1–4), Mode (0=COOL, 1=DRY, 2=FAN, 3=AUTO), Target RH (30–80%)]`
* **Fitness Function**: Memaksimalkan skor kenyamanan termal & efisiensi energi (0–149 poin, dinormalisasi ke 0–100%).
* **Proses**: Inisialisasi populasi (15 individu) -> Seleksi roda roulette & elitisme -> Crossover titik tunggal (85%) -> Mutasi acak (30%) -> Evaluasi fitness -> Mengaplikasikan setting optimal.

### 3.2. PSO pada Lampu (`run_pso_optimization`)
* **Tujuan**: Menyesuaikan redup/terang lampu (PWM) agar intensitas cahaya (Lux) ruangan mencapai **350 Lux** (ada orang) atau **0 Lux** (kosong).
* **Partikel 2D**: `[PWM1 (0–255), PWM2 (0–255)]`
* **Fitness Function**: Meminimalkan error kuadrat Lux terhadap target 350 Lux.
* **Proses**: Inisialisasi 10 partikel titik PWM -> Kirim sinyal PWM ke lampu ESP32 via MQTT -> Jeda 5 detik hingga sensor LDR stabil -> Baca nilai Lux nyata ($L_1, L_2, L_3$) -> Perbarui $p_{best}$ dan $g_{best}$.

### 3.3. PSO pada AC (`run_pso_for_ac`) — *[Sebaliknya]*
* **Tujuan**: Menggunakan pergerakan kawanan partikel untuk mencari parameter AC paling ideal secara kontinu.
* **Partikel 4D**: `[Suhu (°C), Fan (1–4), Mode (0–3), RH (30–80%)]`
* **Fitness Function**: Memaksimalkan skor kenyamanan termal (sama dengan GA AC).
* **Proses**: Partikel 4D bergerak di ruang pencarian berdasarkan kecepatan $V$. Memakai *Inersia Adaptif* ($w=0.5 \to 0.3$) agar pencarian di awal luas dan memuluskan konvergensi. Posisi dipotong (*clipped*) sesuai batas fisik AC.

### 3.4. GA pada Lampu (`run_ga_for_lamp`) — *[Sebaliknya]*
* **Tujuan**: Menggunakan proses evolusi generasi untuk menemukan nilai PWM lampu dengan umpan balik sensor nyata.
* **Kromosom 2D**: `[PWM1 (0–255), PWM2 (0–255)]`
* **Fitness Function**: Meminimalkan error Lux terhadap target 350 Lux.
* **Proses**: Populasi 15 kromosom PWM dibuat -> Individu PWM terbaik dari tiap generasi dikirim ke lampu via MQTT -> Jeda 5 detik per generasi -> Membaca Lux nyata sensor -> Evaluasi error fitness -> Seleksi elitisme, crossover, dan mutasi.

---

## 📊 4. Detail Fungsi Fitness (GA & PSO)

Fungsi fitness adalah inti dari setiap algoritma optimasi. Fungsi ini mengubah kondisi sensor ruangan dan paramater kontrol yang diusulkan menjadi satu nilai skor numerik — semakin tinggi skor, semakin baik solusi tersebut. Semua logika fitness ada di file [`fitness.py`](fitness.py).

### 4.1. Fitness GA: Optimasi AC (`calculate_ac_fitness`)

Menerima dua parameter: `temp_set` (suhu AC, 16–30°C) dan `fan_speed` (kecepatan kipas, 1–3). **Skor total maksimal ≈ 100 poin.**

| No. | Komponen | Bobot (Maks) | Cara Kerja |
| :-- | :------- | :----------: | :--------- |
| 1 | **Comfort Score** | 40 | Skor Gaussian terhadap target suhu ideal. Target berubah berdasarkan **waktu** (pagi/siang/sore/malam) dan **ada-tidaknya orang**. Juga dikompensasi terhadap *tren suhu* (apakah ruangan memanas atau mendingin). |
| 2 | **Humidity Response** | 15 | Jika kelembapan >60%, mendorong suhu lebih rendah & kipas lebih cepat (dehumidifikasi). Jika <40% (terlalu kering), menghindari pendinginan berlebih. Di kisaran ideal 40–60%, skor penuh diberikan. |
| 3 | **Fan Appropriateness** | 15 | Menilai kesesuaian kecepatan kipas terhadap selisih suhu ruangan dan suhu AC. Selisih besar → kipas harus kencang; selisih kecil → kipas rendah. |
| 4 | **Energy Efficiency** | 15 | Menghitung estimasi daya AC dan memberi skor lebih tinggi untuk pengaturan yang lebih hemat. **Bobot berubah dinamis**: hemat lebih penting saat ruangan **kosong** (bobot 15), lebih sedikit saat ada orang (bobot 5). |
| 5 | **Uniformity Bonus** | 8 | Bonus jika distribusi suhu dari 3 sensor DHT22 seragam. Jika tidak seragam, bonus diberikan bila kipas cepat (membantu sirkulasi). |
| 6 | **Trend Compensation** | 7 | Bonus proaktif: jika ruangan sedang cepat memanas, pengaturan suhu rendah diberi nilai lebih; jika mendingin, pengaturan moderat diberi nilai lebih. |
| — | **Penalti Overcooling** | –maks 18 | Pengurangan skor jika AC disetel terlalu dingin (<24°C) padahal ruangan **kosong**. |
| — | **Penalti Ekstrem** | –10 | Pengurangan skor jika suhu <18°C dipadukan dengan kipas penuh (fan=3). |

#### Formula Estimasi Daya AC

```python
ac_power = (30.0 - temp_set) * 50.0 + fan_speed * 30.0  # Watt (estimasi)
max_power = (30.0 - 16.0) * 50.0 + 3 * 30.0             # Daya maksimum ≈ 790 Watt
energy_ratio = 1.0 - (ac_power / max_power)              # 0.0 = boros, 1.0 = hemat

# Bobot skor efisiensi:
if person_detected:
    fitness += energy_ratio * 5.0   # Kenyamanan diutamakan
else:
    fitness += energy_ratio * 15.0  # Penghematan diutamakan
```

---

### 4.2. Fitness PSO: Optimasi Lampu (`calculate_lamp_fitness`)

Menerima satu parameter: `brightness` (kecerahan lampu, 0–100%). **Skor total maksimal ≈ 100 poin.**

| No. | Komponen | Bobot (Maks) | Cara Kerja |
| :-- | :------- | :----------: | :--------- |
| 1 | **Lighting Comfort** | 50 | Jika ada orang: target total cahaya 300–500 lux (standar kerja/belajar). Terlalu redup (<200) atau terlalu terang (>600) akan dikurangi secara bertahap. Jika kosong: brightness ≤5% mendapat skor maksimal. |
| 2 | **Energy Efficiency** | 30 | Semakin rendah `brightness`, semakin hemat, semakin tinggi skor. **Bobot berubah dinamis**: hemat lebih penting saat kosong (bobot 30), lebih sedikit saat ada orang (bobot 10). |
| 3 | **Ambient Adaptation** | 20 | Menyesuaikan kecerahan lampu dengan kondisi cahaya alami (`ambient_lux`). Cahaya alami cukup (≥400 lux) → lampu harus diredup. Kondisi gelap (<200 lux) → lampu harus terang. Jika kosong, komponen ini diabaikan. |

#### Formula Estimasi Daya Lampu

```python
lamp_power = brightness * 0.5   # Watt (asumsi: 100% brightness = 50 Watt)
max_power  = 100 * 0.5          # 50 Watt
energy_ratio = 1 - (lamp_power / max_power)  # 0.0 = boros, 1.0 = hemat

# Bobot skor efisiensi:
if person_detected:
    fitness += energy_ratio * 10  # Kenyamanan diutamakan
else:
    fitness += energy_ratio * 30  # Penghematan diutamakan
```

#### Estimasi Total Lux Ruangan

```python
lamp_lux_contribution = brightness * 5  # 1% brightness ≈ 5 lux
total_lux = ambient_lux + lamp_lux_contribution
```

---

### 4.3. Ringkasan Bobot Dinamis Berdasarkan Kehadiran Orang

| Kondisi | Prioritas GA (AC) | Prioritas PSO (Lampu) |
| :------ | :---------------- | :-------------------- |
| **Ada orang** | Kenyamanan termal (maks 40) >> Efisiensi daya (maks 5) | Kenyamanan cahaya (maks 50) >> Efisiensi daya (maks 10) |
| **Kosong** | Efisiensi daya (maks 15) + Penalti *overcooling* | Efisiensi daya (maks 30) + Matikan lampu (maks 50) |

---

## 📲 5. Sistem Notifikasi Telegram (Ambang Batas Offline 10 Menit)

Sistem dilengkapi dengan pemantau kesehatan perangkat (*sensor health detection*) berbasis **Telegram Bot Alert**:

* **Konfigurasi Telegram**:
  - `TELEGRAM_BOT_TOKEN`: `8635310992:AAEXVrdT2r2aWg-8lb7txKIShN04wjzgnkI`
  - `TELEGRAM_CHAT_ID`: `6029706835`
* **Aturan Ambang Batas (Threshold)**:
  - `TELEGRAM_OFFLINE_THRESHOLD_S = 600` (600 detik = **10 Menit**).
  - Notifikasi Telegram **HANYA dikirimkan setelah perangkat terputus/offline secara terus-menerus selama minimal 10 menit**.
  - Pencegahan Spam: Pesan peringatan hanya dikirim **1x** saat ambang batas 10 menit tercapai.
  - Recovery Alert: Ketika perangkat terhubung kembali (*online*), Telegram akan menerima 1x notifikasi pemulihan (*back online*).

---

## ⚙️ 6. Arsitektur Backend (`dashboard/app.py`)

### 5.1. Pengelolaan State Central
State algoritma dikelola oleh variabel global di server Flask:
```python
opt_algo_config = 'ga_pso'  # Opsi: 'ga_pso', 'pso_ga', 'ga_ga', 'pso_pso'
OPT_ALGO_OPTIONS = {'ga_pso', 'pso_ga', 'ga_ga', 'pso_pso'}

def _get_ac_algo():
    return 'pso' if opt_algo_config in ('pso_ga', 'pso_pso') else 'ga'

def _get_lamp_algo():
    return 'ga' if opt_algo_config in ('pso_ga', 'ga_ga') else 'pso'
```

### 5.2. API Endpoint (`/api/ml/algo`)
- **`GET /api/ml/algo`**: Mengembalikan status algoritma aktif (`config`, `ac_algo`, `lamp_algo`).
- **`POST /api/ml/algo`**: Menerima payload JSON `{"config": "pso_ga"}`.
  - Memperbarui `opt_algo_config`.
  - Meng-update dictionary telemetry `mqtt_data['system']`.
  - Memancarkan pesan WebSocket `mqtt_update` ke seluruh klien.
  - Meluncurkan thread optimasi baru secara otomatis (`run_optimization_cycle('both')`).

---

## 🖥️ 7. Arsitektur Frontend (`dashboard.js` & `dashboard_v2.js`)

### 6.1. Alur Pembaruan UI Dinamis
Saat pengguna mengeklik salah satu kartu algoritma:
1. **Optimistic Update**: UI langsung menyoroti kartu yang diklik (border biru, badge ACTIVE) tanpa menunggu server.
2. **POST API**: Mengirim permintaan HTTP POST ke `/api/ml/algo`.
3. **Pembaruan Label & Grafik**:
   - Judul Ringkasan: `summary-ac-title` ("GA → AC" atau "PSO → AC") & `summary-lamp-title` ("PSO → Lamp" atau "GA → Lamp").
   - Judul Grafik: `chart-ac-title` & `chart-lamp-title`.
   - Legenda & Warna Grafik: Dataset `gaFitness` berubah warna (Biru untuk GA, Cyan untuk PSO) dan label dataset menyesuaikan secara dinamis.
   - Header Tabel Riwayat: `hist-ac-title` & `hist-lamp-title` diperbarui.

---

## 📖 8. Panduan Penggunaan (User Manual)

1. Buka dashboard Smart Room dan navigasi ke menu **Machine Learning Optimization**.
2. Pada bagian **Select Algorithm Configuration**, klik salah satu kartu algoritma yang diinginkan (misal **`PSO | GA`**).
3. Status indikator akan menampilkan **"Saving..."** diikuti oleh **"✓ Saved"**.
4. Mesin backend akan otomatis menjalankan optimasi menggunakan algoritma baru dan memperbarui grafik secara live.

---
*Dokumentasi ini dibuat secara otomatis untuk proyek Smart Room IoT & Machine Learning.*
