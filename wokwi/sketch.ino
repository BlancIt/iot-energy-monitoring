#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* MQTT_SERVER = "dog.lmq.cloudamqp.com";
const int MQTT_PORT = 8883;
const char* MQTT_USER = "tdyrvlts:tdyrvlts";
const char* MQTT_PASS = "YOUR_REAL_PASSWORD";
const char* MQTT_TOPIC = "iot/telemetry";

WiFiClientSecure wifiClient;
PubSubClient client(wifiClient);

String deviceId = "esp32-device-001";

void connectWifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect(deviceId.c_str(), MQTT_USER, MQTT_PASS)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

float randomFloat(float minVal, float maxVal) {
  return minVal + ((float)random(0, 1000) / 1000.0) * (maxVal - minVal);
}

void publishTelemetry() {
  StaticJsonDocument<256> doc;

  float voltage = randomFloat(210.0, 240.0);
  float current = randomFloat(0.5, 15.0);
  float pf = randomFloat(0.70, 1.00);
  float power = voltage * current * pf;

  doc["device_id"] = deviceId;
  doc["voltage"] = voltage;
  doc["current"] = current;
  doc["power"] = power;
  doc["energy"] = randomFloat(0.1, 50.0);
  doc["power_factor"] = pf;
  doc["frequency"] = randomFloat(49.8, 50.2);

  char buffer[256];
  serializeJson(doc, buffer);

  bool ok = client.publish(MQTT_TOPIC, buffer);
  if (ok) {
    Serial.print("[PUB] ");
    Serial.println(buffer);
  } else {
    Serial.println("[ERR] publish failed");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  connectWifi();

  // Workshop/demo shortcut: skip certificate validation.
  // Good for demo use, not for production.
  wifiClient.setInsecure();

  client.setServer(MQTT_SERVER, MQTT_PORT);

  randomSeed(micros());

  connectMQTT();
}

void loop() {
  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  static unsigned long lastPublish = 0;
  if (millis() - lastPublish >= 5000) {
    lastPublish = millis();
    publishTelemetry();
  }
}