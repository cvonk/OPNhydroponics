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
│         │             │             │          │
│    ┌────┴────┐   ┌────┴────┐   ┌───┴───┐  ┌──────┴──────┐              │
│    │  I2C    │   │  GPIO   │   │ UART  │  │    SPI      │              │
│    │  Bus    │   │         │   │       │  │  (future)   │              │
│    └────┬────┘   └────┬────┘   └───────┘  └─────────────┘              │
│         │             │                                                 │
│    ┌────┴───────┐  ┌──┴───────┐                                        │
│    │ pH EZO     │  │Ultrasonic│                                        │
│    │ EC EZO     │  │ HC-SR04  │                                        │
│    │ RTD EZO    │  └──────────┘                                        │
│    │ BH1750     │                                                      │
│    │ BME280     │                                                      │
│    │ OLED       │                                                      │
│    └────────────┘                                                      │
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

### 6. Dosing Reservoir Level Monitoring

**Decision: Software volume tracking for v1. No hardware float sensors on dosing reservoirs.**

Rationale:
- GPIO pins are fully exhausted (GPIO21–23 reserved only for future RS-485)
- Adding hardware float sensors would require an I2C GPIO expander (e.g., PCF8574)
- Dosing reservoirs are small (1–2 L) and refilled manually during routine maintenance
- Pumps are peristaltic with a known flow rate (mL/s), so remaining volume can be
  estimated by tracking cumulative dose volume in firmware
- A low-volume warning can be triggered at, for example, 10% remaining (estimated)

**Software tracking approach:**
- At startup: user sets initial reservoir volume (or uses a default)
- Firmware subtracts estimated dose volume after each pump activation
- Home Assistant alerts when estimated remaining volume drops below threshold
- User resets the counter after refilling (via HA switch entity)

**v2 hardware path (if desired):**
- Add PCF8574 I2C GPIO expander (address 0x20–0x27, 8 GPIO pins)
- Mount one horizontal NC float switch (e.g., LH25) in each reservoir at ~20% fill
- Wire switches to PCF8574 inputs with pull-ups
- PCF8574 is polled over shared I2C bus (address 0x24, requires one spare I2C address)
- Cost: ~$2 for PCF8574 + ~$25 per float switch

### 7. Hardware Float Switch Safety Cutoffs

**Decision: FLOAT_LOW and FLOAT_HIGH provide hardware-enforced cutoffs, not software-only.**

To ensure fail-safe operation independent of MCU firmware, each float switch drives a small
NPN transistor that directly pulls the respective MOSFET gate to GND when its cutoff
condition is met. The MCU can still read the float state via GPIO for monitoring and
alerting, but the hardware path acts regardless of software state.

**FLOAT_LOW (GPIO0) → Main Pump (Q1) hardware cutoff:**
- GPIO0 HIGH = water below LOW mark (switch open, pull-up active) = pump must stop
- GPIO0 drives NPN transistor base; NPN collector tied to Q1 gate
- When GPIO0 HIGH: NPN saturates → Q1 gate pulled to ≈GND → pump off (hardware)
- When GPIO0 LOW: NPN off → Q1 gate controlled by GPIO10 normally

**FLOAT_HIGH (GPIO1) → ATO Valve (Q8) hardware cutoff:**
- FLOAT_HIGH is wired with pull-DOWN + switch-to-3.3V (reversed from FLOAT_LOW)
  so that GPIO1 HIGH = water at/above HIGH mark = consistent active-HIGH logic
- GPIO1 drives NPN transistor base; NPN collector tied to Q8 gate
- When GPIO1 HIGH: NPN saturates → Q8 gate pulled to ≈GND → ATO valve closes (hardware)
- When GPIO1 LOW: NPN off → Q8 gate controlled by GPIO7 normally

**Additional components required (per channel):**
- 1× MMBT3904 NPN transistor, SOT-23 (~$0.05)
- 1× 4.7kΩ base resistor, 0805 (already in BOM)

## Pin Assignment

| GPIO | Signal | Direction | Notes |
|------|--------|-----------|-------|
| 0 | FLOAT_LOW | Input | Flow float switch |
| 1 | FLOAT_HIGH | Input | High-level float switch |
| 2 | (available) | — | GPIO2 free — was 1-Wire; R30 4.7kΩ DNP |
| 3 | US_ECHO | Input | Ultrasonic sensor echo |
| 4 | I2C_SDA | Bidirectional | I2C bus (4.7kΩ pullup) |
| 5 | I2C_SCL | Output | I2C bus (4.7kΩ pullup) |
| 7 | ATO_VALVE | Output | ATO solenoid valve via MOSFET Q8 |
| 8 | (RGB LED) | — | DevKit on-board RGB LED — do not use |
| 9 | US_TRIG | Output | Ultrasonic sensor trigger (strapping pin, internal 45kΩ pullup) |
| 10 | PUMP_MAIN | Output | Main circulation pump via MOSFET Q1 (IRLR2905) |
| 11 | PUMP_PH_UP | Output | pH Up dosing pump via MOSFET Q2 |
| 15 | PUMP_PH_DN | Output | pH Down dosing pump via MOSFET Q3 (strapping pin) |
| 17 | (CP2102 TX) | — | Reserved — CP2102 UART TX on DevKit |
| 19 | PUMP_NUT_A | Output | Nutrient A dosing pump via MOSFET Q4 |
| 20 | PUMP_NUT_B | Output | Nutrient B dosing pump via MOSFET Q5 |
| 21 | (reserved) | — | Future RS-485 |
| 22 | (reserved) | — | Future RS-485 |
| 23 | (reserved) | — | Future RS-485 |

## Power Architecture

```
12V DC Input (5A min)
    │
    ├──► 12V Rail ──┬──► Main Pump MOSFET (IRLZ44N)
    │               ├──► Dosing Pump MOSFETs (4x IRLZ44N)
    │               └──► ATO Solenoid Valve MOSFET
    │
    └──► TPS62933 Buck ──► 5V @ 3A ──► USB/Sensors
                               │
                               └──► AMS1117-3.3 ──► 3.3V @ 1A ──► ESP32-C6
                                                                   │
                                                   ADM3260 ────────┘
                                                   (I2C isolator + isoPower
                                                    for pH and EC EZO circuits)
```

### Power Budget

| Component | Voltage | Current (typ) | Current (max) |
|-----------|---------|---------------|---------------|
| ESP32-C6 | 3.3V | 80mA | 350mA |
| pH EZO circuit | 3.3V | 15mA | 50mA |
| EC EZO circuit | 3.3V | 15mA | 50mA |
| RTD EZO circuit | 3.3V | 15mA | 50mA |
| BME280 | 3.3V | 1mA | 3mA |
| BH1750 | 3.3V | 0.2mA | 1mA |
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
- Interface: I2C via EZO-pH circuit (MEZZ3, U3 ADM3260, address 0x63)
- Calibration: 3-point (pH 4, 7, 10) — mid → low → high order required

### EC/TDS Sensor
- Type: 2-electrode conductivity probe, K=1.0
- Range: 0-20,000 µS/cm
- Accuracy: ±2%
- Interface: I2C via EZO-EC circuit (MEZZ2, U4 ADM3260, address 0x64)
- Calibration: Dry, single or dual point

### Water Temperature (EZO-RTD)
- Type: PT-1000 RTD probe with BNC connector
- Range: -126 to +1254°C
- Accuracy: ±(0.1 + 0.0017×°C)
- Interface: I2C via EZO-RTD circuit (address 0x66)
- No isolation required (unlike pH and EC)

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
| Main Pump | 2-pin pluggable screw terminal (**5.08mm** — Phoenix MSTB 2.5/2-ST-5.08) |
| Dosing Pumps | 4×2-pin pluggable screw terminal (3.5mm — Phoenix MC 1.5/2-ST-3.5) |
| ATO Solenoid | 2-pin pluggable screw terminal (3.5mm — Phoenix MC 1.5/2-ST-3.5) |
| pH/EC/RTD Probes | BNC female (panel mount) |
| I2C Sensors | 4-pin Phoenix Contact 1803280/1803581 |
| Float Switches | 2-pin JST-XH (×2) |
| Ultrasonic | 4-pin JST-XH |
| OLED Display | 4-pin header or Phoenix Contact |
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
- Panel-mount BNC connectors for pH/EC/RTD probes (3×)
- Optional: Clear lid for status LED visibility
