# OPNhydro - ESP32-C6 Hydroponics Controller

A fully autonomous, data-rich hydroponics automation system with precision control, automatic top-off, and remote monitoring via Home Assistant.

## Features

- **Full Water Quality Monitoring**: pH, EC/TDS, dissolved oxygen (optional), temperature
- **Environmental Monitoring**: Air temp/humidity, light intensity (lux/PPFD), VPD
- **Automatic Dosing**: pH up (optional)/down, two-part nutrients (A/B)
- **Automatic Top-Off (ATO)**: Ultrasonic level sensing with user-approved filling
- **Standalone Operation**: Local automation continues if Home Assistant is offline
- **Safety Features**: Float switch interlocks, dosing limits, timeout protection

## Project Structure

```
OPNhydroponics/
├── esphome/                    # ESPHome firmware configuration
│   ├── hydroponics-controller.yaml
│   ├── secrets.yaml.example
│   └── home-assistant-automations.yaml
├── hardware/
│   ├── ARCHITECTURE.md         # System design and pin assignments
│   ├── BOM.md                  # Bill of materials with pricing
│   ├── SCHEMATIC_DESIGN.md     # Circuit design guide
│   └── kicad/                  # KiCad PCB project
│       ├── hydroponics-controller.kicad_pro
│       └── README.md
├── docs/                       # Additional documentation
├── firmware/                   # Custom ESPHome components (if needed)
└── README.md
```

## Hardware Overview

| Category | Selection |
|----------|-----------|
| System Type | NFT (Nutrient Film Technique), 20-80 plants |
| Controller | ESP32-C6-DevKitC-1-N8 (WiFi 6, Thread, USB-C) |
| Sensors | Atlas Scientific EZO (pH, EC, DO) + environmental |
| Actuators | 1× 12V main pump, 4× 12V dosing pumps, 1× 12V ATO valve |
| Integration | Home Assistant via ESPHome, standalone capable |

### Sensor Suite

| Sensor | Interface | Purpose |
|--------|-----------|---------|
| Atlas EZO-pH | I2C | Water pH monitoring |
| Atlas EZO-EC | I2C | Nutrient concentration (EC/TDS) |
| Atlas EZO-DO | I2C | Dissolved oxygen (optional) |
| DS18B20 | 1-Wire | Water temperature |
| HC-SR04 | GPIO | Water level (ultrasonic) |
| BME280 | I2C | Air temp, humidity, pressure |
| BH1750 | I2C | Light intensity (lux) |
| Float switches | GPIO | Safety level detection |

### Actuators

| Actuator | Voltage | Control |
|----------|---------|---------|
| Main circulation pump | 12V DC | GPIO → MOSFET |
| pH Up dosing pump (optional) | 12V DC | GPIO → MOSFET |
| pH Down dosing pump | 12V DC | GPIO → MOSFET |
| Nutrient A dosing pump | 12V DC | GPIO → MOSFET |
| Nutrient B dosing pump | 12V DC | GPIO → MOSFET |
| ATO solenoid valve | 12V DC (NC) | GPIO → MOSFET |

## Quick Start

### 1. Hardware Setup

See [hardware/BOM.md](hardware/BOM.md) for the complete parts list.

**Minimum for testing:**
- ESP32-C6-DevKitC-1-N8 development board
- Atlas Scientific EZO-pH kit (or DFRobot for budget option)
- DS18B20 waterproof temperature probe
- Peristaltic dosing pump (12V)

### 2. ESPHome Configuration

1. Copy `esphome/secrets.yaml.example` to `esphome/secrets.yaml`
2. Fill in your WiFi credentials and generate API keys
3. Update DS18B20 address in the YAML (run I2C scan to find it)
4. Flash to ESP32-C6:

```bash
cd esphome
esphome run hydroponics-controller.yaml
```

### 3. Home Assistant Integration

1. The device will auto-discover in Home Assistant
2. Add the provided automations from `home-assistant-automations.yaml`
3. Create a dashboard with the exposed entities

## Local Automation

The controller runs standalone pH and EC control without Home Assistant:

**pH Control (once daily at 10:00 AM):**
- Runs once per day to avoid temperature-induced pH fluctuations
- If pH > (target + tolerance): dose pH Down
- If pH < (target - tolerance): logs warning (pH Up pump optional)
- Respects daily limits (default 50 mL/day)

**EC Control (every 10 minutes):**
- If EC < (target - tolerance): dose Nutrient A, then B
- Only doses if pH is within range (5.5-6.5)
- Respects lockout timer (default 5 min between doses)
- Respects daily limits (default 100 mL/day)

**ATO (Automatic Top-Off):**
- Monitors water level via ultrasonic sensor
- When level drops below threshold (default 70%), requests approval
- User approves via Home Assistant notification or dashboard
- Fills until target level (95%) or timeout

## Safety Features

1. **Float Switch Interlocks**: Main pump stops if low level detected
2. **ATO Overflow Protection**: High float switch stops fill immediately
3. **Dosing Lockout**: Minimum time between doses prevents overdosing
4. **Daily Limits**: Maximum mL per day for each chemical
5. **Timeout Protection**: ATO fill times out after configurable period
6. **Fail-Safe Valve**: NC (normally closed) solenoid prevents flooding on power loss

## PCB Design

The custom PCB is designed for JLCPCB fabrication:

- **Size**: 100mm × 80mm
- **Layers**: 2-layer
- **Features**: Reverse polarity protection, TVS diodes, proper isolation

See [hardware/kicad/README.md](hardware/kicad/README.md) for design files and manufacturing instructions.

## Configuration Reference

### Setpoints (adjustable via Home Assistant)

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| pH Target | 6.0 | 5.0-7.5 | Target pH value |
| pH Tolerance | 0.3 | 0.1-1.0 | Deadband before dosing |
| EC Target | 1500 µS/cm | 500-3000 | Target conductivity |
| EC Tolerance | 200 µS/cm | 50-500 | Deadband before dosing |
| Dose Amount | 2.0 mL | 0.5-20 | Per-dose volume |
| Lockout Time | 5 min | 1-30 | Min time between doses |
| Daily pH Limit | 50 mL | 10-200 | Max pH adjustment per day |
| Daily Nutrient Limit | 100 mL | 10-500 | Max nutrients per day |
| ATO Low Threshold | 70% | 50-90 | Level to trigger ATO request |
| ATO High Target | 95% | 80-100 | Level to stop filling |
| ATO Max Fill Time | 180s | 30-600 | Timeout for safety |

### Pin Assignment

See [hardware/ARCHITECTURE.md](hardware/ARCHITECTURE.md) for complete GPIO mapping.

## Cost Estimate

| Category | Cost |
|----------|------|
| Microcontroller | $8 |
| Power Management | $15 |
| Water Quality Sensors (Atlas) | $350 |
| Environmental Sensors | $20 |
| Actuators | $75 |
| PCB + Connectors | $40 |
| Enclosure | $25 |
| **Total** | **~$530** |

Budget option with DFRobot sensors: ~$280

## Contributing

This is an open project. Contributions welcome:

- Bug reports and feature requests via Issues
- PCB improvements and alternative designs
- ESPHome component enhancements
- Documentation improvements

## License

See [LICENSE](LICENSE) file.

## Acknowledgments

- [ESPHome](https://esphome.io/) for the excellent ESP32 framework
- [Atlas Scientific](https://atlas-scientific.com/) for quality sensor documentation
- [Home Assistant](https://www.home-assistant.io/) for the automation platform
