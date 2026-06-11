#include <WiFi.h>
#include <WebServer.h>

#include "dashboard.h"


constexpr char WIFI_SSID[] = "demo";
constexpr char WIFI_PASSWORD[] = "1234567890";
constexpr char AP_SSID[] = "Shower-Monitor";
constexpr char AP_PASSWORD[] = "1234567890";
constexpr uint32_t USB_BAUD_RATE = 115200;
constexpr uint32_t UART_BAUD_RATE = 115200;

#if CONFIG_IDF_TARGET_ESP32C6
constexpr int UART_RX_PIN = 17;
constexpr int UART_TX_PIN = 16;
#else
constexpr int UART_RX_PIN = 16;
constexpr int UART_TX_PIN = 17;
#endif

constexpr size_t UART_LINE_CAPACITY = 96;
constexpr unsigned long WIFI_RETRY_INTERVAL_MS = 10000;
constexpr unsigned long IP_REPORT_INTERVAL_MS = 5000;

WebServer server(80);

char uartLine[UART_LINE_CAPACITY];
size_t uartLineLength = 0;
float latestX = 0.0f;
float latestY = 0.0f;
float latestZ = 0.0f;
uint32_t sampleSequence = 0;
unsigned long lastSampleTime = 0;
unsigned long lastWifiAttempt = 0;
unsigned long lastIpReport = 0;
bool sampleValid = false;
bool serverStarted = false;
String senderStatus = "waiting";

void handleDashboard() {
  server.sendHeader("Cache-Control", "no-store");
  server.send_P(200, "text/html", DASHBOARD_HTML);
}

void handleData() {
  char response[256];
  const unsigned long age =
      sampleValid ? millis() - lastSampleTime : 0;

  snprintf(response, sizeof(response),
           "{\"valid\":%s,\"sequence\":%lu,\"x\":%.6f,\"y\":%.6f,"
           "\"z\":%.6f,\"ageMs\":%lu,\"status\":\"%s\"}",
           sampleValid ? "true" : "false",
           static_cast<unsigned long>(sampleSequence),
           latestX, latestY, latestZ, age, senderStatus.c_str());

  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", response);
}

void configureWebServer() {
  server.on("/", HTTP_GET, handleDashboard);
  server.on("/data", HTTP_GET, handleData);
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not found");
  });
}

void startWebServer() {
  if (serverStarted) {
    return;
  }

  server.begin();
  serverStarted = true;
  Serial.println();
  Serial.println("Web dashboard started.");
  Serial.print("Fallback dashboard: http://");
  Serial.print(WiFi.softAPIP());
  Serial.println("/");
}

void maintainWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastWifiAttempt < WIFI_RETRY_INTERVAL_MS) {
    return;
  }

  lastWifiAttempt = now;
  Serial.println("Connecting to Wi-Fi SSID \"demo\"...");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void reportIpAddressPeriodically() {
  const unsigned long now = millis();
  if (now - lastIpReport < IP_REPORT_INTERVAL_MS) {
    return;
  }

  lastIpReport = now;

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Demo Wi-Fi dashboard: http://");
    Serial.print(WiFi.localIP());
    Serial.print("/ | ");
  } else {
    Serial.print("Demo Wi-Fi is not connected | ");
  }

  Serial.print("Fallback dashboard: http://");
  Serial.print(WiFi.softAPIP());
  Serial.println("/");
}

void processUartLine(char *line) {
  if (strncmp(line, "#STATUS,", 8) == 0) {
    if (strcmp(line + 8, "connected") == 0) {
      senderStatus = "connected";
    } else if (strcmp(line + 8, "disconnected") == 0) {
      senderStatus = "disconnected";
    } else {
      senderStatus = "waiting";
    }
    return;
  }

  float x;
  float y;
  float z;
  char trailing;

  if (sscanf(line, " %f , %f , %f %c", &x, &y, &z, &trailing) != 3) {
    return;
  }

  latestX = x;
  latestY = y;
  latestZ = z;
  lastSampleTime = millis();
  sampleSequence++;
  sampleValid = true;
}

void readUart() {
  while (Serial1.available()) {
    const char incoming = static_cast<char>(Serial1.read());

    if (incoming == '\r') {
      continue;
    }

    if (incoming == '\n') {
      if (uartLineLength > 0) {
        uartLine[uartLineLength] = '\0';
        processUartLine(uartLine);
        uartLineLength = 0;
      }
      continue;
    }

    if (uartLineLength < UART_LINE_CAPACITY - 1) {
      uartLine[uartLineLength++] = incoming;
    } else {
      uartLineLength = 0;
    }
  }
}

void setup() {
  Serial.begin(USB_BAUD_RATE);
  Serial1.begin(UART_BAUD_RATE, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

  Serial.println();
  Serial.println("Shower UART and web monitor starting.");
  Serial.printf("UART2: RX GPIO %d, TX GPIO %d, %lu baud\n",
                UART_RX_PIN, UART_TX_PIN,
                static_cast<unsigned long>(UART_BAUD_RATE));

  configureWebServer();
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.print("Fallback Wi-Fi started: ");
  Serial.println(AP_SSID);
  Serial.print("Fallback dashboard: http://");
  Serial.print(WiFi.softAPIP());
  Serial.println("/");
  startWebServer();

  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  lastWifiAttempt = millis();
  Serial.println("Connecting to Wi-Fi SSID \"demo\"...");
}

void loop() {
  readUart();
  maintainWifi();
  reportIpAddressPeriodically();

  if (serverStarted) {
    server.handleClient();
  }

  delay(1);
}
