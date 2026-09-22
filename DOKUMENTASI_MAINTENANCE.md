# 📖 DOKUMENTASI MAINTENANCE LENGKAP
# Smart Room IoT — Panduan untuk Asisten Lab

> **Dokumen ini ditujukan untuk asisten lab selanjutnya** yang akan bertanggung jawab memelihara (maintain) sistem Smart Room IoT di Lab IoT UNS. Seluruh informasi yang dibutuhkan untuk menjalankan, memelihara, dan troubleshoot sistem tercakup di sini.

---

## 📋 Daftar Isi

1. [Gambaran Umum Sistem](#1-gambaran-umum-sistem)
2. [Arsitektur & Alur Data](#2-arsitektur--alur-data)
3. [Struktur File & Direktori](#3-struktur-file--direktori)
4. [Prasyarat & Dependencies](#4-prasyarat--dependencies)
5. [Cara Menjalankan Server](#5-cara-menjalankan-server)
6. [Kredensial & Akses Login](#6-kredensial--akses-login)
7. [Panduan Maintenance Per Halaman](#7-panduan-maintenance-per-halaman)
8. [Maintenance Backend (app.py)](#8-maintenance-backend-apppy)
9. [Maintenance Service Layer](#9-maintenance-service-layer)
10. [Maintenance Algoritma ML](#10-maintenance-algoritma-ml)
11. [Maintenance Database (InfluxDB)](#11-maintenance-database-influxdb)
12. [Maintenance MQTT](#12-maintenance-mqtt)
13. [Maintenance Hardware (ESP32)](#13-maintenance-hardware-esp32)
14. [API Endpoints Reference](#14-api-endpoints-reference)
15. [MQTT Topics Reference](#15-mqtt-topics-reference)
16. [Troubleshooting & FAQ](#16-troubleshooting--faq)
17. [Checklist Maintenance Berkala](#17-checklist-maintenance-berkala)
18. [Kontak & Referensi](#18-kontak--referensi)

---

## 1. Gambaran Umum Sistem

Smart Room IoT adalah sistem otomasi ruangan cerdas yang menggunakan:
- **Genetic Algorithm (GA)** untuk optimasi pengaturan AC
- **Particle Swarm Optimization (PSO)** untuk optimasi brightness lampu
- **YOLOv8** untuk deteksi kehadiran orang via kamera
- **Flask + SocketIO** untuk dashboard monitoring real-time
- **MQTT** untuk komunikasi antara Raspberry Pi dan ESP32
- **InfluxDB 2.x** untuk penyimpanan data time-series
- **MySQL (Jagoan Hosting)** untuk data energy meter (PZEM)

### Komponen Utama

| Komponen | Device | Fungsi |
|----------|--------|--------|
| Server Utama | Raspberry Pi 4 | Menjalankan Flask, YOLO, GA/PSO |
| Controller AC | ESP32 #1 | 3x DHT22, IR Blaster, PZEM |
| Controller Lamp | ESP32 #2 | 3x BH1750, 2x LED PWM |
| Kamera | USB Camera di RPi | Deteksi orang (YOLOv8 Nano) |
| MQTT Broker | Cloud (128.199.206.166) | Penghubung komunikasi |
| Database | InfluxDB 2.x (lokal RPi) | Time-series storage |
| Energy DB | MySQL (Jagoan Hosting) | Data daya listrik dari PZEM |

---

## 2. Arsitektur & Alur Data

```
+---------------------------------------------------------------------+
|                      SMART ROOM SYSTEM                              |
+---------------------------------------------------------------------+
|                                                                     |
|  +-------------+    MQTT      +------------------------------+      |
|  |  ESP32 AC   |<----------->|    Raspberry Pi Server        |      |
|  |  3x DHT22   |             |                              |      |
|  |  IR Blaster  |             |  +------------------------+  |      |
|  |  PZEM        |             |  |  dashboard/app.py      |  |      |
|  +-------------+              |  |  (Flask + SocketIO)    |  |      |
|                               |  |  - GA/PSO Engine       |  |      |
|  +-------------+              |  |  - YOLO Detection      |  |      |
|  |  ESP32 Lamp |<----------->|  |  - MQTT Handler        |  |      |
|  |  3x BH1750   |             |  |  - Alert System        |  |      |
|  |  2x LED PWM  |             |  |  - Energy Monitor      |  |      |
|  +-------------+              |  +------------------------+  |      |
|                               |                              |      |
|  +-------------+              |  +------------------------+  |      |
|  |  USB Camera |------------>|  |  InfluxDB 2.x          |  |      |
|  |  (YOLOv8)   |              |  |  Bucket: SENSORDATA   |  |      |
|  +-------------+              |  +------------------------+  |      |
|                               +------------------------------+      |
|                                                                     |
|  +---------------+    +----------------------+                      |
|  |  MQTT Broker  |    |  MySQL (Jagoan)      |                      |
|  |  Cloud Server |    |  api_energy.php      |                      |
|  |  :1883        |    |  Data PZEM meter     |                      |
|  +---------------+    +----------------------+                      |
|                                                                     |
|  +---------------+                                                  |
|  |  SBMS Server  |  (Smart Building Management System)              |
|  |  iotlab-uns   |  Kontrol outlet, AC, Lamp via API                |
|  +---------------+                                                  |
+---------------------------------------------------------------------+
```

### Alur Data:
1. ESP32 membaca sensor -> publish ke MQTT broker
2. Raspberry Pi subscribe ke MQTT -> terima data sensor
3. Data disimpan ke InfluxDB (via `influx_writer.py` dan `app.py`)
4. GA/PSO engine di `app.py` membaca data sensor -> kalkulasi optimasi
5. Hasil optimasi dikirim ke ESP32 via MQTT -> ESP32 kontrol AC/Lamp
6. Dashboard menampilkan data real-time via WebSocket (SocketIO)

---

## 3. Struktur File & Direktori

```
smartroom/
|
|-- main.py                     # Controller optimasi standalone (TIDAK DIPAKAI jika app.py jalan)
|-- genetic_algorithm.py        # GA standalone (legacy, tidak dipakai oleh app.py)
|-- pso.py                      # PSO standalone (legacy, tidak dipakai oleh app.py)
|-- fitness.py                  # Fitness function standalone (legacy)
|-- config.py                   # Konfigurasi global (MQTT, InfluxDB, GA, PSO)
|-- dashboardweb.py             # Launcher dashboard sederhana (legacy)
|
|-- dashboard/                  # *** APLIKASI UTAMA ***
|   |-- app.py                  # Flask app utama (6677 baris) - SEMUA LOGIKA ADA DI SINI
|   |                           # Berisi: routes, GA/PSO engine, MQTT handler,
|   |                           # YOLO detection, energy recording, alerts, dll
|   |-- mysql_energy.py         # Polling data energy dari MySQL Jagoan Hosting
|   |-- ir_codes.json           # Database kode IR remote AC
|   |-- energy_recording.json   # State recording energy (persisted)
|   |-- yolov8n.pt              # Model YOLO Nano untuk deteksi orang
|   |
|   |-- templates/
|   |   |-- base.html           # Template dasar HTML (head, CDN links)
|   |   |-- dashboard.html      # Layout utama (sidebar + semua halaman)
|   |   |-- login.html          # Halaman login
|   |   |-- pages/              # Konten setiap halaman
|   |   |   |-- dashboard_ac.html       # Monitoring AC
|   |   |   |-- dashboard_lamp.html     # Monitoring Lampu
|   |   |   |-- control_ac.html         # Kontrol manual AC + IR Learning
|   |   |   |-- control_lamp.html       # Kontrol manual Lampu
|   |   |   |-- control_outlet.html     # Kontrol outlet (via SBMS)
|   |   |   |-- energy.html             # Energy analytics & comparison
|   |   |   |-- ml_optimization.html    # ML tuning GA/PSO
|   |   |   |-- camera.html             # Camera feed + detection
|   |   |   |-- ac_analytics.html       # Chart historis AC
|   |   |   |-- lamp_analytics.html     # Chart historis Lamp
|   |   |   |-- outlet_analytics.html   # Chart historis Outlet
|   |   |   |-- esp32_ota.html          # OTA firmware update ESP32
|   |   |   |-- occupancy_feedback.html # Form feedback kehadiran
|   |   |   |-- logs.html               # System logs viewer
|   |   |   |-- esp.cpp                 # Firmware ESP32 AC (referensi)
|   |   |   +-- lamp_esp.cpp            # Firmware ESP32 Lamp (referensi)
|   |   +-- partials/
|   |       |-- sidebar.html            # Navigasi sidebar
|   |       |-- modals.html             # Modal dialog
|   |       +-- sensor_health_bar.html  # Status bar sensor
|   |
|   +-- static/
|       |-- css/dashboard.css           # Stylesheet utama (45KB)
|       +-- js/dashboard.js             # JavaScript utama (291KB)
|
|-- services/                   # Service layer (OPSIONAL - app.py sudah all-in-one)
|   |-- mqtt_handler.py         # MQTT client wrapper class
|   |-- influx_writer.py        # MQTT -> InfluxDB bridge (service terpisah)
|   |-- data_collector.py       # CSV data collector
|   |-- camera_services.py      # Camera service wrapper
|   +-- check_org.py            # InfluxDB org checker
|
|-- ml/                         # Modul ML (OPSIONAL - app.py sudah embed)
|   |-- ac_genetic_algorithm.py # GA dengan DEAP framework
|   |-- lamp_pso.py             # PSO dengan pyswarms
|   |-- person_detector.py      # YOLO person detection class
|   +-- test_yolo.py            # Test script YOLO
|
|-- data/                       # Dataset training/historis
|   |-- ac_data.csv             # Riwayat sensor AC
|   +-- lamp_data.csv           # Riwayat sensor Lamp
|
|-- yolov8n.pt                  # Model YOLO Nano (backup)
|-- smartroom.log               # File log aplikasi
+-- report.log                  # File log report
```

### PENTING: File Utama
**Hanya 1 file yang perlu dijalankan: `dashboard/app.py`**

File ini adalah "monolith" yang berisi SEMUA logika:
- Flask web server & routes
- MQTT subscribe/publish
- GA/PSO optimization engine (embedded)
- YOLO camera detection
- InfluxDB read/write
- Energy recording & monitoring
- Alert system & Telegram notifications
- SBMS integration

---

## 4. Prasyarat & Dependencies

### Hardware Requirement
| Item | Spesifikasi |
|------|------------|
| Raspberry Pi | Model 4 (4GB+ RAM), Raspberry Pi OS |
| ESP32 AC | ESP32-WROOM-32 + 3x DHT22 + IR LED + PZEM |
| ESP32 Lamp | ESP32-WROOM-32 + 3x BH1750 + 2x LED PWM |
| Kamera | USB Camera (720p minimum) |
| WiFi | SSID: `IoT`, Password: `agusramelan` |

### Software Requirement
| Software | Versi | Catatan |
|----------|-------|---------|
| Python | 3.13.x (sesuai venv) | Harus Python 3.10+ |
| InfluxDB | 2.x | Harus sudah terinstall di RPi |
| MQTT Broker | Mosquitto (cloud) | Sudah ada di 128.199.206.166 |

### Python Packages
Berikut library Python yang harus terinstall di virtual environment:

```bash
# Web Framework
flask
flask-socketio

# MQTT
paho-mqtt

# Database
influxdb-client

# Computer Vision
ultralytics        # YOLOv8
opencv-python-headless  # atau opencv-python

# Scientific/Math
numpy

# ML Libraries (opsional, hanya jika pakai ml/ folder)
deap               # GA framework
pyswarms           # PSO framework

# HTTP
requests
```

**Install semua sekaligus:**
```bash
pip install flask flask-socketio paho-mqtt influxdb-client ultralytics opencv-python-headless numpy requests
```

---

## 5. Cara Menjalankan Server

### 5.1. Menjalankan di Raspberry Pi (Production)

#### Langkah 1: SSH ke Raspberry Pi
```bash
ssh iotlab@172.20.0.65
# Password: (tanyakan ke admin lab)
```

#### Langkah 2: Aktifkan Virtual Environment
```bash
cd /home/iotlab/smartroom
source venv/bin/activate
```

#### Langkah 3: Pastikan InfluxDB Berjalan
```bash
sudo systemctl status influxdb
# Jika mati:
sudo systemctl start influxdb
```

#### Langkah 4: (Opsional) Jalankan InfluxDB Writer Terpisah
```bash
# Hanya jika ingin logging terpisah dari app.py
python services/influx_writer.py &
```

#### Langkah 5: Jalankan Dashboard (Aplikasi Utama)
```bash
cd dashboard
python app.py
```

**Output yang diharapkan:**
```
Smart Room Dashboard starting...
  [TZ] Timezone OK: Asia/Jakarta
  [OK] Loaded 15 IR codes from file
  [YOLO] Ready
  [OPT] GA auto-opt every 600s, PSO every 300s
  [RESTORE] Loading last optimization results...
  [FAULT] Sensor fault detection thread started
  [WEATHER] Outdoor weather polling started
  [URL] Dashboard: http://172.20.0.65:5000
  [MySQL] Energy polling thread started
  [SBMS] Auto-connecting to SBMS Server...
```

#### Langkah 6: Akses Dashboard
Buka browser dan akses:
```
http://172.20.0.65:5000
```

### 5.2. Menjalankan di Background (Supaya Tetap Jalan Setelah SSH Ditutup)

#### Opsi A: Menggunakan `screen` (Termudah)
```bash
# Buat screen baru
screen -S smartroom

# Jalankan
cd /home/iotlab/smartroom/dashboard
source ../venv/bin/activate
python app.py

# Detach: tekan Ctrl+A lalu D
# Re-attach: screen -r smartroom
```

#### Opsi B: Menggunakan `nohup`
```bash
cd /home/iotlab/smartroom/dashboard
source ../venv/bin/activate
nohup python app.py > ../smartroom.log 2>&1 &
```

#### Opsi C: Menggunakan systemd (Rekomendasi untuk Production)
Buat file service:
```bash
sudo nano /etc/systemd/system/smartroom.service
```

Isi:
```ini
[Unit]
Description=Smart Room IoT Dashboard
After=network.target influxdb.service
Wants=influxdb.service

[Service]
Type=simple
User=iotlab
WorkingDirectory=/home/iotlab/smartroom/dashboard
Environment=PATH=/home/iotlab/smartroom/venv/bin:/usr/bin
ExecStart=/home/iotlab/smartroom/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Aktifkan:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartroom
sudo systemctl start smartroom

# Cek status:
sudo systemctl status smartroom

# Lihat log:
journalctl -u smartroom -f
```

### 5.3. Cara Mematikan Server
```bash
# Jika pakai screen:
screen -r smartroom
# Tekan Ctrl+C

# Jika pakai systemd:
sudo systemctl stop smartroom

# Jika pakai nohup, cari PID:
ps aux | grep app.py
kill <PID>
```

### 5.4. Restart Server (Setelah Ada Perubahan Kode)
```bash
# Matikan dulu
sudo systemctl stop smartroom   # atau Ctrl+C

# Jalankan lagi
sudo systemctl start smartroom  # atau python app.py
```

### 5.5. Set Timezone (WAJIB)
```bash
sudo timedatectl set-timezone Asia/Jakarta
```
**PERINGATAN:** Jika timezone salah, data timestamp di InfluxDB dan grafik dashboard akan kacau!

---

## 6. Kredensial & Akses Login

### Dashboard Login
| Username | Password | Role | Akses |
|----------|----------|------|-------|
| `iotlab` | `iotlab2023` | Admin | Semua halaman |
| `user` | `iotlab2023` | User | Dashboard AC, Lamp, Control saja |

> **Role Admin** bisa mengakses: Analytics, Camera, Energy, ML Optimization, Logs, OTA, SBMS.
> **Role User** hanya bisa mengakses: Dashboard AC/Lamp, Control AC/Lamp/Outlet.

Credential didefinisikan di `app.py` baris 36-39:
```python
USERS = {
    'iotlab': {'password': 'iotlab2023', 'role': 'admin'},
    'user':  {'password': 'iotlab2023',  'role': 'user'},
}
```

### MQTT Broker
| Parameter | Nilai |
|-----------|-------|
| Broker | `128.199.206.166` |
| Port | `1883` |
| Username | `labiot` |
| Password | `iotlabftuns2023` |

### InfluxDB
| Parameter | Nilai |
|-----------|-------|
| URL | `http://localhost:8086` |
| Org | `IOTLAB` |
| Bucket | `SENSORDATA` |
| Token | `rfi_HvWdjwaG8jB3Rqx6g0y5kMWRfSfq_HmLLUvkom1yaHKvwonU9Qfj6nlZjTqb_I0leIREUnMhvQQXtgETfg==` |

### MySQL Energy (Jagoan Hosting)
| Parameter | Nilai |
|-----------|-------|
| PHP URL | `https://iotlab-uns.com/api_energy.php` |
| API Key | `iotlab_smartroom_2024` |
| Polling | Setiap 5 detik |

### SBMS (Smart Building Management System)
| Parameter | Nilai |
|-----------|-------|
| URL | `https://iotlab-uns.com/neo-sbms` |
| Email | `admin@example.com` |
| Password | `123456` |

### Telegram Alert Bot
| Parameter | Nilai |
|-----------|-------|
| Bot Token | `8635310992:AAEXVrdT2r2aWg-8lb7txKIShN04wjzgnkI` |
| Chat ID | `6029706835` |
| Threshold Offline | 10 menit |

### WiFi Lab
| Parameter | Nilai |
|-----------|-------|
| SSID | `IoT` |
| Password | `agusramelan` |

### ESP32 HTTPS Direct
| Parameter | Nilai |
|-----------|-------|
| API Key | `esp32-smartroom-secret` |
| Header | `X-API-Key` |

---

## 7. Panduan Maintenance Per Halaman

Berikut penjelasan detail setiap halaman di dashboard dan apa yang perlu di-maintain.

---

### 7.1. Halaman Login (`login.html`)

**Lokasi file:** `dashboard/templates/login.html`

**Fungsi:**
- Autentikasi user sebelum masuk dashboard
- Mendukung 2 role: `admin` dan `user`

**Maintenance yang perlu dilakukan:**
- **Mengganti password:** Edit variabel `USERS` di `app.py` (baris 36-39)
- **Menambah user baru:** Tambahkan entry di dictionary `USERS`
- **Styling:** Edit langsung CSS inline di `login.html`

**Troubleshoot:**
- Login gagal -> pastikan username/password sesuai `USERS` dict
- Session expired -> server di-restart akan menghapus semua session

---

### 7.2. Dashboard AC (`dashboard_ac.html`)

**Lokasi file:** `dashboard/templates/pages/dashboard_ac.html`

**Fungsi:**
- Menampilkan suhu dan kelembapan real-time dari 3 sensor DHT22
- Status AC (ON/OFF, suhu setting, fan speed)
- Heat Index, trend suhu
- Mode operasi (MANUAL/ADAPTIVE)
- Connection status ESP32 AC

**Data yang ditampilkan:**
| Data | Sumber | MQTT Topic |
|------|--------|-----------|
| Temperature 1-3 | ESP32 AC (DHT22) | `smartroom/ac/sensors` |
| Humidity 1-3 | ESP32 AC (DHT22) | `smartroom/ac/sensors` |
| AC State | ESP32 AC | `smartroom/ac/status` |
| AC Temp Setting | ESP32 AC | `smartroom/ac/status` |
| Fan Speed | ESP32 AC | `smartroom/ac/status` |

**Maintenance:**
- Data tidak muncul -> cek apakah ESP32 AC online (lihat Sensor Health Bar)
- Nilai suhu aneh -> cek koneksi kabel sensor DHT22 di ESP32
- Heat Index salah -> kalkulasi ada di JavaScript (`dashboard.js`)
- Trend suhu -> dihitung dari riwayat suhu 5 menit terakhir

**Yang sering bermasalah:**
- ESP32 AC offline (WiFi putus) -> restart ESP32
- Sensor DHT22 gagal baca -> output NaN -> cek kabel/resistor pull-up

---

### 7.3. Dashboard Lamp (`dashboard_lamp.html`)

**Lokasi file:** `dashboard/templates/pages/dashboard_lamp.html`

**Fungsi:**
- Menampilkan intensitas cahaya (Lux) real-time dari 3 sensor BH1750
- Brightness lampu 1 & 2 (PWM value)
- Motion detection status
- Mode operasi (MANUAL/ADAPTIVE)

**Data yang ditampilkan:**
| Data | Sumber | MQTT Topic |
|------|--------|-----------|
| Lux 1-3 | ESP32 Lamp (BH1750) | `smartroom/lamp/sensors` |
| Brightness 1-2 | ESP32 Lamp (PWM) | `smartroom/lamp/sensors` |
| Motion | ESP32 Lamp (PIR) | `smartroom/lamp/sensors` |

**Maintenance:**
- Lux selalu 0 -> cek sensor BH1750, pastikan I2C address benar
- Brightness tidak berubah -> cek koneksi PWM ke LED driver

---

### 7.4. AC Analytics (`ac_analytics.html`)

**Lokasi file:** `dashboard/templates/pages/ac_analytics.html`

**Fungsi:**
- Grafik historis suhu dan kelembapan
- Pilih rentang waktu (1h, 6h, 12h, 24h, 7d)
- Data dari InfluxDB

**API yang digunakan:**
- `GET /api/chart/ac_sensor/temperature/<hours>`
- `GET /api/chart/ac_sensor/humidity/<hours>`

**Maintenance:**
- Grafik kosong -> cek koneksi InfluxDB, pastikan data masuk
- Data lama hilang -> cek retention policy InfluxDB

---

### 7.5. Lamp Analytics (`lamp_analytics.html`)

**Lokasi file:** `dashboard/templates/pages/lamp_analytics.html`

**Fungsi:** Grafik historis lux dan brightness dari InfluxDB.

**API yang digunakan:**
- `GET /api/chart/lamp_sensor/lux_avg/<hours>`
- `GET /api/chart/lamp_sensor/brightness_avg/<hours>`

---

### 7.6. Camera (`camera.html`)

**Lokasi file:** `dashboard/templates/pages/camera.html`

**Fungsi:**
- Live feed kamera USB via MJPEG stream
- Deteksi orang menggunakan YOLOv8 Nano
- Menampilkan: jumlah orang, status occupied, inference time
- Start/Stop/Restart camera

**API yang digunakan:**
- `GET /video_feed` -- MJPEG stream
- `GET /api/camera/status` -- Status kamera & deteksi
- `POST /api/camera/toggle` -- Start/Stop kamera
- `POST /api/camera/restart` -- Restart kamera

**Maintenance:**
- Camera tidak bisa dibuka -> pastikan USB camera terhubung, cek `ls /dev/video*`
- YOLO gagal load -> cek file `yolov8n.pt` ada di folder `dashboard/`
- Frame rate rendah -> normal di RPi (5-10 FPS), jangan naikkan resolusi
- Deteksi tidak akurat -> tuning confidence threshold di `app.py` (default 0.5)

**Yang sering bermasalah:**
- Camera busy (dipakai proses lain) -> `sudo fuser /dev/video0`
- Memory habis saat YOLO -> restart server, tutup aplikasi lain

---

### 7.7. Energy Usage (`energy.html`)

**Lokasi file:** `dashboard/templates/pages/energy.html`

**Fungsi:**
- Monitoring penggunaan daya listrik real-time (Voltage, Current, Power, kWh)
- Energy recording: Before vs After optimasi
- Perbandingan konsumsi energi sebelum dan sesudah ML
- Export data ke CSV
- Data dari MySQL via PHP proxy (Jagoan Hosting)

**API yang digunakan:**
- `GET /api/data` -- Data energy terkini
- `POST /api/energy/record` -- Start/stop recording
- `GET /api/energy/compare` -- Bandingkan before vs after
- `GET /api/energy/export-csv` -- Export CSV
- `GET /api/energy/daily-summary` -- Ringkasan harian
- `GET /api/energy/history` -- Riwayat penggunaan

**Maintenance:**
- Data energy 0 / tidak muncul -> cek koneksi ke `iotlab-uns.com/api_energy.php`
- Recording tidak persist -> cek file `energy_recording.json`, jangan dihapus
- Lamp energy -> estimasi dari brightness (bukan dari sensor daya langsung)

**Yang sering bermasalah:**
- PHP proxy down -> hubungi admin Jagoan Hosting
- PZEM sensor error -> reset ESP32 AC, cek kabel PZEM

---

### 7.8. Control AC (`control_ac.html`)

**Lokasi file:** `dashboard/templates/pages/control_ac.html`

**Fungsi:**
- Kontrol manual AC: set suhu, fan speed, mode (COOL/DRY/FAN/AUTO)
- Switch mode: MANUAL <-> ADAPTIVE
- IR Learning: merekam kode IR remote AC
- Kirim IR code ke ESP32

**API yang digunakan:**
- `POST /api/ac/control` -- Kirim command ke AC via MQTT/SBMS
- `POST /api/ac/mode` -- Set mode MANUAL/ADAPTIVE
- `POST /api/ir/learn` -- Mulai IR learning
- `POST /api/ir/send` -- Kirim IR code
- `GET /api/ir/codes` -- List IR codes tersimpan
- `GET /api/ir/status` -- Status IR learning

**Mode Operasi:**
- **MANUAL:** User kontrol langsung via dashboard, GA/PSO tidak berlaku
- **ADAPTIVE:** GA menentukan suhu & fan optimal, diterapkan otomatis

**Maintenance:**
- AC tidak merespon -> cek koneksi MQTT ESP32 AC, cek IR LED fisik
- IR Learning gagal -> pastikan ESP32 dalam mode learn, arahkan remote tepat ke receiver
- Mode ADAPTIVE tidak apply -> cek log GA di terminal, ada debounce 10 menit

**IR Codes tersimpan di:** `dashboard/ir_codes.json`

---

### 7.9. Control Lamp (`control_lamp.html`)

**Lokasi file:** `dashboard/templates/pages/control_lamp.html`

**Fungsi:**
- Kontrol manual brightness lampu 1 & 2 (slider 0-100%)
- Switch mode: MANUAL <-> ADAPTIVE
- Toggle ON/OFF

**API yang digunakan:**
- `POST /api/lamp/control` -- Kirim brightness ke ESP32 Lamp
- `POST /api/lamp/mode` -- Set mode MANUAL/ADAPTIVE

**Maintenance:**
- Lampu tidak merespon -> cek koneksi MQTT ESP32 Lamp
- Brightness mentok di 255 -> normal, itu PWM max (8-bit)
- Mode ADAPTIVE -> PSO menentukan brightness optimal setiap 5 menit

---

### 7.10. Control Outlet (`control_outlet.html`)

**Lokasi file:** `dashboard/templates/pages/control_outlet.html`

**Fungsi:**
- Kontrol outlet listrik via SBMS API
- Toggle ON/OFF per device
- Monitoring status device

**API yang digunakan:**
- `GET /api/sbms/devices` -- List device dari SBMS
- `POST /api/sbms/control/<device_id>` -- Toggle device
- `POST /api/sbms/login` -- Login ke SBMS
- `GET /api/outlet/status` -- Status outlet

**Maintenance:**
- Outlet tidak bisa dikontrol -> cek koneksi ke SBMS server
- Login SBMS gagal -> cek kredensial, mungkin berubah
- SBMS auto-connect di startup -> lihat log `[SBMS]`

---

### 7.11. Outlet Analytics (`outlet_analytics.html`)

**Lokasi file:** `dashboard/templates/pages/outlet_analytics.html`

**Fungsi:** Grafik historis penggunaan outlet, export CSV.

**API yang digunakan:**
- `GET /api/outlet/history`
- `GET /api/outlet/energy`
- `GET /api/outlet/export/csv`

---

### 7.12. ML Optimization (`ml_optimization.html`)

**Lokasi file:** `dashboard/templates/pages/ml_optimization.html`

**Fungsi:**
- Monitor GA/PSO fitness score & konvergensi
- Tuning parameter GA: population size, generations, mutation rate, crossover rate
- Tuning parameter PSO: swarm size, iterations, w, c1, c2
- Switching algoritma (GA<->PSO): ga_pso, pso_ga, ga_ga, pso_pso
- Trigger optimasi manual
- Grafik fitness history
- Export hasil optimasi ke CSV

**API yang digunakan:**
- `GET /api/ml/status` -- Status & hasil optimasi terbaru
- `GET /api/ml/algo` -- Konfigurasi algoritma aktif
- `POST /api/ml/algo` -- Ubah konfigurasi algoritma
- `GET /api/ml/params` -- Parameter GA/PSO aktif
- `POST /api/ml/params` -- Ubah parameter GA/PSO
- `POST /api/ml/run` -- Trigger optimasi manual
- `GET /api/ga/export-csv` -- Export hasil GA
- `GET /api/pso/export-csv` -- Export hasil PSO

**Parameter Default GA (untuk AC):**
| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| population_size | 15 | Jumlah individu per generasi |
| generations | 20 | Jumlah generasi evolusi |
| mutation_rate | 0.3 | Probabilitas mutasi (30%) |
| crossover_rate | 0.85 | Probabilitas crossover (85%) |
| elitism_ratio | 0.2 | Top 20% survive |

**Parameter Default PSO (untuk Lamp):**
| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| swarm_size | 10 | Jumlah partikel |
| iterations | 20 | Jumlah iterasi |
| w | 0.5 | Inertia weight (konstan) |
| c1 | 1.5 | Cognitive parameter |
| c2 | 1.5 | Social parameter |

**Interval Auto-Optimization:**
- GA (AC): Setiap 600 detik (10 menit)
- PSO (Lamp): Setiap 300 detik (5 menit)

**Maintenance:**
- Fitness score tidak naik -> cek sensor data, mungkin stale
- GA stuck -> naikkan mutation_rate, atau kurangi stagnation_limit
- PSO tidak konvergen -> tuning w, c1, c2
- Switching algoritma -> pilih di dashboard, otomatis langsung run

---

### 7.13. System Logs (`logs.html`)

**Lokasi file:** `dashboard/templates/pages/logs.html`

**Fungsi:** Menampilkan log sistem real-time dari backend.

**API yang digunakan:**
- `GET /api/logs` -- Ambil log terbaru

**Maintenance:**
- Log terlalu banyak -> `log_messages` pakai `deque(maxlen=100)`
- File log besar -> cek `smartroom.log`, bisa di-rotate manual

---

### 7.14. Occupancy & Feedback (`occupancy_feedback.html`)

**Lokasi file:** `dashboard/templates/pages/occupancy_feedback.html`

**Fungsi:**
- Form feedback untuk koreksi deteksi kehadiran YOLO
- Data dikirim ke Google Form

**API yang digunakan:**
- `POST /api/occupancy/feedback`
- `GET /api/occupancy/feedback/list`

---

### 7.15. ESP32 OTA Update (`esp32_ota.html`)

**Lokasi file:** `dashboard/templates/pages/esp32_ota.html`

**Fungsi:**
- Over-the-Air firmware update untuk ESP32
- Input IP ESP32 -> upload `.bin` file -> flash firmware

**API yang digunakan:**
- `GET /api/esp32-ota/status?ip=<ESP32_IP>` -- Cek status ESP32
- `POST /api/esp32-ota/upload` -- Upload firmware
- `GET /api/esp32-ota/known-ip` -- Get known IP

**Maintenance:**
- OTA gagal -> pastikan ESP32 dalam 1 jaringan, cek IP
- File firmware harus `.bin` (compile dari Arduino IDE / PlatformIO)
- Firmware ESP32 AC: `esp.cpp` | ESP32 Lamp: `lamp_esp.cpp`

---

### 7.16. Sensor Health Bar (`sensor_health_bar.html`)

**Lokasi file:** `dashboard/templates/partials/sensor_health_bar.html`

**Fungsi:**
- Bar status di atas setiap halaman
- Menampilkan status: OK (hijau), Warning (kuning), Fault (merah)
- Per-device: ESP32 AC, ESP32 Lamp, Camera

**API yang digunakan:**
- `GET /api/sensor/health`
- `GET /api/device/status`

**Threshold:**
| Status | Kondisi |
|--------|---------|
| OK | Data fresh < 60 detik |
| Warning | Data stale 60-300 detik |
| Fault | Data stale > 300 detik |

---

### 7.17. Sidebar Navigation (`sidebar.html`)

**Lokasi file:** `dashboard/templates/partials/sidebar.html`

**Fungsi:** Menu navigasi kiri dengan role-based access.

**Maintenance -- Menambah halaman baru:**
1. Buat file di `templates/pages/nama_baru.html`
2. Tambahkan `{% include %}` di `dashboard.html`
3. Tambahkan nav-item di `sidebar.html`
4. Tambahkan handler `showPage('nama-baru')` di `dashboard.js`
5. Jika admin-only, tambahkan class `admin-only`

---

## 8. Maintenance Backend (app.py)

### 8.1. Struktur Kode app.py

File `app.py` (6677 baris) terbagi menjadi beberapa section:

| Baris | Section | Deskripsi |
|-------|---------|-----------|
| 1-100 | Imports & Config | Library, SBMS config, credentials |
| 100-220 | Energy Recording | Persist/restore energy state |
| 220-600 | GA/PSO Engine | Fitness function, optimization bounds |
| 600-1100 | GA/PSO Runners | `run_ga_optimization()`, `run_pso_optimization()` |
| 1100-1700 | MQTT Handlers | Subscribe, on_message, sensor processing |
| 1700-2500 | InfluxDB Functions | Read/write time-series data |
| 2500-3000 | YOLO Camera | Detection loop, video feed |
| 3000-3600 | Background Threads | Auto-opt, fault detection, weather |
| 3600-3700 | Auth Routes | Login, logout, role check |
| 3700-6500 | API Routes | Semua REST API endpoints |
| 6500-6677 | Startup & Main | Init sequence, thread spawning |

### 8.2. Menambah Route API Baru

```python
@app.route('/api/nama_baru', methods=['GET'])
def nama_baru():
    try:
        # Logic
        return jsonify({'status': 'success', 'data': ...})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

### 8.3. Mengedit Fitness Function

**Fitness GA (AC):** `calculate_ac_fitness()` (baris ~400-600)
- Komponen: Comfort Score (40pt), Humidity Response (15pt), Fan Appropriateness (15pt), Energy Efficiency (20pt), Uniformity Bonus (8pt), Trend Compensation (7pt), Mode bonus (10pt), Crowd bonus (12pt), Set RH (10pt), Weather (12pt)
- Total max: ~149 point -> dinormalisasi ke 0-100%
- Crowd tier: 0 person (hemat), 1-2 (normal), 3-5 (medium cool), >5 (max cool)

**Fitness PSO (Lamp):** `calculate_lamp_fitness()` (cari di app.py)
- Komponen: Lighting Comfort, Energy Efficiency, Ambient Adaptation
- Target lux: 350 lux (ada orang), 0 (kosong)

### 8.4. Background Threads

Saat startup, beberapa thread berjalan otomatis:

| Thread | Fungsi | Interval |
|--------|--------|----------|
| `camera_detection_loop` | YOLO detection | 5 detik |
| `optimization_auto_loop` | GA/PSO auto-run | AC: 600s, Lamp: 300s |
| `sensor_fault_loop` | Cek sensor health + Telegram | Berkala |
| `weather_poll_loop` | Fetch cuaca Open-Meteo | Berkala |
| `mysql_energy.start_polling` | Fetch data PZEM | 5 detik |
| `auto_connect_sbms` | Login SBMS otomatis | Sekali saat startup |

---

## 9. Maintenance Service Layer

### 9.1. InfluxDB Writer (`services/influx_writer.py`)

**Fungsi:** Bridge MQTT -> InfluxDB (service standalone opsional)

**Kapan dijalankan:** Hanya jika ingin logging terpisah dari `app.py`. `app.py` sudah punya InfluxDB writer sendiri.

```bash
python services/influx_writer.py
```

**Konfigurasi:** Edit langsung di file (baris 12-19):
```python
INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "rfi_HvWdjwa..."
INFLUX_ORG    = "IOTLAB"
INFLUX_BUCKET = "SENSORDATA"
```

**Measurement yang ditulis:**
| Measurement | Sumber | Fields |
|-------------|--------|--------|
| `ac_sensor` | `smartroom/ac/sensors` | temperature, humidity, heat_index, ac_temp, fan_speed |
| `lamp_sensor` | `smartroom/lamp/sensors` | lux1, lux2, lux3, lux_avg, brightness1, brightness2, motion |
| `camera` | `smartroom/camera/detection` | person_count, occupied |
| `ac_optimization` | `smartroom/ac/optimization` | recommended_temp, fan_speed, energy/comfort_score |
| `lamp_optimization` | `smartroom/lamp/optimization` | brightness, target_lux, efficiency |

### 9.2. MQTT Handler (`services/mqtt_handler.py`)

**Fungsi:** MQTT client wrapper class (dipakai oleh `ml/person_detector.py`)
- Subscribe wildcard `smartroom/#`
- Pattern-based callback routing
- Auto-reconnect on disconnect
- LWT (Last Will & Testament) untuk server status

### 9.3. Data Collector (`services/data_collector.py`)

**Fungsi:** Simpan data sensor ke CSV setiap 5 menit
- `data/ac_data.csv` -- sensor AC
- `data/lamp_data.csv` -- sensor Lamp

### 9.4. MySQL Energy (`dashboard/mysql_energy.py`)

**Fungsi:** Polling data PZEM energy meter dari MySQL via PHP proxy

**Arsitektur:**
```
ESP32 (PZEM) -> Cloud MySQL (Jagoan) <- PHP API <- RPi (HTTP GET)
```

**Data yang diambil (setiap 5 detik):**
- AC (id_kwh=1): Voltage, Current, Active Power, Frequency, Total Energy
- Outlet (id_kwh=2): Voltage, Current, Active Power, Frequency, Total Energy
- Lamp (id_kwh=3): Voltage, Current, Active Power, Frequency, Total Energy

---

## 10. Maintenance Algoritma ML

### 10.1. Genetic Algorithm (AC)

**Lokasi:** Embedded di `dashboard/app.py` -> `run_ga_optimization()` (baris ~907)

**Kromosom 4D:**
```
[Temp_Set (16-30 C), Fan_Speed (1-4), Mode (0-3), Set_RH (30-80%)]
```

**Operator Genetik:**
- Selection: Tournament (size=3)
- Crossover: BLX-alpha (alpha=0.3)
- Mutation: Adaptive Gaussian (rate menurun seiring generasi)
- Elitism: Top 20%
- Stagnation: Diversity injection jika stuck

**Tuning Tips:**
| Problem | Solusi |
|---------|--------|
| Konvergensi terlalu cepat (lokal optimum) | Naikkan mutation_rate (0.4+), kurangi elitism |
| Tidak konvergen | Naikkan generations (30+), populasi (20+) |
| Hasil tidak konsisten | Tambah seed dari siklus sebelumnya |
| Fitness selalu rendah | Cek data sensor, mungkin stale/default |

### 10.2. Particle Swarm Optimization (Lamp)

**Lokasi:** Embedded di `dashboard/app.py` -> `run_pso_optimization()` (cari di app.py)

**Partikel 2D:**
```
[PWM1 (0-255), PWM2 (0-255)]
```

**Real-Time Feedback Loop:**
PSO pada lampu menggunakan sensor lux nyata (bukan simulasi):
1. Kirim PWM -> MQTT -> ESP32 -> lampu berubah
2. Tunggu 5 detik (stabilisasi)
3. Baca lux dari sensor BH1750
4. Evaluasi fitness
5. Update velocity & position

**Tuning Tips:**
| Problem | Solusi |
|---------|--------|
| Lux tidak mencapai target | Cek apakah lampu cukup terang (cek watt lampu) |
| Oscillasi terus | Kurangi c1/c2 (1.0), naikkan w (0.7) |
| Terlalu lambat konvergen | Naikkan swarm_size, kurangi iterations |

### 10.3. Switching Algoritma

Dashboard mendukung 4 kombinasi:

| Config | AC | Lamp |
|--------|------|------|
| `ga_pso` (default) | GA | PSO |
| `pso_ga` | PSO | GA |
| `ga_ga` | GA | GA |
| `pso_pso` | PSO | PSO |

Cara ganti: Dashboard -> ML Optimization -> Select Algorithm Configuration

---

## 11. Maintenance Database (InfluxDB)

### 11.1. Cek InfluxDB
```bash
# Status service
sudo systemctl status influxdb

# Restart
sudo systemctl restart influxdb

# UI admin
# Buka browser: http://localhost:8086
# Login dengan token
```

### 11.2. Query Data Manual
```bash
# Masuk ke InfluxDB CLI
influx query 'from(bucket: "SENSORDATA") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "ac_sensor") |> last()'
```

### 11.3. Backup InfluxDB
```bash
influx backup /home/iotlab/influx_backup/
```

### 11.4. Retention Policy
Pastikan retention policy sesuai kebutuhan. Default biasanya infinite. Jika disk penuh:
```bash
# Lihat bucket
influx bucket list

# Set retention 30 hari
influx bucket update --id <BUCKET_ID> --retention 720h
```

### 11.5. Measurement yang Disimpan

| Measurement | Fields | Tags |
|-------------|--------|------|
| `ac_sensor` | temperature, humidity, heat_index, ac_temp, fan_speed | source: esp32_ac |
| `lamp_sensor` | lux1, lux2, lux3, lux_avg, brightness1, brightness2, motion | source: esp32_lamp |
| `camera` | person_count, occupied | source: raspi_camera |
| `energy_monitor` | voltage, current, power, energy_kwh, frequency, power_factor | device, source |
| `ac_optimization` | recommended_temp, fan_speed, fitness, fitness_pct | algorithm |
| `lamp_optimization` | pwm1, pwm2, fitness, target_lux | algorithm |

---

## 12. Maintenance MQTT

### 12.1. Test Koneksi MQTT
```bash
# Subscribe (lihat semua pesan)
mosquitto_sub -h 128.199.206.166 -p 1883 -u labiot -P iotlabftuns2023 -t "smartroom/#" -v

# Publish test
mosquitto_pub -h 128.199.206.166 -p 1883 -u labiot -P iotlabftuns2023 -t "smartroom/test" -m '{"hello":"world"}'
```

### 12.2. Debug MQTT dari Dashboard
Di dashboard: API -> `POST /api/mqtt/selftest` -> kirim pesan test dan subscribe

### 12.3. Reconnect MQTT
Jika MQTT terputus:
- Dashboard API: `POST /api/mqtt/reconnect`
- Atau restart server: `sudo systemctl restart smartroom`

---

## 13. Maintenance Hardware (ESP32)

### 13.1. ESP32 AC

**Firmware:** `dashboard/templates/pages/esp.cpp`

**Sensor & Pin:**
- 3x DHT22 (suhu & kelembapan)
- 1x IR LED (kontrol remote AC)
- 1x IR Receiver (learning remote)
- 1x PZEM-004T (energy meter)

**Troubleshoot:**
| Masalah | Solusi |
|---------|--------|
| Tidak connect WiFi | Cek SSID/password di firmware, restart ESP32 |
| Sensor NaN | Cek kabel, pastikan pin benar, cek pull-up resistor |
| IR tidak berfungsi | Cek LED IR, jarak ke AC, arah |
| PZEM tidak baca | Cek koneksi serial, cek CT clamp |
| Offline terus | Cek power supply, reset button, re-flash firmware |

**Cara Flash Firmware:**
1. Buka Arduino IDE / PlatformIO
2. Load `esp.cpp`
3. Set Board: ESP32 WROOM
4. Set Port: USB yang terhubung
5. Upload
6. Atau via OTA dari dashboard: ESP32 OTA -> masukkan IP ESP32 -> upload .bin

### 13.2. ESP32 Lamp

**Firmware:** `dashboard/templates/pages/lamp_esp.cpp`

**Sensor & Pin:**
- 3x BH1750 (sensor lux via I2C)
- 2x LED PWM output
- 1x PIR Motion Sensor

**Troubleshoot:**
| Masalah | Solusi |
|---------|--------|
| Lux selalu 0 | Cek I2C address (0x23, 0x5C, 0x46), cek kabel SDA/SCL |
| LED tidak menyala | Cek MOSFET/transistor driver, cek PWM pin |
| Motion false positive | Tuning sensitivity PIR, atau abaikan noise |

---

## 14. API Endpoints Reference

### Authentication
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET/POST | `/login` | Halaman login |
| GET | `/logout` | Logout |
| GET | `/api/auth/role` | Get current user role |

### Dashboard & Data
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/` | Dashboard utama |
| GET | `/api/data` | Data keseluruhan sistem |
| GET | `/api/system/tz-status` | Status timezone |
| GET | `/api/outdoor-weather` | Data cuaca outdoor |
| GET | `/api/device/status` | Status semua device |
| GET | `/api/sensor/health` | Health check sensor |
| GET | `/api/alerts` | Active alerts |
| POST | `/api/alerts/config` | Konfigurasi alert |

### Camera
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/video_feed` | MJPEG video stream |
| GET | `/api/camera/status` | Status kamera & deteksi |
| POST | `/api/camera/toggle` | Start/Stop kamera |
| POST | `/api/camera/restart` | Restart kamera |

### MQTT
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/mqtt/status` | Status koneksi MQTT |
| POST | `/api/mqtt/reconnect` | Reconnect MQTT |
| POST | `/api/mqtt/config` | Update konfigurasi MQTT |
| POST | `/api/mqtt/selftest` | Self-test MQTT |

### Kontrol AC
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/ac/control` | Kirim command AC |
| POST | `/api/ac/mode` | Set MANUAL/ADAPTIVE |

### Kontrol Lamp
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/lamp/control` | Kirim brightness |
| POST | `/api/lamp/mode` | Set MANUAL/ADAPTIVE |

### Kontrol Outlet (SBMS)
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/sbms/devices` | List SBMS devices |
| POST | `/api/sbms/control/<id>` | Toggle device |
| POST | `/api/sbms/login` | Login SBMS |
| POST | `/api/sbms/logout` | Logout SBMS |
| GET/POST | `/api/sbms/config` | SBMS config |
| GET | `/api/outlet/status` | Status outlet |
| GET | `/api/outlet/history` | History outlet |
| GET | `/api/outlet/energy` | Energy outlet |

### ML Optimization
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/ml/status` | Status & hasil optimasi |
| GET/POST | `/api/ml/algo` | Get/Set konfigurasi algoritma |
| GET/POST | `/api/ml/params` | Get/Set parameter GA/PSO |
| POST | `/api/ml/run` | Trigger optimasi manual |
| POST | `/api/optimization/update` | Update hasil (dari main.py) |

### Energy
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET/POST | `/api/energy/phase` | Get/Set phase energy |
| GET/POST | `/api/energy/record` | Get/Set recording state |
| GET | `/api/energy/compare` | Before vs After comparison |
| GET | `/api/energy/export-csv` | Export energy CSV |
| GET | `/api/energy/daily-summary` | Ringkasan harian |
| GET | `/api/energy/history` | Riwayat lengkap |
| GET/POST | `/api/lamp/energy/record` | Lamp energy recording |
| GET | `/api/lamp/energy/compare` | Lamp energy comparison |
| GET/POST | `/api/rec/state` | Recording state |
| GET/POST/DELETE | `/api/rec/data` | Recording data |

### Charts & Export
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/chart/<measurement>/<field>/<hours>` | Data grafik |
| GET | `/api/chart/ac_power/<hours>` | Data daya AC |
| GET | `/api/chart/lamp_power/<hours>` | Data daya Lamp |
| GET | `/api/export/csv` | Export data CSV |
| GET | `/api/ga/export-csv` | Export GA results CSV |
| GET | `/api/pso/export-csv` | Export PSO results CSV |
| GET | `/api/outlet/export/csv` | Export outlet CSV |

### IR Remote
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/ir/learn` | Mulai IR learning |
| POST | `/api/ir/send` | Kirim IR code |
| GET | `/api/ir/codes` | List IR codes |
| POST | `/api/ir/delete` | Hapus IR code |
| GET | `/api/ir/status` | Status IR learning |
| POST | `/api/ir/manual_save` | Manual save IR code |

### ESP32
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/esp32/data` | Terima data dari ESP32 (HTTPS) |
| GET | `/api/esp32-ota/status` | Cek status ESP32 |
| POST | `/api/esp32-ota/upload` | Upload firmware OTA |
| GET | `/api/esp32-ota/known-ip` | Get known ESP32 IP |

### Miscellaneous
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/logs` | System logs |
| POST | `/api/simulate` | Simulasi sensor data |
| POST | `/api/occupancy/feedback` | Submit feedback |
| GET | `/api/occupancy/feedback/list` | List feedback |

---

## 15. MQTT Topics Reference

| Topic | Publisher | Subscriber | Deskripsi |
|-------|----------|-----------|-----------|
| `smartroom/ac/sensors` | ESP32 AC | RPi | Data suhu, kelembapan (3x DHT22) |
| `smartroom/ac/control` | RPi | ESP32 AC | Perintah kontrol AC (suhu, fan, mode) |
| `smartroom/ac/status` | ESP32 AC | RPi | Status AC saat ini |
| `smartroom/ac/mode` | RPi | ESP32 AC | Mode operasi (MANUAL/ADAPTIVE) |
| `smartroom/ac/connection` | ESP32 AC | RPi | Status online/offline |
| `smartroom/ac/ping` | RPi | ESP32 AC | Heartbeat ping |
| `smartroom/lamp/sensors` | ESP32 Lamp | RPi | Data lux (3x BH1750) + brightness |
| `smartroom/lamp/control` | RPi | ESP32 Lamp | Perintah brightness (PWM1, PWM2) |
| `smartroom/lamp/status` | ESP32 Lamp | RPi | Status lampu |
| `smartroom/camera/detection` | RPi | Dashboard | Hasil deteksi orang |
| `smartroom/camera/status` | RPi | ESP32 | Status kamera |
| `smartroom/ml/result` | RPi | Dashboard | Hasil optimasi GA + PSO |
| `smartroom/ml/status` | RPi | Dashboard | Status proses optimasi |
| `smartroom/ml/command` | Dashboard | RPi | Perintah optimasi |
| `smartroom/ir/learned` | ESP32 AC | RPi | Hasil IR capture |
| `smartroom/ir/learn` | RPi | ESP32 AC | Perintah belajar IR |
| `smartroom/ir/send` | RPi | ESP32 AC | Kirim IR code |
| `smartroom/ac/ir_learn_status` | ESP32 AC | RPi | Status IR learning |
| `smartroom/dashboard/state` | RPi | All | State dashboard |
| `smartroom/server/status` | RPi | All | Server online/offline |
| `smartroom/#` | All | RPi | Wildcard subscribe |

---

## 16. Troubleshooting & FAQ

### 16.1. Server / Dashboard

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| Dashboard tidak bisa diakses | Server mati | `python app.py` atau `sudo systemctl start smartroom` |
| Error `Address already in use` | Port 5000 dipakai | `sudo lsof -i :5000`, kill PID, jalankan ulang |
| Error `No module named 'flask'` | Virtual env tidak aktif | `source venv/bin/activate` |
| Dashboard sangat lambat | YOLO makan RAM | Restart server, tutup app lain |
| Session expired | Server restart | Normal -- user perlu login ulang |
| Blank page setelah login | JS error | Buka browser console (F12), cek error |

### 16.2. Data & Sensor

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| Semua data 0 | ESP32 offline | Cek WiFi ESP32, restart |
| Sensor health bar merah | Data stale > 5 menit | Cek MQTT broker, cek ESP32 |
| Suhu NaN | DHT22 error | Cek kabel, cek pull-up resistor |
| Lux selalu 0 | BH1750 tidak terdeteksi | Cek I2C, jalankan `i2cdetect -y 1` |
| Grafik historis kosong | InfluxDB tidak jalan | `sudo systemctl start influxdb` |
| Data timestamp salah | Timezone salah | `sudo timedatectl set-timezone Asia/Jakarta` |

### 16.3. Optimasi ML

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| GA fitness selalu 0 | Sensor data default | Pastikan ESP32 kirim data, cek `opt_sensor_data` |
| PSO tidak konvergen | Parameter kurang optimal | Tuning w, c1, c2 di dashboard ML |
| Mode ADAPTIVE tidak apply | Debounce timer aktif | Tunggu 10 menit (AC) / 5 menit (Lamp) |
| Optimasi tidak jalan | Thread error | Restart server, cek log |
| Fitness turun setelah ganti algo | Normal | Algoritma beda -> fitness beda, bukan berarti buruk |

### 16.4. MQTT

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| MQTT disconnected | Broker down atau network | `POST /api/mqtt/reconnect` atau restart |
| Pesan tidak sampai | Topic salah | Cek topic di `config.py`, gunakan `mosquitto_sub` debug |
| Duplicate message | QoS/retain issue | Pastikan QoS=0 untuk sensor data |

### 16.5. Hardware

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| ESP32 tidak connect WiFi | SSID/password salah | Cek firmware, re-flash |
| ESP32 reset terus | Power supply lemah | Gunakan adaptor 5V 2A dedicated |
| Camera blank | USB lepas | Pasang ulang USB, cek `ls /dev/video*` |
| AC tidak merespon IR | IR LED rusak/lemah | Ganti LED, periksa jarak/arah |
| Lampu tidak menyala | MOSFET/driver error | Cek rangkaian driver PWM |

---

## 17. Checklist Maintenance Berkala

### Harian
- [ ] Cek dashboard bisa diakses (`http://172.20.0.65:5000`)
- [ ] Cek Sensor Health Bar: semua hijau (OK)
- [ ] Cek data suhu/lux masuk dan wajar
- [ ] Cek mode ADAPTIVE aktif (jika dibutuhkan)

### Mingguan
- [ ] Review log sistem (`smartroom.log`)
- [ ] Cek disk space Raspberry Pi: `df -h`
- [ ] Cek koneksi MQTT stabil: `GET /api/mqtt/status`
- [ ] Cek InfluxDB storage: `du -sh /var/lib/influxdb2/`
- [ ] Test semua halaman dashboard berfungsi
- [ ] Cek Telegram bot masih mengirim alert

### Bulanan
- [ ] Backup InfluxDB: `influx backup /home/iotlab/influx_backup/`
- [ ] Backup folder `smartroom/` ke external storage
- [ ] Update RPi OS security patches: `sudo apt update && sudo apt upgrade`
- [ ] Review dan rotate log files (jika > 100MB)
- [ ] Test OTA update ESP32 (dengan firmware test)
- [ ] Cek sensor fisik (debu, kabel longgar)
- [ ] Kalibrasi sensor suhu (bandingkan dengan termometer manual)

### Per Semester
- [ ] Review parameter GA/PSO -- apakah masih optimal?
- [ ] Export data CSV untuk laporan penelitian
- [ ] Update firmware ESP32 jika ada perbaikan
- [ ] Cek MQTT broker cloud -- masih aktif?
- [ ] Review kredensial -- ganti password jika perlu
- [ ] Dokumentasi perubahan yang dilakukan selama semester

### Saat Handover ke Asisten Lab Baru
- [ ] Briefing arsitektur sistem (gunakan dokumen ini)
- [ ] Demo menjalankan server & troubleshoot dasar
- [ ] Share akses SSH Raspberry Pi
- [ ] Share akses InfluxDB admin
- [ ] Share akses MQTT broker
- [ ] Share akses Jagoan Hosting (jika perlu ubah PHP)
- [ ] Pastikan asisten baru bisa login ke dashboard
- [ ] Pastikan asisten baru bisa restart server
- [ ] Update kontak di bagian Kontak & Referensi

---

## 18. Kontak & Referensi

### Kontak
| Peran | Nama | Kontak |
|-------|------|--------|
| Pengembang Awal | (isi nama) | (isi kontak) |
| Admin Lab IoT | (isi nama) | (isi kontak) |
| Admin Server (Jagoan) | (isi nama) | (isi kontak) |

### Referensi
| Resource | Link |
|----------|------|
| Dashboard | `http://172.20.0.65:5000` |
| InfluxDB Admin | `http://localhost:8086` |
| MQTT Broker | `128.199.206.166:1883` |
| SBMS Server | `https://iotlab-uns.com/neo-sbms` |
| PHP Energy API | `https://iotlab-uns.com/api_energy.php` |
| Telegram Bot | `@BotFather` -- token di `config.py` |

### File Penting Yang Tidak Boleh Dihapus
| File | Fungsi |
|------|--------|
| `dashboard/app.py` | Aplikasi utama |
| `dashboard/ir_codes.json` | Database IR remote |
| `dashboard/energy_recording.json` | State recording energy |
| `dashboard/yolov8n.pt` | Model YOLO |
| `dashboard/static/css/dashboard.css` | Stylesheet |
| `dashboard/static/js/dashboard.js` | JavaScript utama |
| `data/ac_data.csv` | Data historis AC |
| `data/lamp_data.csv` | Data historis Lamp |

### Dokumentasi Tambahan
| Dokumen | Lokasi |
|---------|--------|
| README umum | `README.md` |
| Dokumentasi Algoritma | `DOKUMENTASI_ALGORITMA.md` |
| **Dokumentasi Maintenance** | **`DOKUMENTASI_MAINTENANCE.md` (file ini)** |

---

> **Catatan:** Dokumen ini dibuat pada Agustus 2026. Update dokumen ini setiap kali ada perubahan signifikan pada sistem. Selamat memelihara Smart Room IoT!
