# KiCad Project - Hydroponics Controller

## Project Setup

### Required KiCad Version
- KiCad 8.0 or later

### Required Libraries

Install these libraries before opening the project:

1. **ESP32 Symbols & Footprints**
   - Source: https://github.com/espressif/kicad-libraries
   - Contains ESP32-C6-WROOM-1 module

2. **Connector Libraries** (included in KiCad)
   - Connector_BarrelJack
   - Connector_JST
   - Connector_USB

3. **Custom/Third-Party**
   - LCSC component library (optional, for JLCPCB assembly)

### Library Installation

```bash
# Clone Espressif KiCad libraries
git clone https://github.com/espressif/kicad-libraries.git

# Add to KiCad:
# Preferences -> Manage Symbol Libraries -> Add (espressif.kicad_sym)
# Preferences -> Manage Footprint Libraries -> Add (espressif.pretty)
```

## Design Specifications

### Board Parameters
- **Size**: 100mm × 80mm
- **Layers**: 2
- **Copper weight**: 2oz (70µm) outer layers
- **Min trace width**: 0.3mm (signal), 1.0mm (power), 2.0mm (high power)
- **Min clearance**: 0.2mm (signal), 0.3mm (power), 0.5mm (high voltage)
- **Via size**: 0.8mm pad / 0.4mm drill
- **Finish**: HASL (lead-free) or ENIG

### Layer Assignment
- **F.Cu (Top)**: Signal routing, component pads
- **B.Cu (Bottom)**: Ground plane, power distribution
- **F.Silkscreen**: Component designators, polarity marks
- **B.Silkscreen**: Board info, version

### Net Classes

| Class | Track Width | Clearance | Via Size | Usage |
|-------|-------------|-----------|----------|-------|
| Default | 0.3mm | 0.2mm | 0.8/0.4mm | Signal traces |
| Power | 1.0mm | 0.3mm | 1.0/0.5mm | 3.3V, 5V rails |
| HighPower | 2.0mm | 0.5mm | 1.2/0.6mm | 12V, pump/valve outputs |

## Schematic Hierarchy

```
hydroponics-controller.kicad_sch (Root)
├── power-input.kicad_sch        # 12V input, protection, connectors
├── power-regulators.kicad_sch   # Buck converter (12V→5V), LDO (5V→3.3V)
├── devkit-headers.kicad_sch     # ESP32-C6-DevKitC-1 pin headers
├── sensors-i2c.kicad_sch        # I2C bus, EZO connectors, BME280, BH1750
├── sensors-other.kicad_sch      # Ultrasonic, float switches
├── pump-drivers.kicad_sch       # MOSFET drivers for 6 outputs
└── status-led.kicad_sch         # WS2812B, optional OLED
```

## Component Placement Guidelines

### Critical Placement
1. **DevKit headers**: Center of board, USB-C edge accessible
2. **Buck converters**: Near power input, with heatsinking area
3. **MOSFETs**: Grouped near screw terminals for pumps/valve
4. **BNC connectors**: Board edge for panel mounting
5. **Decoupling caps**: Near EZO circuit power pins

### DevKit Mounting
- ESP32-C6-DevKitC-1-N8 mounts via 2×20 female pin headers (2.54mm pitch)
- Header row spacing: 22.86mm (900 mils)
- No antenna keep-out needed - antenna is on DevKit PCB
- USB-C accessible at DevKit edge

### Thermal Considerations
- MOSFETs: Add thermal vias under source pad
- Buck converters: Large copper pour for heatsinking
- LDO: Thermal pad connected to ground plane

## Connector Pinouts

### J1 - 12V Power Input (3.5mm Pluggable Terminal)
| Pin | Signal |
|-----|--------|
| 1 | +12V |
| 2 | GND |

### J2 - Main Pump (5.08mm Pluggable Terminal — Phoenix MSTB 2.5/2-ST-5.08)
| Pin | Signal |
|-----|--------|
| 1 | PUMP+ (12V switched) |
| 2 | PUMP- (GND) |

> 5.08mm pitch — physically incompatible with 3.5mm dosing connectors.

### J3-J6 - Dosing Pumps (3.5mm Pluggable Terminal each — Phoenix MC 1.5/2-ST-3.5)
| Pin | Signal |
|-----|--------|
| 1 | PUMP+ (12V switched) |
| 2 | PUMP- (GND) |

### J7 - ATO Solenoid Valve (3.5mm Pluggable Terminal)
| Pin | Signal |
|-----|--------|
| 1 | VALVE+ (12V switched) |
| 2 | VALVE- (GND) |

### J8-J10 - BNC Probe Connectors
- Panel-mount BNC female for pH, EC, RTD probes
- Connect to respective EZO circuit PRB input

### J11-J14 - I2C Sensors (JST-PH 4-pin, Qwiic compatible)
| Pin | Signal | Color |
|-----|--------|-------|
| 1 | GND | Black |
| 2 | 3.3V | Red |
| 3 | SDA | Blue |
| 4 | SCL | Yellow |

### J16 - Ultrasonic Sensor (JST-XH 4-pin)
| Pin | Signal |
|-----|--------|
| 1 | VCC (5V) |
| 2 | TRIG |
| 3 | ECHO |
| 4 | GND |

### J17-J18 - Float Switches (JST-XH 2-pin each)
| Pin | Signal |
|-----|--------|
| 1 | SWITCH |
| 2 | GND |

## Manufacturing Files

### Gerber Export Settings (JLCPCB)
- Gerber X2 format
- Include: F.Cu, B.Cu, F.Paste, B.Paste, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, Edge.Cuts
- Drill files: Excellon format, PTH and NPTH combined

### BOM Export
- Export as CSV for JLCPCB assembly
- Include: Reference, Value, Footprint, LCSC Part Number

### Pick & Place
- Export component positions for SMT assembly
- Origin: Aux origin or board origin (check JLCPCB requirements)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | TBD | Initial design |
