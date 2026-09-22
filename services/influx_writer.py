#!/usr/bin/env python3
"""InfluxDB Writer - Writes MQTT sensor data to InfluxDB 2.x"""

import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# ============================================================
# KONFIGURASI INFLUXDB - UPDATE DENGAN KREDENSIAL BARU
# ============================================================
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "rfi_HvWdjwaG8jB3Rqx6g0y5kMWRfSfq_HmLLUvkom1yaHKvwonU9Qfj6nlZjTqb_I0leIREUnMhvQQXtgETfg=="
INFLUX_ORG = "IOTLAB"
INFLUX_BUCKET = "SENSORDATA"
MQTT_BROKER   = "128.199.206.166"
MQTT_PORT     = 1883
MQTT_USER     = "labiot"
MQTT_PASSWORD = "iotlabftuns2023"
# ============================================================

def main():
    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
    except ImportError:
        print("[ERROR] influxdb-client not installed!")
        print("Run: pip install influxdb-client")
        return

    influx_client = None
    write_api = None

    try:
        influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        print(f"[InfluxDB] Connected to {INFLUX_URL}")
        print(f"[InfluxDB] Org={INFLUX_ORG}, Bucket={INFLUX_BUCKET}")
    except Exception as e:
        print(f"[InfluxDB] Connection failed: {e}")
        return

    def on_connect(client, userdata, flags, rc):
        print(f"[MQTT] Connected rc={rc}")
        # Subscribe ke topic dengan prefix smartroom/
        client.subscribe("smartroom/ac/sensors")
        client.subscribe("smartroom/lamp/sensors")
        client.subscribe("smartroom/camera/detection")
        client.subscribe("smartroom/ac/optimization")
        client.subscribe("smartroom/lamp/optimization")
        print("[MQTT] Subscribed to smartroom/* sensor topics")

    def on_message(client, userdata, msg):
        if not write_api:
            return

        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            if topic == "smartroom/ac/sensors":
                point = Point("ac_sensor") \
                    .tag("source", "esp32_ac") \
                    .field("temperature", float(payload.get("temperature", 0))) \
                    .field("humidity", float(payload.get("humidity", 0))) \
                    .field("heat_index", float(payload.get("heat_index", 0))) \
                    .field("ac_temp", int(payload.get("ac_temp", 0))) \
                    .field("fan_speed", int(payload.get("fan_speed", 0)))
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                print(f"[InfluxDB] AC: temp={payload.get('temperature')} hum={payload.get('humidity')}")

            elif topic == "smartroom/lamp/sensors":
                lux1 = float(payload.get("lux1", payload.get("lux", 0)))
                lux2 = float(payload.get("lux2", payload.get("lux", 0)))
                lux3 = float(payload.get("lux3", payload.get("lux", 0)))
                lux_avg = round((lux1 + lux2 + lux3) / 3.0, 1)
                b1 = float(payload.get("brightness1", payload.get("brightness", 0)))
                b2 = float(payload.get("brightness2", b1))
                bright_avg = round((b1 + b2) / 2.0, 1)
                point = Point("lamp_sensor") \
                    .tag("source", "esp32_lamp") \
                    .field("lux1", lux1) \
                    .field("lux2", lux2) \
                    .field("lux3", lux3) \
                    .field("lux_avg", lux_avg) \
                    .field("brightness1", b1) \
                    .field("brightness2", b2) \
                    .field("brightness_avg", bright_avg) \
                    .field("motion", int(payload.get("motion", 0)))
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                print(f"[InfluxDB] Lamp: lux1={lux1} lux2={lux2} lux3={lux3} avg={lux_avg} motion={payload.get('motion')}")

            elif topic == "smartroom/camera/detection":
                point = Point("camera") \
                    .tag("source", "raspi_camera") \
                    .field("person_count", int(payload.get("person_count", 0))) \
                    .field("occupied", bool(payload.get("occupied", False)))
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                print(f"[InfluxDB] Camera: persons={payload.get('person_count')}")

            elif topic == "smartroom/ac/optimization":
                point = Point("ac_optimization") \
                    .tag("algorithm", "genetic") \
                    .field("recommended_temp", float(payload.get("recommended_temp", 0))) \
                    .field("fan_speed", int(payload.get("fan_speed", 0))) \
                    .field("energy_score", float(payload.get("energy_score", 0))) \
                    .field("comfort_score", float(payload.get("comfort_score", 0)))
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                print(f"[InfluxDB] AC Optimization: temp={payload.get('recommended_temp')}")

            elif topic == "smartroom/lamp/optimization":
                point = Point("lamp_optimization") \
                    .tag("algorithm", "pso") \
                    .field("brightness", float(payload.get("brightness", 0))) \
                    .field("target_lux", float(payload.get("target_lux", 0))) \
                    .field("efficiency", float(payload.get("efficiency", 0)))
                write_api.write(bucket=INFLUX_BUCKET, record=point)
                print(f"[InfluxDB] Lamp Optimization: brightness={payload.get('brightness')}")

        except Exception as e:
            print(f"[InfluxDB] Write error: {e}")

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "influx_writer_v2")
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("[InfluxDB Writer] Running... Press Ctrl+C to stop")
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\n[InfluxDB Writer] Stopped")
    except Exception as e:
        print(f"[MQTT] Error: {e}")
    finally:
        if influx_client:
            influx_client.close()

if __name__ == "__main__":
    main()