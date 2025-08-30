#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>

// RFID
#define SS_PIN 9
#define RST_PIN 8

// Пины устройств
#define BUZZER_PIN 7
#define RELAY_PIN 12
#define ADDITIONAL_RELAY_PIN 5

// Кнопки вместо датчиков
const int buttonPins[] = {22, 24, 26, 28, 30, 32, 34}; // 7 кнопок
//const int buttonPins[] = {2, 4, 6, 7, 8, 12, 13}; // 7 кнопок uno test

// Температура
#define DHTPIN 6
#define DHTTYPE DHT22
#define TEMPERATURE_CHECK_INTERVAL 10000
#define TEMPERATURE_THRESHOLD 28.0

// Интервалы
#define CHECK_INTERVAL 5000
#define RELAY_DURATION 3000

// Объекты
MFRC522 mfrc522(SS_PIN, RST_PIN);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastCheckTime = 0;
unsigned long lastTemperatureCheckTime = 0;
unsigned long toneStartTime = 0;
//unsigned long relayTimer = 0;

bool relayState = HIGH;
bool isTonePlaying = false;
//bool autoRelayOff = false;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  dht.begin();

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(ADDITIONAL_RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(ADDITIONAL_RELAY_PIN, HIGH);

  for (int i = 0; i < 7; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP); // Кнопки с внутренней подтяжкой
  }

  Serial.println("System Initialized with Buttons.");
}

void loop() {
  unsigned long currentTime = millis();

  // Обработка команд от сервера
  if (Serial.available() > 0) {
    processSerialCommand();
    delay(2);
  }

  // Проверка RFID
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    handleRFID();
    // autoRelayOff = true;
    // relayTimer = millis();
  }

  // // Автоматическое отключение реле
  // if (autoRelayOff && millis() - relayTimer >= RELAY_DURATION) {
  //   relayState = HIGH;
  //   digitalWrite(RELAY_PIN, HIGH);
  //   autoRelayOff = false;
  // }

  // Проверка кнопок
  if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
    lastCheckTime = currentTime;
    checkMotionSensors(); // теперь проверяет кнопки
  }

  // Проверка температуры
  if (currentTime - lastTemperatureCheckTime >= TEMPERATURE_CHECK_INTERVAL) {
    lastTemperatureCheckTime = currentTime;
    checkTemperature();
  }

  // Выключение зуммера
  if (isTonePlaying && currentTime - toneStartTime >= 50) {
    noTone(BUZZER_PIN);
    isTonePlaying = false;
  }
}

// 📌 Считывает UID карты RFID
void handleRFID() {
  uint32_t uid = 0;
  for (int i = mfrc522.uid.size - 1; i >= 0; i--) {
    uid = (uid << 8) | mfrc522.uid.uidByte[i];
  }

  char formattedUID[11];
  sprintf(formattedUID, "%010lu", uid);

  Serial.print("UID:");
  Serial.println(formattedUID);

  tone(BUZZER_PIN, 1000);
  isTonePlaying = true;
  toneStartTime = millis();

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

// 📌 Обработка команд с Python-сервера
void processSerialCommand() {
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "0" && relayState != LOW) {
    relayState = LOW;
    //relayTimer = millis();
    //autoRelayOff = true;
    digitalWrite(RELAY_PIN, LOW);
  } else if (command == "1" && relayState != HIGH) {
    relayState = HIGH;
    digitalWrite(RELAY_PIN, HIGH);
  } else {
    Serial.println("Unknown command: " + command);
  }

  digitalWrite(RELAY_PIN, relayState);
}

// 📌 Проверка состояния кнопок (вместо датчиков)
void checkMotionSensors() {
  int detected = 0;
  for (int i = 0; i < 7; i++) {
    if (digitalRead(buttonPins[i]) == LOW) { // Кнопка нажата
      detected++;
    }
  }
  Serial.println(String(detected) + "/7");
}

// 📌 Проверка температуры и управление дополнительным реле
void checkTemperature() {
  float temperature = dht.readTemperature();
  if (isnan(temperature)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

  Serial.print(F("Temperature: "));
  Serial.println(temperature);

  digitalWrite(ADDITIONAL_RELAY_PIN, temperature >= TEMPERATURE_THRESHOLD ? LOW : HIGH);
  if (temperature >= TEMPERATURE_THRESHOLD) {
    Serial.println(F("Temperature too high! Additional relay turned off."));
  }
}
