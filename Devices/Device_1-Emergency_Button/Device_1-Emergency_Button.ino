#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// ---------- DEVICE 1 ---------- //

// ESP8266 Pins used
const int button = 5;
const int LEDPower = 4;
const int LEDWiFi = 0;
const int LEDEmergency = 2;

// Local Variables
int count = 0;
bool emergencyState = false;
bool connected = false;
int ID = 1; 
int temp;

//WiFi Details
// const char* SSID = "The boss";
// const char* PASSWORD = "37a472adae";
const char* SSID = "ORBI80";
const char* PASSWORD = "classychair864";
const String IP_ADDRESS = "192.168.1.41";
const String URL = "http://" + IP_ADDRESS + ":8080/";
const int PORT = 8080;

void setup() {
  // Serial Monitor Startup
  Serial.begin(9600);

  // Setting button as input
  pinMode(button, INPUT);

  // Setting Indicators LED pins to OUTPUT
  pinMode(LEDPower, OUTPUT);
  pinMode(LEDWiFi, OUTPUT);
  pinMode(LEDEmergency, OUTPUT);

  // Turn on Power indicator LED to indicate power on
  digitalWrite(LEDPower, HIGH);

  // Set WiFi to Station Mode##
  WiFi.mode(WIFI_STA);

}

void loop() {

  // Check WiFi connection and connect to WiFi and reflect to indicator light
  if (WiFi.status() == WL_CONNECTED) {
    // Keep the indicator LED on
    digitalWrite(LEDWiFi, HIGH);
  } else {
    // Turn off the indicator LED
    digitalWrite(LEDWiFi, LOW);
    connect();
  }

  // get button state
  temp = digitalRead(button);

  // get Server's emergency State
  emergencyState = fetchEmergencyState();

  if (temp == LOW && emergencyState == false){
    post(URL + "unblockCommands", IP_ADDRESS, PORT);
    digitalWrite(LEDEmergency, LOW);
    delay(100);
  }
  else if(temp == HIGH && emergencyState == false){
    sendEmergencyStateUpdate(true);
    post(URL + "blockCommands", IP_ADDRESS, PORT);
    digitalWrite(LEDEmergency, HIGH);
    delay(100);
  }
  else if (temp == LOW && emergencyState == true){
    emergencyState = false;
    sendEmergencyStateUpdate(false);
    post(URL + "unblockCommands", IP_ADDRESS, PORT);
    digitalWrite(LEDEmergency, LOW);
    delay(100);
  }
  else if (temp == HIGH && emergencyState == true){
    post(URL + "blockCommands", IP_ADDRESS, PORT);
    digitalWrite(LEDEmergency, HIGH);
    delay(100);
  }

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

void sendEmergencyStateUpdate(bool emergencyState) {
    WiFiClient client;
    HTTPClient http;

    String path = URL + "updateEmergencyState/1";  
    http.begin(client, path.c_str());
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload for the emergency state update
    String postData = "{\"emergencyState\":" + String(emergencyState) + "}";
    
    int httpCode = http.POST(postData);

    if (httpCode == 200) {
        Serial.println("Emergency state update sent successfully");
    } else {
        Serial.print("Failed to send emergency state update. HTTP code: ");
        Serial.println(httpCode);
    }

    http.end();
}

void post(String url, String IP, int port) {
    
    WiFiClient client;
    HTTPClient http;

    client.connect(IP, port);

    http.begin(client, url.c_str());

    // Specify content type for POST request
    http.addHeader("Content-Type", "application/json"); 

    // Send HTTP POST request with provided data
    int httpResponseCode = http.POST("");

    if (httpResponseCode == 200) {
        String payload = http.getString();
        Serial.println("POST successful");
    } else {
        Serial.print("Failed to post: ");
        Serial.println(httpResponseCode);
    }
    // Free resources
    http.end();

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