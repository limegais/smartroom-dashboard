#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <Wire.h>


// Program ESP32 lampu - sistem pencahayaan adaptif
// Lux BH1750 dikoreksi dengan dark offset dan faktor kalibrasi.

// ==================== WIFI DAN MQTT ====================

const char *ssid = "IoT";
const char *password = "agusramelan";

// Konfigurasi Server MQTT Lab IoT (Disamakan dengan Dashboard/AC)
const char *mqtt_server = "128.199.206.166"; 
const int mqtt_port = 1883;
const char *mqtt_user = "labiot";
const char *mqtt_password = "iotlabftuns2023";

const char *mqtt_client_id = "esp32_lamp_controller";

#define TOPIC_LAMP_SENSORS "smartroom/lamp/sensors"
#define TOPIC_LAMP_CONTROL "smartroom/lamp/control"

// ==================== I2C, TCA9548A, DAN BH1750 ====================

#define TCA_ADDR 0x70
#define BH1750_ADDR 0x23
#define BH1750_MODE 0x20 // Continuous H-Resolution Mode

// ==================== PIN ALAT ====================

#define PIR1_PIN 14
#define PIR2_PIN 12
#define PWM1_PIN 25 // DAC1 ESP32
#define PWM2_PIN 26 // DAC2 ESP32

// ==================== VARIABEL SISTEM ====================

float lux1_s = 0.0f;
float lux2_s = 0.0f;
float lux3_s = 0.0f;

// Faktor kalibrasi agar pembacaan sensor mendekati lux meter pembanding
float calibFactor1 = 3.138f;
float calibFactor2 = 3.104f;
float calibFactor3 = 3.634f;

// Dark offset agar saat kondisi sangat gelap nilai bisa turun ke 0 lux
float darkOffset1 = 0.0f;
float darkOffset2 = 0.0f;
float darkOffset3 = 0.0f;

// Nilai kecil di bawah ambang ini dianggap 0 lux
const float DARK_THRESHOLD = 5.0f;

int pwm1 = 0;
int pwm2 = 0;

bool motionDetected = false;
unsigned long lastMotionTime = 0;
const unsigned long PIR_TIMEOUT = 60000;

const unsigned long SENSOR_READ_INTERVAL = 500;
const unsigned long SENSOR_PUBLISH_INTERVAL = 3000;

unsigned long lastSensorRead = 0;
unsigned long lastSensorPublish = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long bootTime = 0;

WiFiClient espClient;
PubSubClient client(espClient);

// ==================== FUNGSI I2C SENSOR ====================

void tcaSelect(uint8_t channel) {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
  delay(20);
}

void resetI2C() {
  Wire.end();
  delay(10);
  Wire.begin();
  Wire.setClock(50000);
}

float readBH1750(uint8_t channel) {
  tcaSelect(channel);

  Wire.beginTransmission(BH1750_ADDR);
  Wire.write(BH1750_MODE);

  if (Wire.endTransmission() != 0) {
    Serial.printf("[BH1750] Error tulis I2C channel %d\n", channel);
    resetI2C();
    return -1.0f; // -1 = error sensor, bukan 0 lux
  }

  delay(150);

  Wire.requestFrom(BH1750_ADDR, 2);

  if (Wire.available() < 2) {
    Serial.printf("[BH1750] Error baca I2C channel %d\n", channel);
    resetI2C();
    return -1.0f; // -1 = error sensor, bukan 0 lux
  }

  uint16_t raw = Wire.read();
  raw <<= 8;
  raw |= Wire.read();

  float lux = raw / 1.2f;

  if (lux < 0 || lux > 65535) {
    return -1.0f;
  }

  return lux;
}

float calibrateLux(float rawLux, float calibFactor, float darkOffset) {
  float correctedRaw = rawLux - darkOffset;

  if (correctedRaw < 0.0f) {
    correctedRaw = 0.0f;
  }

  float lux = correctedRaw * calibFactor;

  if (lux < DARK_THRESHOLD) {
    lux = 0.0f;
  }

  return lux;
}

void readLuxSensor(uint8_t channel, float calibFactor, float darkOffset,
                   float &result) {
  float rawLux = readBH1750(channel);

  // 0 lux tetap valid. Error sensor ditandai dengan -1.
  if (rawLux >= 0.0f) {
    result = calibrateLux(rawLux, calibFactor, darkOffset);
  }
}

// ==================== WIFI DAN MQTT ====================

void setupWiFi() {
  Serial.print("[WiFi] Menghubungkan ke ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[WiFi] Terhubung. IP ESP32: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Gagal terhubung");
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  char msg[512];
  int len = min((int)length, 511);

  memcpy(msg, payload, len);
  msg[len] = '\0';

  StaticJsonDocument<512> doc;

  if (deserializeJson(doc, msg) != DeserializationError::Ok) {
    Serial.println("[MQTT] Format JSON tidak valid");
    return;
  }

  String topicStr = String(topic);

  if (topicStr == TOPIC_LAMP_CONTROL) {
    if (doc.containsKey("brightness1")) {
      int brightness1 = constrain(doc["brightness1"].as<int>(), 0, 100);
      int brightness2 = constrain(doc["brightness2"] | brightness1, 0, 100);

      pwm1 = map(brightness1, 0, 100, 0, 255);
      pwm2 = map(brightness2, 0, 100, 0, 255);

      Serial.printf(
          "[MQTT] Brightness1=%d%% Brightness2=%d%% -> PWM1=%d PWM2=%d\n",
          brightness1, brightness2, pwm1, pwm2);
    }

    else if (doc.containsKey("brightness")) {
      int brightness = constrain(doc["brightness"].as<int>(), 0, 100);

      pwm1 = map(brightness, 0, 100, 0, 255);
      pwm2 = map(brightness, 0, 100, 0, 255);

      Serial.printf("[MQTT] Brightness=%d%% -> PWM1=%d PWM2=%d\n", brightness,
                    pwm1, pwm2);
    }

    // Dark offset dapat dikirim dari Raspberry Pi jika ingin diatur manual
    if (doc.containsKey("darkOffset1")) {
      darkOffset1 = max(0.0f, doc["darkOffset1"].as<float>());
    }

    if (doc.containsKey("darkOffset2")) {
      darkOffset2 = max(0.0f, doc["darkOffset2"].as<float>());
    }

    if (doc.containsKey("darkOffset3")) {
      darkOffset3 = max(0.0f, doc["darkOffset3"].as<float>());
    }
  }
}

bool mqttConnect() {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  Serial.printf("[MQTT] Menghubungkan ke %s:%d\n", mqtt_server, mqtt_port);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  client.setBufferSize(1024);

  // Menggunakan user dan password untuk server MQTT
  if (client.connect(mqtt_client_id, mqtt_user, mqtt_password)) {
    Serial.println("[MQTT] Terhubung");
    client.subscribe(TOPIC_LAMP_CONTROL);
    return true;
  }

  Serial.printf("[MQTT] Gagal, kode=%d\n", client.state());
  return false;
}

// ==================== PUBLISH DATA SENSOR ====================

void publishSensorData() {
  if (!client.connected()) {
    return;
  }

  float brightness1 = pwm1 * 100.0f / 255.0f;
  float brightness2 = pwm2 * 100.0f / 255.0f;
  float luxAvg = (lux1_s + lux2_s + lux3_s) / 3.0f;

  StaticJsonDocument<512> doc;

  doc["lux1"] = round(lux1_s * 10) / 10.0;
  doc["lux2"] = round(lux2_s * 10) / 10.0;
  doc["lux3"] = round(lux3_s * 10) / 10.0;
  doc["lux_avg"] = round(luxAvg * 10) / 10.0;

  doc["brightness1"] = round(brightness1 * 10) / 10.0;
  doc["brightness2"] = round(brightness2 * 10) / 10.0;

  doc["motion"] = motionDetected;

  doc["darkOffset1"] = round(darkOffset1 * 100) / 100.0;
  doc["darkOffset2"] = round(darkOffset2 * 100) / 100.0;
  doc["darkOffset3"] = round(darkOffset3 * 100) / 100.0;

  doc["rssi"] = WiFi.RSSI();
  doc["uptime"] = (millis() - bootTime) / 1000;

  String payload;
  serializeJson(doc, payload);
  client.publish(TOPIC_LAMP_SENSORS, payload.c_str());

  Serial.printf("[PUB] L1=%.1f L2=%.1f L3=%.1f Avg=%.1f lx | B1=%.1f%% "
                "B2=%.1f%% | Motion=%s\n",
                lux1_s, lux2_s, lux3_s, luxAvg, brightness1, brightness2,
                motionDetected ? "YES" : "NO");
}

// ==================== DARK OFFSET ====================

void calibrateDarkOffset() {
  Serial.println("[DARKCAL] Tutup sensor atau buat ruangan sangat gelap.");

  float sum1 = 0.0f;
  float sum2 = 0.0f;
  float sum3 = 0.0f;
  int count = 0;

  for (int i = 0; i < 10; i++) {
    float r1 = readBH1750(1);
    float r2 = readBH1750(2);
    float r3 = readBH1750(3);

    if (r1 >= 0.0f && r2 >= 0.0f && r3 >= 0.0f) {
      sum1 += r1;
      sum2 += r2;
      sum3 += r3;
      count++;
    }

    delay(200);
  }

  if (count > 0) {
    darkOffset1 = sum1 / count;
    darkOffset2 = sum2 / count;
    darkOffset3 = sum3 / count;

    Serial.println("[DARKCAL] Offset gelap tersimpan:");
    Serial.printf("darkOffset1=%.2f | darkOffset2=%.2f | darkOffset3=%.2f\n",
                  darkOffset1, darkOffset2, darkOffset3);
  } else {
    Serial.println("[DARKCAL] Gagal membaca sensor.");
  }
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n============================================");
  Serial.println(" ESP32 Lamp Node - Adaptive Lighting System");
  Serial.println(" Sensor: 3x BH1750 via TCA9548A");
  Serial.println(" Output: DAC PWM1 dan PWM2");
  Serial.println(" Lux: dark offset + faktor kalibrasi");
  Serial.println("============================================\n");

  bootTime = millis();

  Wire.begin();
  Wire.setClock(50000);

  pinMode(PIR1_PIN, INPUT);
  pinMode(PIR2_PIN, INPUT);

  dacWrite(PWM1_PIN, pwm1);
  dacWrite(PWM2_PIN, pwm2);

  setupWiFi();
  mqttConnect();

  Serial.println(
      "[READY] Ketik STATUS pada Serial Monitor untuk melihat data.");
  Serial.println(
      "[READY] Ketik DARKCAL saat sensor gelap untuk menyimpan dark offset.");
}

// ==================== LOOP ====================

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastReconnectAttempt > 10000) {
      lastReconnectAttempt = millis();
      Serial.println("[WiFi] Reconnecting...");
      WiFi.disconnect();
      WiFi.begin(ssid, password);
    }
  }

  if (WiFi.status() == WL_CONNECTED && !client.connected()) {
    if (millis() - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = millis();
      mqttConnect();
    }
  }

  client.loop();

  bool pirState = digitalRead(PIR1_PIN) || digitalRead(PIR2_PIN);

  if (pirState) {
    lastMotionTime = millis();
  }

  motionDetected = (millis() - lastMotionTime < PIR_TIMEOUT);

  if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
    lastSensorRead = millis();

    readLuxSensor(1, calibFactor1, darkOffset1, lux1_s);
    delay(30);

    readLuxSensor(2, calibFactor2, darkOffset2, lux2_s);
    delay(30);

    readLuxSensor(3, calibFactor3, darkOffset3, lux3_s);
  }

  // ESP32 hanya menjalankan nilai PWM yang diterima dari MQTT.
  dacWrite(PWM1_PIN, pwm1);
  dacWrite(PWM2_PIN, pwm2);

  if (millis() - lastSensorPublish >= SENSOR_PUBLISH_INTERVAL) {
    lastSensorPublish = millis();
    publishSensorData();
  }

  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "DARKCAL") {
      calibrateDarkOffset();
    }

    else if (cmd == "STATUS") {
      float luxAvg = (lux1_s + lux2_s + lux3_s) / 3.0f;

      Serial.println("\n========== STATUS ==========");
      Serial.printf("MQTT Broker : %s:%d\n", mqtt_server, mqtt_port);

      Serial.printf("Lux1        : %.1f lx\n", lux1_s);
      Serial.printf("Lux2        : %.1f lx\n", lux2_s);
      Serial.printf("Lux3        : %.1f lx\n", lux3_s);
      Serial.printf("Lux Avg     : %.1f lx\n", luxAvg);

      Serial.printf("DarkOffset  : %.2f | %.2f | %.2f\n", darkOffset1,
                    darkOffset2, darkOffset3);

      Serial.printf("PWM1        : %d (%.1f%%)\n", pwm1,
                    pwm1 * 100.0f / 255.0f);
      Serial.printf("PWM2        : %d (%.1f%%)\n", pwm2,
                    pwm2 * 100.0f / 255.0f);

      Serial.printf("Motion      : %s\n", motionDetected ? "YES" : "NO");
      Serial.printf("WiFi        : %s\n", WiFi.status() == WL_CONNECTED
                                              ? "CONNECTED"
                                              : "DISCONNECTED");
      Serial.printf("MQTT        : %s\n",
                    client.connected() ? "CONNECTED" : "DISCONNECTED");
      Serial.printf("RSSI        : %d dBm\n", WiFi.RSSI());
      Serial.printf("Uptime      : %lu s\n", (millis() - bootTime) / 1000);

      Serial.println("Lux Source  : BH1750 + dark offset + calibration factor");
      Serial.println("============================\n");
    }
  }

  delay(50);
}
