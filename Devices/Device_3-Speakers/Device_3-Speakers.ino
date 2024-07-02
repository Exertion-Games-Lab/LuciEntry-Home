#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// ---------- DEVICE 3 ---------- //

// ESP8266 Pins used
const int Relay = 5;
const int LEDPower = 4;
const int LEDWiFi = 0;
const int LEDEmergency = 2;

// Local Variables
bool emergencyState = false;
bool connected = false;
int ID = 3;

// WIFI Details
// const char* SSID = "The boss";
// const char* PASSWORD = "37a472adae";
const char* SSID = "ORBI80";
const char* PASSWORD = "classychair864";
const String IP_ADDRESS = "192.168.1.41";
const String URL = "http://" + IP_ADDRESS + ":8080/";

void setup() {
    // Serial Monitor Startup
    Serial.begin(9600);

    // Setting Indicators LED pins and Relays to OUTPUT
    pinMode(LEDPower, OUTPUT);
    pinMode(LEDWiFi, OUTPUT);
    pinMode(LEDEmergency, OUTPUT);
    pinMode(Relay, OUTPUT);

    // Setup wifi 
    WiFi.mode(WIFI_STA);  // SETS TO STATION MODE!

    // Turn on Power indicator LED to indicate power on
    digitalWrite(LEDPower, HIGH);
}

void loop() {

    // Check WiFi connection and reflect to indicator light
    if (WiFi.status() == WL_CONNECTED) {
    // Keep the indicator LED on
    digitalWrite(LEDWiFi, HIGH);
    } else {
    // Turn off the indicator LED
    digitalWrite(LEDWiFi, LOW);
    connect();
    }

    emergencyState = fetchEmergencyState();
    if (emergencyState == false){
      digitalWrite(LEDEmergency, LOW);
      digitalWrite(Relay, LOW);
    } else {
      digitalWrite(LEDEmergency, HIGH);
      digitalWrite(Relay, HIGH);
    }

    delay(2000);
}

void connect(){
    // Connect to Wi-Fi network with SSID and password
    WiFi.begin(SSID, PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(1000);
    }

    connected = true;
    
    Serial.println("Connected!");
}

bool fetchEmergencyState() {
  bool emergencyState = false;

  WiFiClient client;
  HTTPClient http;

  client.connect(IP_ADDRESS, 8080);

  String path = URL + "emergencyState/";

  http.begin(client, path.c_str());

  // Send HTTP GET request
  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    emergencyState = doc["emergencyState"];
  } else {
    Serial.print("Failed to get emergency state: ");
    Serial.println(httpResponseCode);
  }

  http.end();

  return emergencyState;
}