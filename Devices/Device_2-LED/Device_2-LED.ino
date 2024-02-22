#include <SoftwareSerial.h> // Included SoftwareSerial Library
#include <ArduinoJson.h>
#include <Adafruit_NeoPixel.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>

// ---------- DEVICE 2 ---------- //

// ESP8266 Pins used
#define LED_PIN 5
const int LEDPower = 4;
const int LEDWiFi = 0;
const int LEDEmergency = 2;
const int Relay = 14;

// Local Variables
bool emergencyState = false;
bool connected = false;
int ID = 2;
#define NUM_LEDS 28

// LED Strip Initialization
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// WIFI Details
const char* SSID = "HUAWEI Nat 10 Pro";
const char* PASSWORD = "O6Z12D38";
const String IP_ADDRESS = "192.168.43.47";
const String URL = "http://" + IP_ADDRESS + ":8080/";

// Enums
enum InstructionCodes {
    TurnOnLED = 1,
    TurnOffLED = 2,
    Wait = 11,
};

// Structs
struct Instruction {
    int code;
    JsonObject payload;
};

struct Command {
    String name;
    Instruction* instructions;
    int noOfInstructions;
    // New component
    int currentInstructionNum; // To trace which instruction to execute next
};

// Empty command
Command currentCommand;
Command EmptyCommand;

void setup() {
    // Serial Monitor Startup
    Serial.begin(9600);

    // Setting Indicators LED pins and Relays to OUTPUT
    pinMode(LEDPower, OUTPUT);
    pinMode(LEDWiFi, OUTPUT);
    pinMode(LEDEmergency, OUTPUT);
    pinMode(Relay, OUTPUT);

    // Setup LED Strip
    strip.begin();            // INITIALIZE NeoPixel strip object (REQUIRED)
    strip.show();             // Turn OFF all pixels ASAP

    // Setup WiFi
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
    if (!emergencyState) {
      digitalWrite(LEDEmergency, LOW);
      digitalWrite(Relay, LOW);
      if(currentCommand.noOfInstructions == 0){
        currentCommand = fetchNextCommand();
      }
      else{
        executeCommand();
      }
    } else {
        digitalWrite(LEDEmergency, HIGH);
        digitalWrite(Relay, HIGH);
        currentCommand = EmptyCommand;
    }
}

void connect() {
    // Connect to Wi-Fi network with SSID and password
    WiFi.begin(SSID, PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(1000);
    }

    connected = true;

    Serial.println("Connected!");
}

Command fetchNextCommand() {
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
        command.currentInstructionNum = 0; // Initialize current instruction number
    } else {
        Serial.print("Failed to get command: ");
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
    command.instructions = new Instruction[jsonInstructions.size()];
    command.noOfInstructions = jsonInstructions.size();

    Serial.println("Command: " + command.name);

    int i = 0;
    for (JsonObject jsonInstruction : jsonInstructions) {
        command.instructions[i].code = jsonInstruction["code"].as<int>();
        command.instructions[i].payload = jsonInstruction["payload"].as<JsonObject>();
        i++;
    }

    return command;
}

void executeCommand() {
    if (currentCommand.currentInstructionNum < currentCommand.noOfInstructions) {
        executeInstruction(currentCommand.instructions[currentCommand.currentInstructionNum]);
    } else {
        // Command finished, release the command
        currentCommand = EmptyCommand;
    }
}

void executeInstruction(Instruction instruction) {
    switch (instruction.code) {
        case TurnOnLED:
            turnOnLED(instruction.payload["brightness"].as<int>(), instruction.payload["colour"]["r"].as<int>(), instruction.payload["colour"]["g"].as<int>(), instruction.payload["colour"]["b"].as<int>());
            break;
        case TurnOffLED:
            turnOffLED();
            break;
        case Wait:
            wait(instruction.payload["millis"]);
            break;
        default:
            Serial.println("Instruction code does not exist");
    }
}

// Functionality 
void turnOnLED(int brightness, int red, int green, int blue) {
    Serial.println("Turn on led");
    strip.setBrightness(brightness);  // Set BRIGHTNESS to about 1/5 (max = 255)
    for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(red, green, blue));   // Set pixel's color (in RAM)
    }
    strip.show();  
    currentCommand.currentInstructionNum++; //remember to add the number after the completion of the instruction 
}

void turnOffLED() {
    Serial.println("Turn off led");
    strip.clear();
    strip.show();
    currentCommand.currentInstructionNum++; //remember to add the number after the completion of the instruction 
}

// Function to wait for a specified duration without blocking the loop
void wait(unsigned long time) {
    static unsigned long waitStartTime = 0;
    static unsigned long waitDuration = 0;

    if (waitDuration == 0) {
        // Start waiting
        waitStartTime = millis();
        waitDuration = time;
    } else {
        // Continue waiting
        unsigned long elapsedTime = millis() - waitStartTime;
        if (elapsedTime >= waitDuration) {
            // Finish waiting
            waitDuration = 0;
            currentCommand.currentInstructionNum++; // Move to the next instruction
        }
    }
}

// Function to fetch the emergency state from the server
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
