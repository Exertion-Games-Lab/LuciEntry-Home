#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>

// ---------- DEVICE 4 ---------- //

// ESP8266 Pins used
#define PUMP 5
const int LEDPower = 4;
const int LEDWiFi = 0;
const int LEDEmergency = 2;
const int Relay = 14;

// Local Variables
bool emergencyState = false;
bool connected = false;
int ID = 4;

// WIFI Details
const char* SSID = "HUAWEI Nat 10 Pro";
const char* PASSWORD = "O6Z12D38";
const String IP_ADDRESS = "192.168.43.47";
const String URL = "http://" + IP_ADDRESS + ":8080/";

enum InstructionCodes {
    TurnOn = 1,
    TurnOff = 2,
    Wait = 11,
};

// structs
struct Instruction {
    int code;
    JsonObject payload;
    int payloadItems;
};

struct Command {
    String name;
    Instruction* instructions;
    int noOfInstructions;
};
// empty command
Command EmptyCommand;


void setup() {
    // Serial S Begin at 9600 Baud
  Serial.begin(9600);

  // Setting Indicators LED pins and Relays to OUTPUT
  pinMode(LEDPower, OUTPUT);
  pinMode(LEDWiFi, OUTPUT);
  pinMode(LEDEmergency, OUTPUT);
  pinMode(Relay, OUTPUT);

  // Setting Pump pin to OUTPUT
  pinMode(PUMP, OUTPUT);

  // Setup wifi
  WiFi.mode(WIFI_STA);  // SETS TO STATION MODE!
  connect();

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
      Command command = fetchNextCommand();
      executeCommand(command);
    } else {
      digitalWrite(LEDEmergency, HIGH);
      digitalWrite(Relay, HIGH);
    }

    delay(2000);
}

void Enable(bool active)
{
  if(active)
  {
    digitalWrite(PUMP, HIGH);
  }
  else
  {
    digitalWrite(PUMP, LOW);
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

Command fetchNextCommand(){
    Command command = EmptyCommand;

    Serial.println("Making http request for next command\n");

    WiFiClient client;
    HTTPClient http;

    client.connect(IP_ADDRESS, 8080);

    String path = URL + "command/" + String(ID);

    http.begin(client, path.c_str());

    // Send HTTP GET request
    int httpResponseCode = http.GET();

    if (httpResponseCode == 200) {
        String payload = http.getString();
        command = jsonObjectToCommand(payload);
    } else {
        Serial.print("Failed to get: ");
        Serial.println(httpResponseCode);
    }
    // Free resources
    http.end();

    return command;
}

Command jsonObjectToCommand(String payload) {
    DynamicJsonDocument doc(5200);
    DeserializationError error = deserializeJson(doc, payload);

    if (error) {
      Serial.println("Failed to read command");
      Serial.println(error.c_str());
      return EmptyCommand;
    }

    Command command;
    command.name = doc["command"]["name"].as<String>();
    JsonArray jsonInstructions = doc["command"]["instructions"].as<JsonArray>();
    command.noOfInstructions = jsonInstructions.size();
    command.instructions = new Instruction[command.noOfInstructions];

    Serial.println("Command: " + command.name);

    int i = 0;
    for (JsonObject jsonInstruction : jsonInstructions) {
      command.instructions[i].code = jsonInstruction["code"].as<int>();
      command.instructions[i].payload = jsonInstruction["payload"].as<JsonObject>();
      i++;
    }

    return command;
}

void executeCommand(Command command){
    for (int i=0; i<command.noOfInstructions; i++){
        executeInstruction(command.instructions[i]);
    }
}

void executeInstruction(Instruction instruction){
    switch (instruction.code){
        case TurnOn:
            Enable(true);
            Serial.println("on");
            break;
        case TurnOff:
            Enable(false);
            Serial.println("off");
            break;
        case Wait:
            wait(instruction.payload["millis"]);
            break;
        default:
            Serial.println("Instruction code does not exist");
    }
}

void wait(int time){
  delay(time);
  Serial.println("Wait");
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
