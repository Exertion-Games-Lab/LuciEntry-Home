#include <SoftwareSerial.h> //Included SoftwareSerial Library
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>

// ---------- DEVICE 6 ---------- //

// ESP8266 Pins used
#define PWMControl 14
#define IN1 12
#define IN2 13
const int LEDPower = 4;
const int LEDWiFi = 0;
const int LEDEmergency = 2;
const int Relay = 5;

// Local Variables
bool emergencyState = false;
bool connected = false;
int ID = 6; 
#define ChangeGVSDirectionInterval 500

// WIFI Details
const char* SSID = "The boss";
const char* PASSWORD = "37a472adae";
const String IP_ADDRESS = "192.168.1.118";
const String URL = "http://" + IP_ADDRESS + ":8080/";

// enums 
enum InstructionCodes {
    TurnOnLED = 1,
    TurnOffLED = 2,
    PlaySound = 3,
    StopSound = 4,
    IncreaseVibration = 5,
    DecreaseVibration = 6,
    LiftLegs = 7,
    LowerLegs = 8,
    LiftHead = 9,
    LowerHead = 10,
    Wait = 11,
    TurnOnBlueLED = 12,
};

// structs
struct Instruction {
    int code;
    JsonObject payload;
};

struct Command {
    String name;
    Instruction* instructions;
    int noOfInstructions;
};
// empty command
Command EmptyCommand;

void setup() {
    // Serial Monitor Startup
    Serial.begin(9600);

    // Setting Indicators LED pins and Relays to OUTPUT
    pinMode(LEDPower, OUTPUT);
    pinMode(LEDWiFi, OUTPUT);
    pinMode(LEDEmergency, OUTPUT);
    pinMode(Relay, OUTPUT);

    // Set Pins for IC as OUTPUT
    pinMode(PWMControl, OUTPUT);
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    

    // Setup wifi 
    WiFi.mode(WIFI_STA);  // SETS TO STATION MODE!
    connect();

    // Initialise Device
    analogWrite(PWMControl, 0);
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);

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

void ReadInput()
{
  while(Serial.available()>0)
  {
    int serialRead = Serial.parseInt();
    analogWrite(PWMControl, serialRead);
    Serial.println("I read "+String(serialRead));
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
        case TurnOnLED:
            Turn(true);
            break;
        case TurnOffLED:
            Turn(false);
            break;
        case Wait:
            ChangeGVSDirection(instruction.payload["millis"]);
            break;
        default:
            Serial.println("Instruction code does not exist");
    }
}


void wait(int time){
  //delay(time);
  Serial.println("Wait");
}


void ChangeGVSDirection(int time)
{
  int cnt=0;
  while(cnt<time)
  {
    
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    Serial.println("CW");
    delay(ChangeGVSDirectionInterval);
    cnt+=ChangeGVSDirectionInterval;
    //ReadInput();
    
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    Serial.println("CCW");
    delay(ChangeGVSDirectionInterval);
    cnt+=ChangeGVSDirectionInterval;
  }
  
}

void Turn(bool active)
{
  if(active)
  {
    analogWrite(PWMControl, 255);
    Serial.println("Turn on");
  }
  else
  {
    analogWrite(PWMControl, 0);
    Serial.println("Turn off");
  }
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