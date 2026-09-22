#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// =====================================================
// KONFIGURASI WIFI & MQTT
// =====================================================
const char* ssid = "IoT";
const char* password = "agusramelan";

const char* mqtt_server = "128.199.206.166";
const int mqtt_port = 1883;
const char* mqtt_user = "labiot";
const char* mqtt_password = "iotlabftuns2023";

WiFiClient espClient;
PubSubClient client(espClient);

// =====================================================
// SISTEM MONITORING RUANGAN
// ESP32 + 1 MAX3485 + 3 SENSOR
//
// Sensor:
// ID 1 = CO2
// ID 2 = Temperature + Humidity
// ID 3 = Illuminance
//
// Baudrate : 4800
//
// ESP32:
// RX2   = GPIO16
// TX2   = GPIO17
// DE/RE = GPIO27
// =====================================================

#define RX2_PIN    16
#define TX2_PIN    17
#define DE_RE_PIN  27

#define MODBUS_BAUD 4800

HardwareSerial RS485(2);


// =====================================================
// PERSAMAAN KALIBRASI
// =====================================================

// CO2
// y = 0.2218516x + 231.900647
float kalibrasiCO2(float x)
{
  return (0.2218516 * x) + 231.900647;
}


// Temperature
// y = -0.83652255x + 46.78491663
float kalibrasiTemperature(float x)
{
  return (-0.83652255 * x) + 46.78491663;
}


// Humidity
// y = 0.701912687x + 8.771442108
float kalibrasiHumidity(float x)
{
  return (0.701912687 * x) + 8.771442108;
}


// Lux
// y = 0.951325255x - 4.155780843
float kalibrasiLux(float x)
{
  return (0.951325255 * x) + -4.155780843;
}


// =====================================================
// CRC16 MODBUS
// =====================================================

uint16_t modbusCRC(uint8_t *data, uint8_t length)
{
  uint16_t crc = 0xFFFF;

  for (uint8_t i = 0; i < length; i++)
  {
    crc ^= data[i];

    for (uint8_t j = 0; j < 8; j++)
    {
      if (crc & 0x0001)
      {
        crc >>= 1;
        crc ^= 0xA001;
      }
      else
      {
        crc >>= 1;
      }
    }
  }

  return crc;
}


// =====================================================
// FUNGSI BACA MODBUS
// =====================================================

int readModbus(
  uint8_t slaveID,
  uint16_t startAddress,
  uint16_t quantity,
  uint8_t *response,
  uint8_t maxResponseLength
)
{
  uint8_t request[8];

  // ---------------------------------------------------
  // Slave ID
  // ---------------------------------------------------

  request[0] = slaveID;

  // ---------------------------------------------------
  // Function 03
  // ---------------------------------------------------

  request[1] = 0x03;

  // ---------------------------------------------------
  // Start Address
  // ---------------------------------------------------

  request[2] = (startAddress >> 8) & 0xFF;
  request[3] = startAddress & 0xFF;

  // ---------------------------------------------------
  // Quantity
  // ---------------------------------------------------

  request[4] = (quantity >> 8) & 0xFF;
  request[5] = quantity & 0xFF;

  // ---------------------------------------------------
  // CRC
  // ---------------------------------------------------

  uint16_t crc = modbusCRC(request, 6);

  request[6] = crc & 0xFF;
  request[7] = (crc >> 8) & 0xFF;


  // ---------------------------------------------------
  // Bersihkan RX buffer
  // ---------------------------------------------------

  while (RS485.available())
  {
    RS485.read();
  }


  // ---------------------------------------------------
  // TRANSMIT
  // ---------------------------------------------------

  digitalWrite(DE_RE_PIN, HIGH);

  delayMicroseconds(500);

  RS485.write(request, 8);

  RS485.flush();

  delayMicroseconds(1000);


  // ---------------------------------------------------
  // RECEIVE
  // ---------------------------------------------------

  digitalWrite(DE_RE_PIN, LOW);


  // ---------------------------------------------------
  // Baca response
  // ---------------------------------------------------

  int index = 0;

  unsigned long startTime = millis();

  while (millis() - startTime < 1000)
  {
    while (RS485.available())
    {
      if (index < maxResponseLength)
      {
        response[index] = RS485.read();
        index++;
      }
      else
      {
        RS485.read();
      }
    }
  }

  return index;
}

// =====================================================
// FUNGSI KONEKSI WIFI & MQTT
// =====================================================
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("esp32_outdoor_sensor", mqtt_user, mqtt_password)) {
      Serial.println("connected to MQTT Broker");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);

  pinMode(DE_RE_PIN, OUTPUT);

  // Awal dalam mode RECEIVE
  digitalWrite(DE_RE_PIN, LOW);

  // UART2
  RS485.begin(
    MODBUS_BAUD,
    SERIAL_8N1,
    RX2_PIN,
    TX2_PIN
  );

  // Mulai WiFi dan MQTT
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  delay(1000);

  Serial.println();
  Serial.println("========================================");
  Serial.println(" SISTEM MONITORING RUANGAN");
  Serial.println("========================================");
  Serial.println("CO2       : Slave ID 1");
  Serial.println("Temp/Humi : Slave ID 2");
  Serial.println("Lux       : Slave ID 3");
  Serial.println("Baudrate  : 4800");
  Serial.println("========================================");

  delay(1000);
}


// =====================================================
// LOOP
// =====================================================

void loop()
{
  // Jaga koneksi MQTT tetap hidup
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  uint8_t response[32];
  int length;

  // Variabel penampung hasil untuk dikirim ke JSON MQTT
  float finalCO2 = -1.0;
  float finalTemp = -1.0;
  float finalHum = -1.0;
  float finalLux = -1.0;

  // ===================================================
  // 1. SENSOR CO2
  // ===================================================

  length = readModbus(
    1,          // Slave ID
    0x0002,     // Register CO2
    1,          // Quantity
    response,
    sizeof(response)
  );


  Serial.println();
  Serial.println("---------- DATA SENSOR ----------");


  if (length >= 7)
  {
    // -----------------------------------------------
    // Nilai RAW CO2
    // -----------------------------------------------

    uint16_t co2Raw =
      ((uint16_t)response[3] << 8) |
      response[4];


    // -----------------------------------------------
    // Kalibrasi CO2
    // -----------------------------------------------

    float co2Kalibrasi =
      kalibrasiCO2((float)co2Raw);
    
    finalCO2 = co2Kalibrasi;

    Serial.print("CO2          : ");
    Serial.print(co2Kalibrasi, 1);
    Serial.println(" ppm");
  }
  else
  {
    Serial.println("CO2          : ERROR");
  }


  delay(200);


  // ===================================================
  // 2. SENSOR TEMPERATURE + HUMIDITY
  // ===================================================

  length = readModbus(
    2,          // Slave ID
    0x0000,     // Register awal
    2,          // Quantity
    response,
    sizeof(response)
  );


  if (length >= 9)
  {
    // -----------------------------------------------
    // RAW HUMIDITY
    // -----------------------------------------------

    uint16_t humidityRaw =
      ((uint16_t)response[3] << 8) |
      response[4];


    // -----------------------------------------------
    // RAW TEMPERATURE
    // -----------------------------------------------

    uint16_t temperatureRaw =
      ((uint16_t)response[5] << 8) |
      response[6];


    // -----------------------------------------------
    // Nilai sebelum kalibrasi
    //
    // Sensor menggunakan skala 0.1
    // -----------------------------------------------

    float humiditySensor =
      humidityRaw / 10.0;

    float temperatureSensor =
      temperatureRaw / 10.0;


    // -----------------------------------------------
    // Kalibrasi
    // -----------------------------------------------

    float humidityKalibrasi =
      kalibrasiHumidity(humiditySensor);

    float temperatureKalibrasi =
      kalibrasiTemperature(temperatureSensor);
      
    finalHum = humidityKalibrasi;
    finalTemp = temperatureKalibrasi;

    // -----------------------------------------------
    // Tampilkan
    // -----------------------------------------------

    Serial.print("Temperature  : ");
    Serial.print(temperatureKalibrasi, 2);
    Serial.println(" C");

    Serial.print("Humidity     : ");
    Serial.print(humidityKalibrasi, 2);
    Serial.println(" %RH");
  }
  else
  {
    Serial.println("Temperature  : ERROR");
    Serial.println("Humidity     : ERROR");
  }


  delay(200);


  // ===================================================
  // 3. SENSOR LUX
  // ===================================================

  length = readModbus(
    3,          // Slave ID
    0x0002,     // Register Lux
    2,          // Quantity
    response,
    sizeof(response)
  );


  if (length >= 9)
  {
    // -----------------------------------------------
    // Ambil dua register
    // -----------------------------------------------

    uint16_t reg1 =
      ((uint16_t)response[3] << 8) |
      response[4];

    uint16_t reg2 =
      ((uint16_t)response[5] << 8) |
      response[6];


    // -----------------------------------------------
    // Gabungkan menjadi nilai RAW
    // -----------------------------------------------

    uint32_t luxRaw32 =
      ((uint32_t)reg1 << 16) |
      reg2;


    // -----------------------------------------------
    // Konversi sesuai format sensor
    // -----------------------------------------------

    float luxSensor =
      luxRaw32 / 1000.0;


    // -----------------------------------------------
    // Kalibrasi Lux
    // -----------------------------------------------

    float luxKalibrasi =
      kalibrasiLux(luxSensor);
      
    finalLux = luxKalibrasi;

    // -----------------------------------------------
    // Tampilkan
    // -----------------------------------------------

    Serial.print("Illuminance  : ");
    Serial.print(luxKalibrasi, 2);
    Serial.println(" lux");
  }
  else
  {
    Serial.println("Illuminance  : ERROR");
  }


  // ===================================================
  // PUBLISH DATA KE MQTT
  // ===================================================
  StaticJsonDocument<200> doc;
  
  // Masukkan nilai sensor ke dalam objek JSON (atau -1 jika ERROR)
  doc["co2"]         = finalCO2;
  doc["temperature"] = finalTemp;
  // Menjaga format penulisan key di MQTT sama dengan dashboard app.py
  doc["humidity"]    = finalHum;
  doc["lux"]         = finalLux;

  // Format menjadi JSON String
  char jsonString[200];
  serializeJson(doc, jsonString);
  
  // Kirim ke MQTT Broker
  client.publish("smartroom/outdoor/sensors", jsonString);
  
  Serial.print("=> Mengirim ke MQTT: ");
  Serial.println(jsonString);


  // ===================================================
  // AKHIR SIKLUS
  // ===================================================

  Serial.println("---------------------------------");

  // Pembacaan berikutnya setiap 5 detik
  delay(5000);

}