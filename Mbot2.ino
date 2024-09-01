#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiServer.h>

// Pin definitions for motor 1
const int enA = 9;
const int in1 = 8;
const int in2 = 7;

// Pin definitions for motor 2
const int enB = 6;
const int in3 = 4;
const int in4 = 5;

// Pin definitions for encoder 1
const int encoderA1 = 2;
const int encoderB1 = 3;

// Pin definitions for encoder 2
const int encoderA2 = 12;
const int encoderB2 = 13;

volatile long encoderCount1 = 0;
volatile long encoderCount2 = 0;
long targetCount1 = 0;
long targetCount2 = 0;

// WiFi settings
const char* ssid = "ZTE_2.4G_K7HknT";
const char* password = "Defrag2022";
WiFiServer server(80);

// Constants for scaling and mapping
const float scalingFactor = 10.0; 
const float wheelRadius = 0.05; // meters
const float wheelBase = 0.15;   // meters

// Robot's current position and orientation
float x = 0.0; // Robot's current x position
float y = 0.0; // Robot's current y position
float theta = 0.0; // Robot's current orientation

void setup() {
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

  attachInterrupt(digitalPinToInterrupt(encoderA1), countEncoder1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoderB1), countEncoder1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoderA2), countEncoder2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoderB2), countEncoder2, CHANGE);

  Serial.begin(9600);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    String request = client.readStringUntil('\r');
    client.flush();

    if (request.startsWith("GET /setTarget")) {
      int xIndex = request.indexOf("x=") + 2;
      int yIndex = request.indexOf("&y=") + 3;
      int xEndIndex = request.indexOf("&", xIndex);
      int yEndIndex = request.indexOf(" ", yIndex);

      String xStr = request.substring(xIndex, xEndIndex);
      String yStr = request.substring(yIndex, yEndIndex);

      long x = xStr.toInt();
      long y = yStr.toInt();

      targetCount1 = x * scalingFactor;
      targetCount2 = y * scalingFactor;
      encoderCount1 = 0;
      encoderCount2 = 0;
    } else if (request.startsWith("GET /stop")) {
      targetCount1 = encoderCount1;
      targetCount2 = encoderCount2;
    } else if (request.startsWith("GET /getPWM")) {
      int pwmLeft = analogRead(A0);  
      int pwmRight = analogRead(A1); 

      String response = "PWM Left: " + String(pwmLeft) + "<br>PWM Right: " + String(pwmRight);
      client.print("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n");
      client.print(response);
      client.stop();
      return;
    }

    controlMotors();

    client.print("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n");
    client.print("Target Count Motor 1: ");
    client.print(targetCount1);
    client.print("<br>Target Count Motor 2: ");
    client.print(targetCount2);
    client.stop();
  }

  delay(100);
}

void countEncoder1() {
  encoderCount1++;
}

void countEncoder2() {
  encoderCount2++;
}

// Function to calculate forward kinematics
void forwardKinematics(float &x, float &y, float &theta) {
  float dLeft = (encoderCount1 / scalingFactor) * (2 * PI * wheelRadius);
  float dRight = (encoderCount2 / scalingFactor) * (2 * PI * wheelRadius);

  float dCenter = (dLeft + dRight) / 2.0;
  theta += (dRight - dLeft) / wheelBase;
  x += dCenter * cos(theta);
  y += dCenter * sin(theta);
}

// Function to calculate inverse kinematics
void inverseKinematics(float targetX, float targetY, float targetTheta, long &targetCount1, long &targetCount2) {
  float dx = targetX - x; // current x position
  float dy = targetY - y; // current y position
  float dTheta = targetTheta - theta; // desired orientation

  float dCenter = sqrt(dx * dx + dy * dy);
  float dLeft = dCenter - (dTheta * wheelBase / 2.0);
  float dRight = dCenter + (dTheta * wheelBase / 2.0);

  targetCount1 = (dLeft / (2 * PI * wheelRadius)) * scalingFactor;
  targetCount2 = (dRight / (2 * PI * wheelRadius)) * scalingFactor;
}

void controlMotors() {
  long error1 = targetCount1 - encoderCount1;
  long error2 = targetCount2 - encoderCount2;

  int motorSpeed1 = constrain(error1, -255, 255);
  int motorSpeed2 = constrain(error2, -255, 255);

  if (abs(error1) <= 5) {
    motorSpeed1 = 0;
  }
  if (abs(error2) <= 5) {
    motorSpeed2 = 0;
  }

  if (motorSpeed1 != 0) {
    if (motorSpeed1 > 0) {
      digitalWrite(in1, HIGH);
      digitalWrite(in2, LOW);
    } else {
      digitalWrite(in1, LOW);
      digitalWrite(in2, HIGH);
    }
    analogWrite(enA, abs(motorSpeed1));
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    analogWrite(enA, 0);
  }

  if (motorSpeed2 != 0) {
    if (motorSpeed2 > 0) {
      digitalWrite(in3, HIGH);
      digitalWrite(in4, LOW);
    } else {
      digitalWrite(in3, LOW);
      digitalWrite(in4, HIGH);
    }
    analogWrite(enB, abs(motorSpeed2));
  } else {
    digitalWrite(in3, LOW);
    digitalWrite(in4, LOW);
    analogWrite(enB, 0);
  }
}
