#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>

// ArduinoBLE does not currently expose PHY selection in its public API.
#include <utility/ATT.h>
#include <utility/HCI.h>

constexpr char DEVICE_NAME[] = "Nano33-Accel";
constexpr unsigned long SAMPLE_INTERVAL_MS = 50;

BLEService accelerometerService("7f510000-1b15-4f0d-8f53-7b2e95d4a101");
BLECharacteristic accelerometerCharacteristic(
    "7f510001-1b15-4f0d-8f53-7b2e95d4a101",
    BLERead | BLENotify,
    sizeof(float) * 3,
    true);

struct __attribute__((packed)) AccelerationData {
  float x;
  float y;
  float z;
};

uint16_t connectionHandleFor(const BLEDevice &central) {
  unsigned int displayedAddress[6];

  if (sscanf(central.address().c_str(),
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

  // A central may use either a public (0) or random (1) address.
  uint16_t handle = ATT.connectionHandle(0, address);
  if (handle == 0xffff) {
    handle = ATT.connectionHandle(1, address);
  }

  return handle;
}

bool requestCodedPhy(const BLEDevice &central) {
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

  parameters.connectionHandle = connectionHandleFor(central);
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

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  const unsigned long serialWaitStarted = millis();
  while (!Serial && millis() - serialWaitStarted < 3000) {
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize BMI270 accelerometer.");
    while (true) {
    }
  }

  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE.");
    while (true) {
    }
  }

  BLE.setLocalName(DEVICE_NAME);
  BLE.setDeviceName(DEVICE_NAME);
  BLE.setAdvertisedService(accelerometerService);

  accelerometerService.addCharacteristic(accelerometerCharacteristic);
  BLE.addService(accelerometerService);

  const AccelerationData initialValue = {0.0f, 0.0f, 0.0f};
  accelerometerCharacteristic.writeValue(
      reinterpret_cast<const uint8_t *>(&initialValue),
      sizeof(initialValue));

  BLE.advertise();
  Serial.println("#STATUS,disconnected");
  Serial.println("Advertising accelerometer service.");
}

void loop() {
  BLEDevice central = BLE.central();

  if (!central) {
    digitalWrite(LED_BUILTIN, LOW);
    BLE.poll();
    return;
  }

  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("#STATUS,connected");
  Serial.print("Connected to ");
  Serial.println(central.address());

  delay(100);
  BLE.poll();

  if (requestCodedPhy(central)) {
    Serial.println("Requested LE Coded PHY, S=8.");
  } else {
    Serial.println("Could not request LE Coded PHY.");
  }

  unsigned long lastSampleTime = 0;

  while (central.connected()) {
    BLE.poll();

    const unsigned long now = millis();
    if (now - lastSampleTime < SAMPLE_INTERVAL_MS ||
        !IMU.accelerationAvailable()) {
      continue;
    }

    lastSampleTime = now;

    float x;
    float y;
    float z;
    IMU.readAcceleration(x, y, z);

    const AccelerationData sample = {x, y, z};
    accelerometerCharacteristic.writeValue(
        reinterpret_cast<const uint8_t *>(&sample),
        sizeof(sample));

    Serial.print(sample.x, 3);
    Serial.print(',');
    Serial.print(sample.y, 3);
    Serial.print(',');
    Serial.println(sample.z, 3);
  }

  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("#STATUS,disconnected");
  Serial.println("Central disconnected.");
}
