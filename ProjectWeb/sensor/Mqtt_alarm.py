# Mqtt_alarm.py
import paho.mqtt.client as mqtt
import json

mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic_publish = "IC/TeamC05Alarmaaaa"

class AlarmMQTT:
    def __init__(self):
        self.client = mqtt.Client("TeamC05AlarmPublisher")
        self.client.connect(mqtt_broker, mqtt_port)
        self.alarm_sent = False  # Track if alarm has been sent
    
    def publish_alarm(self, alarm_triggered):
        """
        Publish simple alarm status to MQTT topic
        """
        try:
            if alarm_triggered and not self.alarm_sent:
                payload = json.dumps({"Alarm": "True"})
                self.client.publish(mqtt_topic_publish, payload, qos=mqtt_qos)
                print(f"Published alarm to {mqtt_topic_publish}: {payload}")
                self.alarm_sent = True
            elif not alarm_triggered:
                self.alarm_sent = False
        except Exception as e:
            print(f"Error publishing alarm: {str(e)}")

# Global instance to be used across the application
alarm_mqtt = AlarmMQTT()