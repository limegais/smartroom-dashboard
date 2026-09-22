import paho.mqtt.client as mqtt
import json
import time
import logging

logger = logging.getLogger("MQTTHandler")

MQTT_BROKER = "128.199.206.166"
MQTT_PORT = 1883
MQTT_USER = "labiot"
MQTT_PASSWORD = "iotlabftuns2023"
MQTT_KEEPALIVE = 60


class MQTTHandler:
    def __init__(self, client_id="SmartRoom_Handler", broker=None, port=None):
        self.broker = broker or MQTT_BROKER
        self.port = port or MQTT_PORT
        self.client_id = client_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
        if MQTT_USER and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self._callbacks = {}
        self.connected = False
        self._reconnect_count = 0
        self.client.will_set(
            "smartroom/server/status",
            json.dumps({"status": "offline", "timestamp": time.time()}),
            qos=1, retain=True
        )

    def connect(self):
        try:
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, MQTT_KEEPALIVE)
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def start(self):
        if self.connect():
            self.client.loop_start()
            logger.info("MQTT loop started")
            return True
        return False

    def stop(self):
        self.publish("smartroom/server/status",
                     {"status": "offline", "timestamp": time.time()})
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT stopped")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self._reconnect_count = 0
            logger.info("Connected to MQTT broker!")
            client.subscribe("smartroom/#", qos=1)
            self.publish("smartroom/server/status", {
                "status": "online", "timestamp": time.time()
            })
        else:
            self.connected = False
            logger.error(f"Connection failed, rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self._reconnect_count += 1
            logger.warning(f"Unexpected disconnect (rc={rc})")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = msg.payload.decode()
        for pattern, callbacks in self._callbacks.items():
            if self._topic_matches(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        logger.error(f"Callback error for {topic}: {e}")

    def register_callback(self, topic_pattern, callback):
        if topic_pattern not in self._callbacks:
            self._callbacks[topic_pattern] = []
        self._callbacks[topic_pattern].append(callback)

    def publish(self, topic, payload, qos=0, retain=False):
        if not self.connected:
            logger.warning(f"Not connected! Cannot publish to {topic}")
            return False
        try:
            if isinstance(payload, dict):
                message = json.dumps(payload)
            else:
                message = str(payload)
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Publish error: {e}")
            return False

    def publish_ac_control(self, action, temperature=None, fan_speed=None):
        payload = {"action": action}
        if temperature is not None:
            payload["temperature"] = temperature
        if fan_speed is not None:
            payload["fan_speed"] = fan_speed
        return self.publish("smartroom/ac/control", payload)

    def publish_lamp_control(self, brightness=None, action=None):
        payload = {}
        if brightness is not None:
            payload["brightness"] = brightness
        if action is not None:
            payload["action"] = action
        return self.publish("smartroom/lamp/control", payload)

    def publish_ir_learn_command(self, target):
        return self.publish("smartroom/ac/ir_learn_cmd", {
            "command": "start_learn", "target": target
        })

    @staticmethod
    def _topic_matches(pattern, topic):
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")
        for i, p in enumerate(pattern_parts):
            if p == "#":
                return True
            if i >= len(topic_parts):
                return False
            if p == "+":
                continue
            if p != topic_parts[i]:
                return False
        return len(pattern_parts) == len(topic_parts)

    def get_status(self):
        return {
            "connected": self.connected,
            "broker": self.broker,
            "port": self.port,
            "client_id": self.client_id,
            "reconnect_count": self._reconnect_count
        }