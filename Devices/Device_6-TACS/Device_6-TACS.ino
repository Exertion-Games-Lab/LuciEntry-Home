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
int ID = 5; 
#define ChangeGVSDirectionInterval 500

// WIFI Details
const char* SSID = "S@M@NTH@";
const char* PASSWORD = "0437013417";
const String IP_ADDRESS = "192.168.0.146";
const String URL = "http://" + IP_ADDRESS + ":8080/";

// enums 
enum InstructionCodes {
    TurnOnLED = 1,
    TurnOffLED = 2,
    PlaySound = 3,
    StopSound = 4,
    StartTACS = 5,
    StopTACS = 6,
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
    DynamicJsonDocument* payload;
};

struct Command {
    String name;
    Instruction* instructions;
    int noOfInstructions;
    int currentInstructionNum;
};

// empty command
Command EmptyCommand;
Command* currentCommandPointer = nullptr;

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

    // Initialise Device
    analogWrite(PWMControl, 0);
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);

    // Turn on Power indicator LED to indicate power on
    digitalWrite(LEDPower, HIGH);
    EmptyCommand.name = "EmptyCommand";
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
        if (currentCommandPointer == nullptr || currentCommandPointer->noOfInstructions == 0) {
            currentCommandPointer = fetchNextCommand();
        } else {
            executeCommand();
        }
    } else {
        digitalWrite(LEDEmergency, HIGH);
        digitalWrite(Relay, HIGH);
        currentCommandPointer = &EmptyCommand;
    }
}

void ReadInput() {
    while (Serial.available() > 0) {
        int serialRead = Serial.parseInt();
        analogWrite(PWMControl, serialRead);
        Serial.println("I read " + String(serialRead));
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

Command* fetchNextCommand() {
    static unsigned long waitStartTime = 0;
    static unsigned long waitDuration = 0;

    if (waitDuration == 0) {
        waitStartTime = millis();
        waitDuration = 2000;
    } else {
        unsigned long elapsedTime = millis() - waitStartTime;
        if (elapsedTime < waitDuration) {
            return &EmptyCommand;
        } else {
            waitDuration = 0;
        }
    }

    Command* commandptr = &EmptyCommand;

    Serial.println("Making http request for next command");

    WiFiClient client;
    HTTPClient http;

    client.connect(IP_ADDRESS, 8080);

    String path = URL + "command/" + String(ID);

    http.begin(client, path.c_str());

    // Send HTTP GET request
    int httpResponseCode = http.GET();

    if (httpResponseCode == 200) {
        String payload = http.getString();
        commandptr = jsonObjectToCommand(payload);
        commandptr->currentInstructionNum = 0;
    } else {
        Serial.print("Failed to get: ");
        Serial.println(httpResponseCode);
    }
    // Free resources
    http.end();

    return commandptr;
}

Command* jsonObjectToCommand(String payload) {
    DynamicJsonDocument doc(5200);
    DeserializationError error = deserializeJson(doc, payload);

    if (error) {
        Serial.println("Failed to read command");
        Serial.println(error.c_str());
        return &EmptyCommand;
    }

    if (doc["command"]["name"].as<String>() == "null") {
        // Empty command, ignore
        return &EmptyCommand;
    }

    Command* commandptr = new Command;
    commandptr->name = doc["command"]["name"].as<String>();
    JsonArray jsonInstructions = doc["command"]["instructions"].as<JsonArray>();
    commandptr->instructions = new Instruction[jsonInstructions.size()];
    commandptr->noOfInstructions = jsonInstructions.size();
    
    Serial.println("Command: " + commandptr->name);
    int i = 0;
    for (JsonObject jsonInstruction : jsonInstructions) {
        commandptr->instructions[i].code = jsonInstruction["code"].as<int>();

        // Deep copy Json object
        commandptr->instructions[i].payload = new DynamicJsonDocument(1024);
        String serialized;
        serializeJson(jsonInstruction["payload"].as<JsonObject>(), serialized);
        // Deserialize the serialized string into the destination JsonObject
        DeserializationError error = deserializeJson(*(commandptr->instructions[i].payload), serialized);
        if (error) {
            Serial.print("Failed to parse JSON: ");
            Serial.println(error.c_str());
        }
        i++;
    }
    
    return commandptr;
}

void executeCommand() {
    if (currentCommandPointer->currentInstructionNum < currentCommandPointer->noOfInstructions) {
        executeInstruction(currentCommandPointer->instructions[currentCommandPointer->currentInstructionNum]);
    } else {
        // Command finished, release the command
        for (int i = 0; i < currentCommandPointer->noOfInstructions; i++) {
            delete currentCommandPointer->instructions[i].payload;
        }
        delete[] currentCommandPointer->instructions;
        delete currentCommandPointer;

        currentCommandPointer = &EmptyCommand;
    }
}

void executeInstruction(Instruction instruction) {
    switch (instruction.code) {
        case StartTACS:
            Turn(true, (*instruction.payload)["intensity"].as<int>(), (*instruction.payload)["frequency"].as<int>());
            break;
        case StopTACS:
            Turn(false, 0, 0);
            break;
        case Wait:
            ChangeGVSDirection((*instruction.payload)["millis"].as<int>(), (*instruction.payload)["frequency"].as<int>());
            break;
        default:
            Serial.println("Instruction code does not exist");
    }
}

void ChangeGVSDirection(int time, int frequency) {
    static unsigned long waitStartTime = 0;
    static unsigned long waitDuration = 0;

    if (waitDuration == 0) {
        waitStartTime = millis();
        waitDuration = time;
    } else {
        unsigned long elapsedTime = millis() - waitStartTime;
        
        if (elapsedTime >= waitDuration) {
            waitDuration = 0;
            currentCommandPointer->currentInstructionNum++;
        } else {
            elapsedTime = millis() - waitStartTime;
            int currentGVSNum = elapsedTime * frequency * 2 / 1000;
            if (currentGVSNum % 2 == 0) {
                digitalWrite(IN1, HIGH);
                digitalWrite(IN2, LOW);
            } else {
                digitalWrite(IN1, LOW);
                digitalWrite(IN2, HIGH);
            }
        }
    }
}

void Turn(bool active, int intensity, int frequency) {
    if (active) {
        analogWrite(PWMControl, intensity);
        Serial.println("Turn on, Intensity = " + String(intensity) + ", Frequency = " + String(frequency));
    } else {
        analogWrite(PWMControl, 0);
        Serial.println("Turn off");
    }
    currentCommandPointer->currentInstructionNum++; // Move to the next instruction
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