# config.py
# Konfigurasi utama Smart Room System

# ===== MQTT =====
# Gunakan cloud broker agar ESP32 dan Raspberry Pi bisa saling berkomunikasi
# meski IP Raspberry Pi berubah-ubah
MQTT_BROKER   = "128.199.206.166"  # Lab IoT server
MQTT_PORT     = 1883
MQTT_USER     = "labiot"
MQTT_PASSWORD = "iotlabftuns2023"
MQTT_KEEPALIVE = 60

# ===== TELEGRAM ALERT =====
TELEGRAM_BOT_TOKEN = "8635310992:AAEXVrdT2r2aWg-8lb7txKIShN04wjzgnkI" # Isi dengan token bot dari BotFather
TELEGRAM_CHAT_ID = "6029706835"   # Isi dengan ID chat (gunakan userinfobot untuk cek)

# ===== MQTT TOPICS =====

TOPICS = {
    # AC — cocokkan dengan esp.cpp TOPIC_AC_*
    "ac_sensors":         "smartroom/ac/sensors",      # ESP32 publish, Flask subscribe
    "ac_control":         "smartroom/ac/control",      # Flask publish, ESP32 subscribe
    "ac_status":          "smartroom/ac/status",       # ESP32 publish
    "ac_mode":            "smartroom/ac/mode",         # Flask publish, ESP32 subscribe
    "ac_connection":      "smartroom/ac/connection",  # ESP32 publish (online/offline)
    "ac_ir_learned":      "smartroom/ir/learned",     # ESP32 publish hasil IR capture
    "ac_ir_learn_cmd":    "smartroom/ir/learn",       # Flask publish perintah belajar IR
    "ac_ir_send":         "smartroom/ir/send",        # Flask publish kirim IR code
    "ac_ir_learn_status": "smartroom/ac/ir_learn_status",
    "ac_ping":            "smartroom/ac/ping",

    # Lamp
    "lamp_sensors": "smartroom/lamp/sensors",
    "lamp_control": "smartroom/lamp/control",
    "lamp_status":  "smartroom/lamp/status",

    # Camera — cocokkan dengan esp.cpp TOPIC_CAMERA_STATUS
    "camera_detection": "smartroom/camera/detection",
    "camera_status":    "smartroom/camera/status",    # Flask publish, ESP32 subscribe (person detect)

    # Dashboard
    "dashboard_state": "smartroom/dashboard/state",

    # Wildcard (subscribe all)
    "all": "smartroom/#",
}

# ===== WIFI (untuk referensi ESP32) =====
WIFI_SSID = "IoT"
WIFI_PASSWORD = "agusramelan"

# ===== CAMERA =====
CAMERA_INDEX = 0                # 0 = USB camera pertama, atau path RTSP
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_DETECTION_INTERVAL = 5   # Deteksi setiap 5 detik
YOLO_MODEL = "yolov8n.pt"      # Model YOLO (nano untuk Raspi)
YOLO_CONFIDENCE = 0.5
PERSON_CLASS_ID = 0             # COCO class ID untuk "person"

# ===== DATA STORAGE =====
DATA_DIR = "data"
AC_DATA_FILE = "data/ac_data.csv"
LAMP_DATA_FILE = "data/lamp_data.csv"
IR_CODES_FILE = "data/ir_codes.json"

# ===== AC - GENETIC ALGORITHM =====
GA_CONFIG = {
    "population_size": 50,
    "generations": 30,
    "crossover_prob": 0.7,
    "mutation_prob": 0.2,
    "ac_temp_min": 16,
    "ac_temp_max": 30,
    "fan_speed_min": 1,
    "fan_speed_max": 3,
    "comfort_temp_min": 22.0,
    "comfort_temp_max": 26.0,
    "comfort_hum_min": 40.0,
    "comfort_hum_max": 60.0,
}

# ===== LAMP - PSO =====
PSO_CONFIG = {
    "n_particles": 30,
    "iterations": 50,
    "c1": 1.5,          # Cognitive parameter
    "c2": 1.5,          # Social parameter
    "w": 0.7,           # Inertia weight
    "brightness_min": 0,
    "brightness_max": 255,
    "target_lux_work": 400,
    "target_lux_relax": 200,
    "target_lux_sleep": 50,
    "target_lux_min": 100,
    "lamp_max_lux_output": 500,  # Estimasi lux dari lampu pada brightness 255
}

# ===== OPTIMIZATION =====
OPTIMIZATION_INTERVAL = 30  # Jalankan ML setiap 30 detik

# ===== DASHBOARD =====
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000

# ===== LOGGING =====
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "smartroom.log"