#include <ArduinoBLE.h>

// ArduinoBLE does not expose PHY selection through its public API.
#include <utility/ATT.h>
#include <utility/HCI.h>

constexpr char ACCELEROMETER_SERVICE_UUID[] =
    "7f510000-1b15-4f0d-8f53-7b2e95d4a101";
constexpr char ACCELEROMETER_CHARACTERISTIC_UUID[] =
    "7f510001-1b15-4f0d-8f53-7b2e95d4a101";
constexpr unsigned long UART_BAUD_RATE = 115200;

// Serial1 uses D1/TX and D0/RX on the Nano 33 BLE.
// Connect D1/TX to the receiver's RX and connect the boards' GND pins.
// D0/RX is available for data sent back to this connector.

struct __attribute__((packed)) AccelerationData {
  float x;
  float y;
  float z;
};

void sendAccelerationOverUart(const AccelerationData &sample) {
  Serial1.print(sample.x, 6);
  Serial1.print(',');
  Serial1.print(sample.y, 6);
  Serial1.print(',');
  Serial1.println(sample.z, 6);
}

void reportDisconnected() {
  digitalWrite(LED_BUILTIN, LOW);
  Serial1.println("#STATUS,disconnected");
}

uint16_t connectionHandleFor(const BLEDevice &peripheral) {
  unsigned int displayedAddress[6];

  if (sscanf(peripheral.address().c_str(),
             "%x:%x:%x:%x:%x:%x",
             &displayedAddress[0],
             &displayedAddress[1],
             &displayedAddress[2],
             &displayedAddress[3],
             &displayedAddress[4],
             &displayedAddress[5]) != 6) {
    return 0xffff;
  }

  uint8_t address[6];
  for (size_t i = 0; i < 6; ++i) {
    address[i] = displayedAddress[5 - i];
  }

  uint16_t handle = ATT.connectionHandle(0, address);
  if (handle == 0xffff) {
    handle = ATT.connectionHandle(1, address);
  }

  return handle;
}

bool requestCodedPhy(const BLEDevice &peripheral) {
  constexpr uint16_t HCI_LE_SET_PHY = (OGF_LE_CTL << 10) | 0x0032;
  constexpr uint8_t PHY_CODED = 0x04;
  constexpr uint16_t CODED_S8 = 0x0002;

  struct __attribute__((packed)) SetPhyParameters {
    uint16_t connectionHandle;
    uint8_t allPhys;
    uint8_t txPhys;
    uint8_t rxPhys;
    uint16_t phyOptions;
  } parameters;

  parameters.connectionHandle = connectionHandleFor(peripheral);
  parameters.allPhys = 0x00;
  parameters.txPhys = PHY_CODED;
  parameters.rxPhys = PHY_CODED;
  parameters.phyOptions = CODED_S8;

  if (parameters.connectionHandle == 0xffff) {
    return false;
  }

  return HCI.sendCommand(
             HCI_LE_SET_PHY, sizeof(parameters), &parameters) == 0;
}

void receiveAcceleration(BLEDevice peripheral) {
  Serial.print("# Connecting to ");
  Serial.println(peripheral.address());

  if (!peripheral.connect()) {
    Serial.println("# Connection failed");
    Serial1.println("#STATUS,disconnected");
    return;
  }

  digitalWrite(LED_BUILTIN, HIGH);
  Serial1.println("#STATUS,connected");

  delay(100);
  BLE.poll();

  if (requestCodedPhy(peripheral)) {
    Serial.println("# Requested LE Coded PHY, S=8");
  } else {
    Serial.println("# Could not request LE Coded PHY");
  }

  if (!peripheral.discoverService(ACCELEROMETER_SERVICE_UUID)) {
    Serial.println("# Accelerometer service discovery failed");
    peripheral.disconnect();
    reportDisconnected();
    return;
  }

  BLECharacteristic acceleration =
      peripheral.characteristic(ACCELEROMETER_CHARACTERISTIC_UUID);

  if (!acceleration) {
    Serial.println("# Accelerometer characteristic not found");
    peripheral.disconnect();
    reportDisconnected();
    return;
  }

  if (!acceleration.canSubscribe() || !acceleration.subscribe()) {
    Serial.println("# Could not subscribe to accelerometer data");
    peripheral.disconnect();
    reportDisconnected();
    return;
  }

  Serial.println("# Connected and receiving data");

  while (peripheral.connected()) {
    BLE.poll();

    if (!acceleration.valueUpdated()) {
      continue;
    }

    AccelerationData sample;
    const int bytesRead = acceleration.readValue(&sample, sizeof(sample));
    if (bytesRead != sizeof(sample)) {
      continue;
    }

    sendAccelerationOverUart(sample);
  }

  reportDisconnected();
  Serial.println("# Sender disconnected");
}

void setup() {
  // USB serial is used only for diagnostic messages.
  Serial.begin(115200);

  // Hardware UART: D1/TX, D0/RX, 115200 baud, 3.3 V logic.
  Serial1.begin(UART_BAUD_RATE);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  const unsigned long serialWaitStarted = millis();
  while (!Serial && millis() - serialWaitStarted < 3000) {
  }

  if (!BLE.begin()) {
    Serial.println("# Failed to initialize BLE");
    while (true) {
    }
  }

  Serial1.println("#STATUS,disconnected");
  Serial.println("# Scanning for Nano33-Accel");
  BLE.scanForUuid(ACCELEROMETER_SERVICE_UUID);
}

void loop() {
  BLEDevice peripheral = BLE.available();

  if (!peripheral) {
    BLE.poll();
    return;
  }

  BLE.stopScan();
  receiveAcceleration(peripheral);

  Serial.println("# Scanning for Nano33-Accel");
  BLE.scanForUuid(ACCELEROMETER_SERVICE_UUID);
}
