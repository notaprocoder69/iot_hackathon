#include <ESP8266WiFi.h>

const char* ssid = "Redmi";  // WiFi SSID
const char* password = "12345678";  // WiFi Password

WiFiClient client;
const char* server_ip = "192.168.47.100";  // Pico W Static IP Address
const uint16_t server_port = 8080;  // Server Port

const int trigPin = D1;  // TRIG pin of HC-SR04
const int echoPin = D2;  // ECHO pin of HC-SR04

long duration;
float distance;

void setup() {
  // Add a delay before starting serial to ensure proper initialization
  delay(1000);
  
  Serial.begin(115200);
  delay(100);  // Short delay to ensure serial connection is properly initialized
  Serial.println("Starting...");

  // Connect to WiFi
  Serial.println("Attempting to connect to WiFi...");
  WiFi.begin(ssid, password);

  // Wait for WiFi connection
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Attempt "); 
    Serial.print(attempts); 
    Serial.println(": Trying to connect...");
    delay(1000);
    attempts++;
    if (attempts >= 20) {  // Timeout after 20 attempts (adjustable)
      Serial.println("Failed to connect to WiFi after multiple attempts.");
      return;
    }
  }

  Serial.println("Connected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize pins for Ultrasonic sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

float getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;
  return distance;
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, attempting to reconnect...");
    WiFi.begin(ssid, password);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.println("Reconnecting to WiFi...");
      attempts++;
      if (attempts >= 20) {
        Serial.println("Failed to reconnect to WiFi.");
        return;
      }
    }
  }

  // Get the ultrasonic sensor distance
  float distance = getDistance();
  Serial.print("Distance measured: ");
  Serial.print(distance);
  Serial.println(" cm");

  // Get the MAC address of the ESP8266
  String macAddress = WiFi.macAddress();
  Serial.print("MAC Address: ");
  Serial.println(macAddress);

  // Prepare the data to be sent
  String data = "Distance:" + String(distance) + "cm, MAC:" + macAddress;

  Serial.println("Attempting to connect to server...");

  // Attempt to connect to the server
  if (client.connect(server_ip, server_port)) {
    Serial.println("Connected to server");
    client.print(data);  // Send the data
    Serial.println("Data sent: " + data);
    client.stop();  // Close the connection
  } else {
    Serial.println("Failed to connect to server");
  }

  delay(3000);  // Delay before sending data again
}
