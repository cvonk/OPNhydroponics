# OPNhydroponics - Hardware Architecture

## System Overview

ESP32-C6 based NFT hydroponics controller with full sensor suite, dosing pump control, and automatic top-off (ATO) capability. Designed for Home Assistant integration via ESPHome with standalone operation support.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           12V DC INPUT                                   │
│                               │                                          │
│                    ┌──────────┴──────────┐                               │
│                    │                     │                               │
│                    ▼                     ▼                               │
│              ┌─────────┐           ┌─────────┐                           │
│              │ 12V Bus │           │ 5V DC   │                           │
│              │ (Pumps) │           │ (Logic) │                           │
│              └────┬────┘           └────┬────┘                           │
│                   │                     │                                │
│         ┌─────────┼─────────┐           ▼                                │
│         ▼         ▼         ▼     ┌──────────┐                           │
│   ┌──────────┐ ┌──────────┐ ┌─────┤ 3.3V LDO │                           │
│   │Main Pump │ │ Dosing   │ │ ATO └────┬─────┘                           │
│   │ MOSFET   │ │ MOSFETs  │ │Valve     │                                 │
│   └──────────┘ └──────────┘ └─────┘    │                                 │
│                                    ┌──────┴──────┐                       │
│                                    │  ESP32-C6   │                       │
│                                    │             │                       │
│                                    └──────┬──────┘                       │
│                                           │                              │
│         ┌─────────────┬─────────────┬─────┴─────┬─────────────┐          │
│         │             │             │           │             │          │
│    ┌────┴────┐  ┌─────┴─────┐ ┌─────┴─────┐ ┌───┴───┐  ┌──────┴──────┐   │
│    │  I2C    │  │  1-Wire   │ │  GPIO     │ │ UART  │  │    SPI      │   │
│    │  Bus    │  │  Bus      │ │           │ │       │  │  (future)   │   │
│    └────┬────┘  └─────┬─────┘ └─────┬─────┘ └───────┘  └─────────────┘   │
│         │             │             │                                    │
│    ┌────┴───────┐     │        ┌────┴─────┐                              │
│    │ pH EZO     │     │        │Ultrasonic│                              │
│    │ EC EZO     │     │        │ HC-SR04  │                              │
│    │ DO EZO     │     │        └──────────┘                              │
│    │ BH1750     │     │                                                  │
│    │ BME280     │     │                                                  │
│    │ OLED       │     │                                                  │
│    └────────────┘     │                                                  │
│                       │                                                  │
│               ┌───────┴───────┐                                          │
│               │   DS18B20     │                                          │
│               │ (Water Temp)  │                                          │
│               └───────────────┘                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Design Decisions

### 1. Probe Isolation Strategy

To prevent ground loops and probe interference (especially between pH and EC), we use:

**Option A: Time-Division Multiplexing (Budget)**
- Single non-isolated ADC (ADS1115)
- MOSFET switches to power probes sequentially
- Only one probe powered at a time
- Cost: ~$15 for all probe interfaces

**Option B: EZO-Style I2C Circuits (Recommended)**
- Each probe has dedicated I2C interface circuit
- Galvanically isolated power per probe
- All probes can read simultaneously
- Cost: ~$60-150 depending on source (Atlas vs clones)

**Selected: Option B** - Better accuracy, easier software, worth the cost for medium scale.

### 2. Dosing Pump Selection

Peristaltic pumps recommended for:
- Self-priming capability
- Precise volume control via timing
- Chemical resistance
- No contamination between fluids

Specification:
- Voltage: 12V DC
- Flow rate: 1-3 mL/s adjustable via PWM
- Tubing: Silicone, 3mm ID

### 3. ESP32-C6 Module Selection

Options:
- **ESP32-C6-WROOM-1** - Bare module, requires antenna trace design and USB circuit
- **ESP32-C6-DevKitC-1** - Development board with USB-C, buttons, and antenna

Selected: **ESP32-C6-DevKitC-1-N8** (8MB flash) - Includes USB-C, PCB antenna, boot/reset buttons, and RGB LED. Mounts to carrier PCB via pin headers.

### 4. Automatic Top-Off (ATO) System

Uses existing ultrasonic sensor for level detection with a normally-closed solenoid valve:
- **Detection**: Ultrasonic sensor monitors water level continuously
- **Valve type**: 12V NC (normally closed) solenoid - fails safe (closed)
- **Safety**: Float switch provides hardware backup cutoff
- **User confirmation**: System requests approval via Home Assistant before filling
- **Timeout**: Maximum fill time prevents overflow if sensor fails

### 5. Standalone Operation

The controller operates independently when Home Assistant is unavailable:
- Local pH control: Once daily at 10:00 AM (avoids temperature-induced pH fluctuations)
  - Doses pH Down when above target (pH Up pump is optional)
- Local EC control: Doses nutrients when EC drops below threshold (every 10 min)
- Safety interlocks: Float switch protection always active
- ATO: Requires HA for user confirmation (manual override via physical button possible)
- Data logging: Buffers readings until HA reconnects

## Pin Assignment

| GPIO | Function | Notes |
|------|----------|-------|
| 0 | BOOT | On DevKit (directly wire button to GND) |
| 1 | I2C SDA | Sensors, display |
| 2 | I2C SCL | Sensors, display |
| 3 | 1-Wire | DS18B20 temp probes |
| 4 | Ultrasonic TRIG | Water level |
| 5 | Ultrasonic ECHO | Water level |
| 6 | Main Pump | 12V pump control |
| 7 | Dosing 1 (pH Up) | 12V peristaltic (optional) |
| 8 | (DevKit RGB LED) | Reserved - do not use |
| 9 | Dosing 3 (Nutrient A) | 12V peristaltic |
| 10 | Dosing 4 (Nutrient B) | 12V peristaltic |
| 11 | Float Switch 1 | Low level alarm |
| 12 | Float Switch 2 | High level (optional) |
| 13 | Status LED | WS2812B RGB (external) |
| 15 | TX (UART) | Debug (directly wire if needed) |
| 16 | RX (UART) | Debug (directly wire if needed) |
| 18 | USB D- | On DevKit |
| 19 | USB D+ | On DevKit |
| 20 | ATO Solenoid Valve | 12V NC solenoid for top-off |
| 21 | Dosing 2 (pH Down) | 12V peristaltic (moved from GPIO8) |
| 22 | Spare GPIO | Future expansion |
| 23 | Spare GPIO | Future expansion |

## Power Architecture

```
12V DC Input (5A min)
    │
    ├──► 12V Rail ──┬──► Main Pump MOSFET (IRLZ44N)
    │               ├──► Dosing Pump MOSFETs (4x IRLZ44N)
    │               └──► ATO Solenoid Valve MOSFET
    │
    └──► MP1584 Buck ──► 5V @ 2A ──► USB/Sensors
                              │
                              └──► AMS1117-3.3 ──► 3.3V @ 800mA ──► ESP32-C6
                                                                    │
                                                   Isolated DC-DC ──┘
                                                   (per probe)
```

### Power Budget

| Component | Voltage | Current (typ) | Current (max) |
|-----------|---------|---------------|---------------|
| ESP32-C6 | 3.3V | 80mA | 350mA |
| pH EZO circuit | 3.3V | 15mA | 50mA |
| EC EZO circuit | 3.3V | 15mA | 50mA |
| DO EZO circuit | 3.3V | 15mA | 50mA |
| BME280 | 3.3V | 1mA | 3mA |
| BH1750 | 3.3V | 0.2mA | 1mA |
| DS18B20 (×2) | 3.3V | 2mA | 4mA |
| OLED Display | 3.3V | 20mA | 30mA |
| HC-SR04 | 5V | 2mA | 15mA |
| WS2812B LED | 5V | 20mA | 60mA |
| **3.3V Total** | | ~150mA | ~550mA |
| **5V Total** | | ~25mA | ~80mA |
| Main Pump | 12V | 500mA | 1.5A |
| Dosing Pump (each) | 12V | 0 (idle) | 300mA |
| ATO Solenoid Valve | 12V | 0 (idle) | 500mA |
| **12V Total** | | 500mA | 3.2A |

## Sensor Specifications

### pH Sensor
- Type: Glass electrode with BNC connector
- Range: 0-14 pH
- Accuracy: ±0.1 pH
- Interface: I2C via EZO circuit (address 0x63)
- Calibration: 2 or 3 point (pH 4, 7, 10)

### EC/TDS Sensor
- Type: 2-electrode conductivity probe, K=1.0
- Range: 0-20,000 µS/cm
- Accuracy: ±2%
- Interface: I2C via EZO circuit (address 0x64)
- Calibration: Dry, single or dual point

### Dissolved Oxygen Sensor
- Type: Galvanic DO probe
- Range: 0-20 mg/L
- Accuracy: ±0.2 mg/L
- Interface: I2C via EZO circuit (address 0x61)
- Note: Membrane replacement every 6-12 months

### Water Temperature
- Type: DS18B20 waterproof probe
- Range: -55 to +125°C
- Accuracy: ±0.5°C
- Interface: 1-Wire (parasite or powered)

### Water Level
- Primary: HC-SR04 ultrasonic (non-contact)
- Backup: Float switches (alarm/safety)
- Range: 2-400cm
- Accuracy: ±3mm

### Air Temperature/Humidity
- Type: BME280
- Temp range: -40 to +85°C
- Humidity range: 0-100% RH
- Accuracy: ±1°C, ±3% RH
- Interface: I2C (address 0x76 or 0x77)

### Light/PAR
- Type: BH1750 (lux meter)
- Range: 1-65535 lux
- Interface: I2C (address 0x23 or 0x5C)
- Note: For true PAR, multiply lux by ~0.015 for typical grow lights

## PCB Design Requirements

### Board Specifications
- Size: 100mm × 80mm (fits common enclosures)
- Layers: 2 (4-layer preferred for EMI)
- Copper: 2oz outer layers (for power traces)
- Finish: HASL or ENIG

### Connector Selection
| Function | Connector Type |
|----------|----------------|
| 12V Power | 2-pin pluggable screw terminal (3.5mm) |
| Main Pump | 2-pin pluggable screw terminal (3.5mm) |
| Dosing Pumps | 4×2-pin pluggable screw terminal (3.5mm) |
| ATO Solenoid | 2-pin pluggable screw terminal (3.5mm) |
| pH/EC/DO Probes | BNC female (panel mount) - use included SMA-to-BNC adapters |
| I2C Sensors | 4-pin JST-PH (Qwiic compatible) |
| 1-Wire | 3-pin JST-PH |
| Float Switches | 2-pin JST-XH |
| Ultrasonic | 4-pin JST-XH |
| OLED Display | 4-pin header or JST-PH |
| Programming | USB-C |

### Protection Features
- Reverse polarity protection (P-MOSFET)
- Overvoltage protection (TVS diodes)
- ESD protection on all external connections
- Fused inputs (resettable PTC)
- Optocoupler isolation on pump outputs (optional)

### EMC Considerations
- Keep analog traces away from switching supplies
- Ground plane under ESP32-C6 antenna keep-out
- Decoupling capacitors close to ICs
- Ferrite beads on power inputs

## Enclosure

Recommended: IP65 rated ABS enclosure, ~150×100×70mm
- Cable glands for all wiring
- Panel-mount BNC connectors for pH/EC/DO probes (3×)
- Optional: Clear lid for status LED visibility
