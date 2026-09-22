# dashboard/app.py
from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import json
import threading

app = Flask(__name__)

# Global state
dashboard_state = {
    "ac": {}, "lamp": {}, "camera": {},
    "ac_optimization": {}, "lamp_optimization": {}
}

def mqtt_listener():
    def on_message(client, userdata, msg):
        global dashboard_state
        try:
            data = json.loads(msg.payload.decode())
            if "dashboard/state" in msg.topic:
                dashboard_state.update(data)
        except:
            pass
    
    client = mqtt.Client("Dashboard")
    client.on_message = on_message
    client.connect("localhost", 1883)
    client.subscribe("smartroom/#")
    client.loop_forever()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    return jsonify(dashboard_state)

@app.route('/api/ac/control', methods=['POST'])
def control_ac():
    data = request.json
    client = mqtt.Client("DashboardControl")
    client.connect("localhost", 1883)
    client.publish("smartroom/ac/control", json.dumps(data))
    client.disconnect()
    return jsonify({"status": "sent"})

@app.route('/api/lamp/control', methods=['POST'])
def control_lamp():
    data = request.json
    client = mqtt.Client("DashboardControl")
    client.connect("localhost", 1883)
    client.publish("smartroom/lamp/control", json.dumps(data))
    client.disconnect()
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    t = threading.Thread(target=mqtt_listener, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=True)