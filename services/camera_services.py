# services/camera_service.py
import cv2
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import json
import threading
import time

class PersonDetector:
    def __init__(self, camera_index=0, broker="localhost"):
        # Gunakan YOLOv8 nano untuk kecepatan di Raspi
        self.model = YOLO("yolov8n.pt")
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.mqtt_client = mqtt.Client("CameraService")
        self.mqtt_client.connect(broker, 1883)
        
        self.person_count = 0
        self.running = False
    
    def detect(self):
        ret, frame = self.cap.read()
        if not ret:
            return 0
        
        # Inference
        results = self.model(frame, conf=0.5, classes=[0])  # class 0 = person
        
        # Hitung jumlah orang
        person_count = 0
        for r in results:
            person_count = len(r.boxes)
        
        return person_count
    
    def start_continuous(self, interval=5):
        """Deteksi setiap `interval` detik"""
        self.running = True
        
        def _loop():
            while self.running:
                count = self.detect()
                self.person_count = count
                
                payload = json.dumps({
                    "person_count": count,
                    "occupancy": count > 0,
                    "timestamp": time.time()
                })
                self.mqtt_client.publish("smartroom/camera/detection", payload)
                print(f"Persons detected: {count}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
    
    def stop(self):
        self.running = False
        self.cap.release()