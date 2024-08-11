#include <WiFi.h>

const char* ssid = "SSID";
const char* password = "Password";

IPAddress ip(192, 168, 1, 100);
WiFiServer server(80);

const int enA = 9;
const int in1 = 8;
const int in2 = 7;

const int enB = 6;
const int in3 = 4;
const int in4 = 5;

const int encoderA1 = 2;
const int encoderB1 = 3;

const int encoderA2 = 12;
const int encoderB2 = 13;

volatile long encoderCount1 = 0;
volatile long encoderCount2 = 0;
long targetCount1 = 0;
long targetCount2 = 0;

const float wheelRadius = 0.033;
const float wheelDistance = 0.16;
const int ticksPerRevolution = 20;
const float Kp = 0.5;

float x = 0.0;
float y = 0.0;
float theta = 0.0;

void setup() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    server.begin();
    Serial.print("Server started at ");
    Serial.println(WiFi.localIP());

    pinMode(enA, OUTPUT);
    pinMode(in1, OUTPUT);
    pinMode(in2, OUTPUT);
    pinMode(enB, OUTPUT);
    pinMode(in3, OUTPUT);
    pinMode(in4, OUTPUT);

    pinMode(encoderA1, INPUT);
    pinMode(encoderB1, INPUT);
    pinMode(encoderA2, INPUT);
    pinMode(encoderB2, INPUT);

    attachInterrupt(digitalPinToInterrupt(encoderA1), encoderISR1, CHANGE);
    attachInterrupt(digitalPinToInterrupt(encoderB1), encoderISR1, CHANGE);
    attachInterrupt(digitalPinToInterrupt(encoderA2), encoderISR2, CHANGE);
    attachInterrupt(digitalPinToInterrupt(encoderB2), encoderISR2, CHANGE);

    Serial.begin(9600);
}

void loop() {
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        int commaIndex = input.indexOf(',');
        if (commaIndex > 0) {
            targetCount1 = input.substring(0, commaIndex).toInt();
            targetCount2 = input.substring(commaIndex + 1).toInt();
            encoderCount1 = 0;
            encoderCount2 = 0;
        }
    }

    float V = (targetCount1 + targetCount2) / 2.0 * wheelRadius;
    float omega = (targetCount2 - targetCount1) / wheelDistance * wheelRadius;

    int motorSpeedLeft = V / wheelRadius - omega * wheelDistance / (2 * wheelRadius);
    int motorSpeedRight = V / wheelRadius + omega * wheelDistance / (2 * wheelRadius);

    if (motorSpeedLeft > 0) {
        digitalWrite(in1, HIGH);
        digitalWrite(in2, LOW);
        analogWrite(enA, abs(motorSpeedLeft) * 2);
    } else if (motorSpeedLeft < 0) {
        digitalWrite(in1, LOW);
        digitalWrite(in2, HIGH);
        analogWrite(enA, abs(motorSpeedLeft) * 2);
    } else {
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);
        analogWrite(enA, 0);
    }

    if (motorSpeedRight > 0) {
        digitalWrite(in3, HIGH);
        digitalWrite(in4, LOW);
        analogWrite(enB, abs(motorSpeedRight) * 2);
    } else if (motorSpeedRight < 0) {
        digitalWrite(in3, LOW);
        digitalWrite(in4, HIGH);
        analogWrite(enB, abs(motorSpeedRight) * 2);
    } else {
        digitalWrite(in3, LOW);
        digitalWrite(in4, LOW);
        analogWrite(enB, 0);
    }

    updatePosition();

    Serial.print("Encoder Count Motor 1: ");
    Serial.println(encoderCount1);
    Serial.print("Encoder Count Motor 2: ");
    Serial.println(encoderCount2);
    delay(100);
}

void updatePosition() {
    float deltaTheta = (encoderCount1 - encoderCount2) * (2 * PI * wheelRadius) / (ticksPerRevolution * wheelDistance);
    float deltaX = (encoderCount1 + encoderCount2) * (PI * wheelRadius) / ticksPerRevolution;

    theta += deltaTheta;
    x += deltaX * cos(theta);
    y += deltaX * sin(theta);

    encoderCount1 = 0;
    encoderCount2 = 0;
}

void encoderISR1() {
    int stateA1 = digitalRead(encoderA1);
    int stateB1 = digitalRead(encoderB1);

    if (stateA1 == stateB1) {
        encoderCount1++;
    } else {
        encoderCount1--;
    }
}

void encoderISR2() {
    int stateA2 = digitalRead(encoderA2);
    int stateB2 = digitalRead(encoderB2);

    if (stateA2 == stateB2) {
        encoderCount2++;
    } else {
        encoderCount2--;
    }
}
