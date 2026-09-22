import paho.mqtt.client as mqtt
import json
import csv
import os
import logging
from datetime import datetime
import time

logger = logging.getLogger("DataCollector")


class DataCollector:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "DataCollector")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.broker = broker
        self.port = port
        os.makedirs("data", exist_ok=True)
        self._init_csv("data/ac_data.csv",
                       ["timestamp", "temperature", "humidity", "occupancy",
                        "ac_temp_setting", "ac_state", "mode"])
        self._init_csv("data/lamp_data.csv",
                       ["timestamp", "lux", "occupancy", "brightness", "lamp_state", "mode"])
        self.last_ac_save = 0
        self.last_lamp_save = 0
        self.save_interval_seconds = 300  # 5 minutes
        self.ac_mode = "MANUAL"
        self.lamp_mode = "MANUAL"

    def _init_csv(self, path, headers):
        if not os.path.exists(path):
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"DataCollector connected (rc={rc})")
        client.subscribe("smartroom/+/sensors")
        client.subscribe("smartroom/+/status")
        client.subscribe("smartroom/+/mode")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            topic = msg.topic
            timestamp = datetime.now().isoformat()
            if "ac/sensors" in topic:
                self._save_ac_data(timestamp, data)
            elif "lamp/sensors" in topic:
                self._save_lamp_data(timestamp, data)
            elif "ac/mode" in topic:
                self.ac_mode = data.get("mode", "MANUAL")
            elif "lamp/mode" in topic:
                self.lamp_mode = data.get("mode", "MANUAL")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _save_ac_data(self, timestamp, data):
        now = time.time()
        if now - self.last_ac_save < self.save_interval_seconds:
            return
        self.last_ac_save = now
        
        with open("data/ac_data.csv", 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                data.get("temperature", 0),
                data.get("humidity", 0),
                data.get("occupancy", False),
                data.get("ac_temp_setting", 0),
                data.get("ac_state", "unknown"),
                self.ac_mode
            ])

    def _save_lamp_data(self, timestamp, data):
        now = time.time()
        if now - self.last_lamp_save < self.save_interval_seconds:
            return
        self.last_lamp_save = now
        
        with open("data/lamp_data.csv", 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                data.get("lux", 0),
                data.get("occupancy", False),
                data.get("brightness", 0),
                data.get("lamp_state", "unknown"),
                self.lamp_mode
            ])

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        logger.info("DataCollector started")