import paho.mqtt.client as mqtt
import json
from datetime import datetime
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
matt_topic_publish = "TeamC05Alarm"

class AlarmMQTT:
    def __init__(self):
        self.client = mqtt.Client("TeamC05AlarmPublisher")
        self.client.connect(mqtt_broker, mqtt_port)
        self.triggered_alarms = {}  # Track triggered alarms and their last notification time
    
    def publish_alarm(self, alarm_data):
    #Publish detailed alarm data to MQTT topic
        try:
            alarm_key = f"{alarm_data['node_id']}_{alarm_data['sensor']}"
            current_time = datetime.now()
            
            # Check if we need to send notification (first time or every 5 minutes)
            last_notification = self.triggered_alarms.get(alarm_key)
            needs_notification = (
                alarm_key not in self.triggered_alarms or
                (current_time - last_notification).total_seconds() >= 300
            )
            
            if needs_notification:
                payload = json.dumps({
                    "Alarm": "True",
                    "node_id": alarm_data['node_id'],
                    "location": alarm_data['location'],
                    "sensor": alarm_data['sensor'],
                    "value": float(alarm_data['value']),
                    "message": alarm_data['message'],
                    "timestamp": alarm_data['timestamp']
                })
                msg = 'Alarm:True'
                self.client.publish(matt_topic_publish, msg, qos=mqtt_qos)
                self.client.publish(matt_topic_publish, payload, qos=mqtt_qos)
                print(f"Published alarm to {matt_topic_publish}: {payload}")
                print(f"Published alarm to {matt_topic_publish}: {msg}")

                self.triggered_alarms[alarm_key] = current_time
                return True
            return False
        except Exception as e:
            print(f"Error publishing alarm: {str(e)}")
            return False
    
    def clear_triggered_alarm(self, alarm_key):
        """
        Clear a specific triggered alarm
        """
        self.triggered_alarms.pop(alarm_key, None)
    
    def clear_all_triggered_alarms(self):
        """
        Clear all triggered alarms
        """
        self.triggered_alarms.clear()

# Global instance
alarm_mqtt = AlarmMQTT()