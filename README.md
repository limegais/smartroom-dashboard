# 🏠 Smart Room IoT — AI-Powered Room Automation System

> Sistem otomasi ruangan pintar berbasis IoT dengan optimasi AI menggunakan **Genetic Algorithm (GA)** untuk kontrol AC dan **Particle Swarm Optimization (PSO)** untuk kontrol lampu, dilengkapi deteksi kehadiran berbasis **YOLOv8** dan dashboard monitoring real-time.

---

## 📋 Daftar Isi

- [Gambaran Umum](#-gambaran-umum)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Fitur Utama](#-fitur-utama)
- [Teknologi](#-teknologi)
- [Struktur Proyek](#-struktur-proyek)
- [Prasyarat](#-prasyarat)
- [Instalasi](#-instalasi)
- [Konfigurasi](#-konfigurasi)
- [Menjalankan Sistem](#-menjalankan-sistem)
- [Dashboard Web](#-dashboard-web)
- [Algoritma Optimasi](#-algoritma-optimasi)
- [MQTT Topics](#-mqtt-topics)
- [API Endpoints](#-api-endpoints)
- [Kontributor](#-kontributor)

---

## 🔍 Gambaran Umum

**Smart Room IoT** adalah sistem otomasi ruangan cerdas yang mengintegrasikan sensor lingkungan (suhu, kelembapan, cahaya), kamera deteksi kehadiran, dan algoritma optimasi AI untuk mengontrol perangkat ruangan (AC dan lampu) secara otomatis dan efisien.

Sistem ini dirancang untuk berjalan pada **Raspberry Pi** sebagai server utama, berkomunikasi dengan **ESP32** melalui protokol **MQTT**, dan menyimpan data historis di **InfluxDB**.

### Alur Kerja Utama

```
ESP32 Sensors → MQTT Broker → Raspberry Pi (Python) → AI Optimization → Device Control
                                    ↓
                              InfluxDB (Storage)
                                    ↓
                           Flask Dashboard (Monitoring)
```

---

## 🏗 Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                        SMART ROOM SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    MQTT     ┌──────────────────────────────┐  │
│  │   ESP32 AC   │◄──────────►│       Raspberry Pi Server     │  │
│  │  3×DHT22     │            │                              │  │
│  │  IR Blaster  │            │  ┌────────────────────────┐  │  │
│  └──────────────┘            │  │   main.py (Controller)  │  │  │
│                              │  │  ┌──────┐  ┌────────┐  │  │  │
│  ┌──────────────┐            │  │  │  GA  │  │  PSO   │  │  │  │
│  │  ESP32 Lamp  │◄──────────►│  │  │ (AC) │  │ (Lamp) │  │  │  │
│  │  3×BH1750    │            │  │  └──────┘  └────────┘  │  │  │
│  │  2×LED PWM   │            │  └────────────────────────┘  │  │
│  └──────────────┘            │                              │  │
│                              │  ┌────────────────────────┐  │  │
│  ┌──────────────┐            │  │  dashboard/app.py      │  │  │
│  │   USB Camera │───────────►│  │  Flask + SocketIO      │  │  │
│  │   (YOLOv8)   │            │  │  Real-time Dashboard   │  │  │
│  └──────────────┘            │  └────────────────────────┘  │  │
│                              │                              │  │
│                              │  ┌────────────────────────┐  │  │
│                              │  │  InfluxDB 2.x          │  │  │
│                              │  │  Time-series Storage   │  │  │
│                              │  └────────────────────────┘  │  │
│                              └──────────────────────────────┘  │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ MQTT Broker  │  (Cloud: 128.199.206.166:1883)                │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Fitur Utama

### 🤖 Optimasi AI
- **Genetic Algorithm (GA)** — Optimasi setting AC (suhu 16–30°C, fan speed 1–3)
  - Continuous encoding, BLX-α crossover, adaptive mutation
  - Seeding dari siklus sebelumnya, 20% elitism
  - Brute-force validation untuk verifikasi solusi optimal
  - Time-of-day awareness (pagi/siang/sore/malam)
  - Dukungan 3 sensor suhu untuk uniformity analysis
- **Particle Swarm Optimization (PSO)** — Optimasi brightness lampu (0–100%)
  - Adaptive inertia weight
  - Ambient light adaptation
  - Energy-efficient optimization

### 📡 IoT & Sensor
- 3× DHT22 sensor suhu & kelembapan (multi-zone)
- 3× BH1750 sensor cahaya (multi-point)
- IR blaster untuk kontrol AC
- PWM LED dimmer untuk kontrol lampu
- MQTT protocol untuk komunikasi real-time

### 📹 Computer Vision
- Deteksi kehadiran orang menggunakan **YOLOv8 Nano**
- Smoothed occupancy detection (rolling average)
- Statistik deteksi (inference time, detection rate)

### 📊 Dashboard Web
- Real-time monitoring via Flask + SocketIO
- Halaman kontrol AC, Lampu, dan Outlet
- Visualisasi analytics & energy monitoring
- Halaman ML Optimization dengan parameter tuning
- OTA update untuk ESP32
- Sistem autentikasi (admin/user roles)
- Integrasi dengan SBMS (Smart Building Management System)
- Telegram alert notifications

### 💾 Data Storage
- **InfluxDB 2.x** untuk time-series data
- CSV backup untuk data historis
- Logging ke file (`smartroom.log`)

---

## 🛠 Teknologi

| Komponen | Teknologi |
|---|---|
| Server | Raspberry Pi (Python 3.13) |
| Microcontroller | ESP32 (C++ / Arduino) |
| AI - AC | Genetic Algorithm (custom) |
| AI - Lamp | Particle Swarm Optimization (custom) |
| AI - Detection | YOLOv8 Nano (ultralytics) |
| Komunikasi | MQTT (paho-mqtt) |
| Database | InfluxDB 2.x |
| Dashboard | Flask + SocketIO |
| Frontend | HTML, CSS, JavaScript |

---

## 📁 Struktur Proyek

```
smartroom/
│
├── main.py                    # Controller utama (Auto Mode: GA + PSO loop)
├── genetic_algorithm.py       # Enhanced GA untuk optimasi AC
├── pso.py                     # PSO untuk optimasi Lamp
├── fitness.py                 # Fungsi fitness (AC + Lamp) + InfluxDB fetch
├── config.py                  # Konfigurasi global (MQTT, InfluxDB, GA, PSO)
├── dashboardweb.py            # Launcher dashboard web sederhana
│
├── ml/                        # Modul Machine Learning
│   ├── ac_genetic_algorithm.py    # GA dengan DEAP (multi-objective)
│   ├── lamp_pso.py                # PSO dengan pyswarms
│   ├── person_detector.py         # YOLOv8 person detection
│   └── test_yolo.py               # Test script YOLO
│
├── services/                  # Service layer
│   ├── mqtt_handler.py            # MQTT client wrapper
│   ├── influx_writer.py           # MQTT → InfluxDB bridge
│   ├── data_collector.py          # Sensor data CSV collector
│   ├── camera_services.py         # Camera service wrapper
│   └── check_org.py               # InfluxDB org checker
│
├── dashboard/                 # Flask dashboard application
│   ├── app.py                     # Main Flask app (6000+ lines)
│   ├── mysql_energy.py            # MySQL energy data handler
│   ├── ir_codes.json              # IR remote codes database
│   ├── energy_recording.json      # Energy recording config
│   ├── templates/
│   │   ├── base.html              # Base template
│   │   ├── dashboard.html         # Main dashboard
│   │   ├── login.html             # Login page
│   │   └── pages/
│   │       ├── dashboard_ac.html      # AC monitoring
│   │       ├── dashboard_lamp.html    # Lamp monitoring
│   │       ├── control_ac.html        # AC control panel
│   │       ├── control_lamp.html      # Lamp control panel
│   │       ├── control_outlet.html    # Outlet control
│   │       ├── energy.html            # Energy analytics
│   │       ├── ml_optimization.html   # ML tuning panel
│   │       ├── camera.html            # Camera feed
│   │       ├── ac_analytics.html      # AC analytics
│   │       ├── lamp_analytics.html    # Lamp analytics
│   │       ├── outlet_analytics.html  # Outlet analytics
│   │       ├── esp32_ota.html         # OTA firmware update
│   │       ├── occupancy_feedback.html # Occupancy feedback
│   │       ├── logs.html              # System logs viewer
│   │       ├── esp.cpp                # ESP32 AC firmware
│   │       └── lamp_esp.cpp           # ESP32 Lamp firmware
│   └── static/
│       ├── css/                   # Stylesheets
│       └── js/                    # JavaScript files
│
├── data/                      # Dataset & historical data
│   ├── ac_data.csv                # AC sensor history
│   └── lamp_data.csv              # Lamp sensor history
│
├── yolo/                      # YOLOv4-tiny model files
│   ├── yolov4-tiny.cfg
│   ├── yolov4-tiny.weights
│   └── coco.names
│
├── yolov8n.pt                 # YOLOv8 Nano model
└── smartroom.log              # Application log
```

---

## 📦 Prasyarat

### Hardware
- **Raspberry Pi 4** (atau lebih baru) dengan Raspberry Pi OS
- **ESP32** × 2 (satu untuk AC, satu untuk Lamp)
- **DHT22** × 3 (sensor suhu & kelembapan)
- **BH1750** × 3 (sensor cahaya)
- **IR LED** + transistor (untuk blast IR ke AC)
- **USB Camera** (untuk deteksi orang)
- **LED Strip / Lampu PWM** × 2

### Software
- Python 3.10+
- InfluxDB 2.x
- MQTT Broker (Mosquitto atau cloud broker)

---

## ⚙ Instalasi

### 1. Clone Repository

```bash
git clone <repository-url>
cd smartroom
```

### 2. Buat Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# atau
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install flask flask-socketio paho-mqtt influxdb-client
pip install ultralytics opencv-python-headless
pip install numpy deap pyswarms requests
```

### 4. Setup InfluxDB

1. Install InfluxDB 2.x pada Raspberry Pi
2. Buat organization: `IOTLAB`
3. Buat bucket: `SENSORDATA`
4. Generate API token dan update di `config.py`

### 5. Setup MQTT Broker

Sistem menggunakan cloud MQTT broker (`128.199.206.166:1883`). Jika ingin menggunakan broker lokal:

```bash
sudo apt install mosquitto mosquitto-clients
```

Lalu update `MQTT_BROKER` di `config.py`.

### 6. Flash ESP32

Upload firmware dari:
- `dashboard/templates/pages/esp.cpp` — untuk ESP32 AC controller
- `dashboard/templates/pages/lamp_esp.cpp` — untuk ESP32 Lamp controller

Gunakan Arduino IDE atau PlatformIO.

---

## 🔧 Konfigurasi

Edit file [`config.py`](config.py) untuk menyesuaikan:

```python
# MQTT
MQTT_BROKER   = "128.199.206.166"
MQTT_PORT     = 1883
MQTT_USER     = "labiot"
MQTT_PASSWORD = "iotlabftuns2023"

# InfluxDB
INFLUX_URL    = "http://localhost:8086"
INFLUX_ORG    = "IOTLAB"
INFLUX_BUCKET = "SENSORDATA"

# Genetic Algorithm
GA_CONFIG = {
    "population_size": 50,
    "generations": 30,
    "crossover_prob": 0.7,
    "mutation_prob": 0.2,
    ...
}

# PSO
PSO_CONFIG = {
    "n_particles": 30,
    "iterations": 50,
    "c1": 1.5, "c2": 1.5, "w": 0.7,
    ...
}

# Camera
YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.5
```

---

## 🚀 Menjalankan Sistem

### 1. Jalankan InfluxDB Writer (background service)

Menyimpan data MQTT ke InfluxDB:

```bash
python services/influx_writer.py
```

### 2. Jalankan AI Optimizer (main controller)

Mode otomatis — fetch sensor → GA/PSO optimize → kirim ke dashboard, loop setiap 10 menit:

```bash
python main.py
```

Output:
```
======================================================================
  SMART ROOM IoT - AI OPTIMIZATION SYSTEM
  GA -> AC Control (Genetic Algorithm)
  PSO -> Lamp Control (Particle Swarm)
  Mode: FULLY AUTOMATIC (no menu)
  Cycle interval: 600 seconds
======================================================================
```

### 3. Jalankan Dashboard Web

```bash
cd dashboard
python app.py
```

Dashboard tersedia di: `http://<raspberry-pi-ip>:5000`

**Login default:**
| Username | Password | Role |
|---|---|---|
| `admin` | `admin` | Admin (full access) |
| `user` | `user` | User (limited) |

---

## 🌐 Dashboard Web

Dashboard web menyediakan antarmuka monitoring dan kontrol:

| Halaman | Deskripsi |
|---|---|
| **Dashboard AC** | Monitoring suhu, kelembapan, status AC real-time |
| **Dashboard Lamp** | Monitoring cahaya dan brightness lampu |
| **Control AC** | Kontrol manual AC (suhu, fan, mode) + IR learning |
| **Control Lamp** | Kontrol manual brightness lampu |
| **Control Outlet** | Kontrol outlet listrik |
| **Energy** | Analytics penggunaan energi & estimasi biaya |
| **ML Optimization** | Panel tuning parameter GA & PSO, trigger optimasi manual |
| **Camera** | Live feed kamera + person detection |
| **Analytics** | Grafik historis sensor AC, Lamp, Outlet |
| **ESP32 OTA** | Over-The-Air firmware update untuk ESP32 |
| **Logs** | System logs viewer |

---

## 🧬 Algoritma Optimasi

### Genetic Algorithm (AC Control)

```
Chromosome: [temperature (float 16-30), fan_speed (int 1-3)]

Operators:
├── Selection:     Tournament (size=3)
├── Crossover:     BLX-α (α=0.3) untuk explorasi kontinu
├── Mutation:      Adaptive Gaussian (rate menurun seiring generasi)
├── Elitism:       Top 20% survive ke generasi berikutnya
├── Stagnation:    Diversity injection jika stuck
└── Validation:    Brute-force verification (45 kombinasi)

Fitness Function (max ~100):
├── Comfort Score (max 40)    — Gaussian terhadap target suhu (time-aware)
├── Humidity Response (max 15) — Proportional dehumidification
├── Fan Appropriateness (max 15) — Match fan ke gap suhu
├── Energy Efficiency (max 15)  — Minimize konsumsi daya
├── Uniformity Bonus (max 8)    — 3-sensor temperature uniformity
├── Trend Compensation (max 7)  — Antisipasi perubahan suhu
└── Penalties                   — Overcooling, extreme settings
```

### Particle Swarm Optimization (Lamp Control)

```
Particle: [brightness (0-100%)]

Parameters:
├── Swarm Size:        40 particles
├── Iterations:        120
├── Inertia (w):       0.9 → 0.4 (adaptive)
├── Cognitive (c1):    2.0
└── Social (c2):       2.0

Fitness Function (max ~100):
├── Lighting Comfort (max 50) — Target 300-500 lux saat ada orang
├── Energy Efficiency (max 30) — Minimize konsumsi daya
└── Ambient Adaptation (max 20) — Sesuaikan dengan cahaya alami
```

---

## 📡 MQTT Topics

| Topic | Publisher | Subscriber | Deskripsi |
|---|---|---|---|
| `smartroom/ac/sensors` | ESP32 AC | Raspi | Data suhu, kelembapan (3×DHT22) |
| `smartroom/ac/control` | Raspi | ESP32 AC | Perintah kontrol AC (suhu, fan) |
| `smartroom/ac/status` | ESP32 AC | Raspi | Status AC saat ini |
| `smartroom/ac/mode` | Raspi | ESP32 AC | Mode AC (MANUAL/ADAPTIVE) |
| `smartroom/lamp/sensors` | ESP32 Lamp | Raspi | Data lux (3×BH1750) |
| `smartroom/lamp/control` | Raspi | ESP32 Lamp | Perintah kontrol lampu |
| `smartroom/camera/detection` | Raspi | Dashboard | Hasil deteksi orang |
| `smartroom/ml/result` | main.py | Dashboard | Hasil optimasi GA + PSO |
| `smartroom/ml/status` | main.py | Dashboard | Status proses optimasi |
| `smartroom/ml/command` | Dashboard | main.py | Perintah optimasi dari dashboard |
| `smartroom/ir/learned` | ESP32 AC | Raspi | Hasil IR capture |
| `smartroom/ir/learn` | Raspi | ESP32 AC | Perintah belajar IR |

---

## 🔌 API Endpoints

Dashboard Flask menyediakan REST API:

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/` | Halaman dashboard utama |
| `GET` | `/api/state` | Status keseluruhan sistem |
| `POST` | `/api/ac/control` | Kontrol AC (temp, fan, action) |
| `POST` | `/api/lamp/control` | Kontrol lampu (brightness, action) |
| `POST` | `/api/optimization/update` | Update hasil optimasi GA/PSO |

---

## 📝 Catatan

- Sistem dirancang untuk berjalan 24/7 pada Raspberry Pi
- Siklus optimasi otomatis setiap 10 menit (configurable via `AUTO_INTERVAL`)
- Jika InfluxDB tidak tersedia, sistem fallback ke data MQTT terakhir
- Dashboard mendukung mode MANUAL dan ADAPTIVE (AI-controlled)
- Timezone harus di-set ke `Asia/Jakarta` pada Raspberry Pi:
  ```bash
  sudo timedatectl set-timezone Asia/Jakarta
  ```

---

## 👥 Kontributor

Proyek Smart Room IoT — Lab IoT, Universitas Sebelas Maret (UNS)

---

## 📄 Lisensi

Proyek ini dikembangkan untuk keperluan riset dan edukasi di Lab IoT UNS.
