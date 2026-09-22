import cv2
import numpy as np
import urllib.request
import os

# Download YOLO files
yolo_dir = 'yolo'
os.makedirs(yolo_dir, exist_ok=True)

weights = f'{yolo_dir}/yolov3-tiny.weights'
config = f'{yolo_dir}/yolov3-tiny.cfg'
names = f'{yolo_dir}/coco.names'

if not os.path.exists(weights):
    print("Downloading YOLO weights...")
    urllib.request.urlretrieve('https://pjreddie.com/media/files/yolov3-tiny.weights', weights)

if not os.path.exists(config):
    print("Downloading YOLO config...")
    urllib.request.urlretrieve('https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg', config)

if not os.path.exists(names):
    print("Downloading COCO names...")
    urllib.request.urlretrieve('https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names', names)

# Load YOLO
print("Loading YOLO...")
net = cv2.dnn.readNet(weights, config)
print("✅ YOLO loaded successfully!")

# Test camera
cam = cv2.VideoCapture(0)
if cam.isOpened():
    print("✅ Camera OK")
    ret, frame = cam.read()
    if ret:
        print(f"✅ Frame captured: {frame.shape}")
        
        # Test detection
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        layer_names = net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
        outs = net.forward(output_layers)
        print(f"✅ YOLO detection output: {len(outs)} layers")
        
        # Check for person detections
        person_count = 0
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if class_id == 0 and confidence > 0.5:  # class_id 0 = person
                    person_count += 1
        
        print(f"✅ Persons detected: {person_count}")
    cam.release()
else:
    print("❌ Camera failed to open")