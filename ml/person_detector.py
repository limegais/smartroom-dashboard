import numpy as np
import json
import time
import threading
import logging

logger = logging.getLogger("PersonDetector")


class PersonDetector:
    def __init__(self, camera_index=0, mqtt_handler=None):
        self.camera_index = camera_index
        self.mqtt_handler = mqtt_handler
        self.person_count = 0
        self.occupancy = False
        self.last_detection_time = 0
        self.bboxes = []
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
        self.cap = None
        self.model = None
        self._model_loaded = False
        self.total_detections = 0
        self.total_frames = 0
        self.avg_inference_ms = 0
        self._occupancy_history = []
        self._history_size = 5

    def load_model(self):
        try:
            from ultralytics import YOLO
            import cv2
            logger.info("Loading YOLO model: yolov8n.pt")
            self.model = YOLO("yolov8n.pt")
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            self.model(dummy, verbose=False)
            self._model_loaded = True
            logger.info("YOLO model loaded!")
            return True
        except ImportError:
            logger.error("ultralytics or opencv not installed!")
            return False
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    def open_camera(self):
        try:
            import cv2
            logger.info(f"Opening camera (index={self.camera_index})...")
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error("Failed to open camera!")
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 10)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info("Camera opened")
            return True
        except ImportError:
            logger.error("opencv not installed!")
            return False
        except Exception as e:
            logger.error(f"Camera error: {e}")
            return False

    def detect_once(self):
        if not self._model_loaded or self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None
        start_time = time.time()
        results = self.model(frame, conf=0.5, classes=[0], verbose=False)
        inference_ms = (time.time() - start_time) * 1000
        bboxes = []
        person_count = 0
        for r in results:
            person_count = len(r.boxes)
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                bboxes.append({
                    "x1": int(x1), "y1": int(y1),
                    "x2": int(x2), "y2": int(y2),
                    "confidence": round(conf, 3)
                })
        self._occupancy_history.append(1 if person_count > 0 else 0)
        if len(self._occupancy_history) > self._history_size:
            self._occupancy_history.pop(0)
        avg = sum(self._occupancy_history) / len(self._occupancy_history)
        smooth_occupancy = avg >= 0.5
        with self._lock:
            self.person_count = person_count
            self.occupancy = smooth_occupancy
            self.bboxes = bboxes
            self.last_detection_time = time.time()
            self.total_frames += 1
            if person_count > 0:
                self.total_detections += 1
            self.avg_inference_ms = (
                (self.avg_inference_ms * (self.total_frames - 1) + inference_ms)
                / self.total_frames
            )
        return {
            "person_count": person_count,
            "occupancy": smooth_occupancy,
            "bboxes": bboxes,
            "inference_ms": round(inference_ms, 1),
            "timestamp": time.time()
        }

    def start_continuous(self, interval=5):
        if self.running:
            return False
        if not self._model_loaded:
            if not self.load_model():
                return False
        if self.cap is None or not self.cap.isOpened():
            if not self.open_camera():
                return False
        self.running = True

        def _loop():
            while self.running:
                try:
                    result = self.detect_once()
                    if result and self.mqtt_handler:
                        self.mqtt_handler.publish(
                            "smartroom/camera/detection",
                            {
                                "person_count": result["person_count"],
                                "occupancy": result["occupancy"],
                                "inference_ms": result["inference_ms"],
                                "timestamp": result["timestamp"]
                            }
                        )
                except Exception as e:
                    logger.error(f"Detection error: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        logger.info("Continuous detection started")
        return True

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Person detector stopped")

    def get_state(self):
        with self._lock:
            return {
                "person_count": self.person_count,
                "occupancy": self.occupancy,
                "running": self.running,
                "model_loaded": self._model_loaded,
                "total_frames": self.total_frames,
                "total_detections": self.total_detections,
                "avg_inference_ms": round(self.avg_inference_ms, 1),
                "detection_rate": (
                    round(self.total_detections / self.total_frames, 3)
                    if self.total_frames > 0 else 0
                )
            }