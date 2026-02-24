# Schematic Design Guide

This document describes the circuit design for the OPNhydroponics controller PCB.

## Block Diagram

```
                                    ┌────────────────────────────────────────┐
                                    │              CONNECTORS                │
                                    │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
                                    │  │ BNC │ │ BNC │ │ BNC │ │Float│       │
                                    │  │ pH  │ │ EC  │ │ DO  │ │ SW  │       │
                                    │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘       │
                                    └─────┼──────┼──────┼──────┼─────────────┘
                                          │      │      │      │
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  PCB                                         │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────┐  │
│  │   POWER     │    │                    SENSORS                          │  │
│  │             │    │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │  │
│  │ 12V ──►5V   │    │  │ EZO-pH │  │ EZO-EC │  │ EZO-DO │  │ BME280 │     │  │
│  │     ──►3.3V │    │  │  I2C   │  │  I2C   │  │  I2C   │  │  I2C   │     │  │
│  │             │    │  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘     │  │
│  └──────┬──────┘    │      │           │           │           │          │  │
│         │           │      └───────────┴───────────┴───────────┘          │  │
│         │           │                      │ I2C Bus                      │  │
│         │           └──────────────────────┼──────────────────────────────┘  │
│         │                                  │                                 │
│         │           ┌──────────────────────┼──────────────────────────────┐  │
│         │           │              ESP32-C6-WROOM-1                       │  │
│         │           │  ┌────────────────────────────────────────────┐     │  │
│         └──────────►│  │  GPIO4/5: I2C      GPIO2: 1-Wire           │     │  │
│                     │  │  GPIO9/3: Ultrasonic  GPIO0/1: Float SW    │     │  │
│                     │  │  GPIO7: ATO  GPIO10/11/15/19/20: Pumps     │     │  │
│                     │  │  GPIO8/17/21-23: Reserved                  │     │  │
│                     │  └────────────────────────────────────────────┘     │  │
│                     └──────────────────────┬──────────────────────────────┘  │
│                                            │                                 │
│         ┌──────────────────────────────────┼──────────────────────────────┐  │
│         │                   PUMP/VALVE DRIVERS (all 12V)                  │  │
│         │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │  │
│         │  │ 12V    │  │ 12V    │  │ 12V    │  │ 12V    │  │ 12V    │     │  │
│         │  │ Main   │  │ pH Up  │  │ pH Dn  │  │ Nut A  │  │ Nut B  │     │  │
│         │  │ Pump   │  │ Dose   │  │ Dose   │  │ Dose   │  │ Dose   │     │  │
│         │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘     │  │
│         │                                                  ┌────────┐     │  │
│         │                                                  │ 12V    │     │  │
│         │                                                  │ ATO    │     │  │
│         │                                                  │ Valve  │     │  │
│         │                                                  └────────┘     │  │
│         └─────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Power Supply Section

### 1.1 Input Protection

```
12V DC IN ──┬──[PTC 5A]──┬──[TVS 15V]──┬──► 12V_PROTECTED
            │            │             │
           ─┴─          ─┴─           ─┴─
           GND          GND           GND

Component Selection:
- PTC: RXEF500 (5A hold, 10A trip)
- TVS: SMBJ15A (15V standoff, 24V clamp)
```

### 1.2 Reverse Polarity Protection

```
12V_PROTECTED ────┬───────────────────────► 12V_RAIL
                  │
              ┌───┴───┐
              │       │ S (Source tied to input)
       ┌──────┤ Q1    │──────────────────────────────────► 12V_SAFE
       │      │ (P-FET)│
       │      └───┬───┘ D
       │          │G
       R1      ┌──┴──┐
       10k     │ R2  │ 100k
       │       │     │
       ├───────┴─────┘
       │
      ─┴─
      GND

Q1: SI2301 (P-channel MOSFET, SOT-23)
- Vds = -20V, Id = -2.8A, Rds(on) = 80mΩ
```

### 1.3 Buck Converter

**12V to 5V (Logic/USB)**
```
                        Cbst
            ┌──────────┤├───────────────────────────────┐
            │         100nF                             │
            │                                      BST─┘
12V_SAFE ───┼──[Cin]──┬──────────────────────────┐
            │  10µF   │                      VIN─┤2      1├─BST
            │        ─┴─                         │           │
            │        GND          EN ────────────┤3  TPS  6 ├─SW──┬──[L1 4.7µH]──┬──► 5V
            │                    3.3V             │  62933    │     │               │
            │                    Rrt ─────────────┤4  DRL  5 ├─GND │            [Cout]
            │                    47k              │           │    ─┴─           2×22µF
            │                    │               ─┴─         GND   │               │
            │                   ─┴─              GND               │              ─┴─
            │                   GND                                │              GND
            │                                                      │
            │              ┌──[R_top 200k]────────────────────────┤ 5V
            │              │                                       │
            │           FB─┤7                                     ─┴─
            │              └──[R_bot 38.3k]──► GND               GND
            │
            │        Css ──────────────────── SS─┤8
            │       10nF                          │
            │                                    ─┴─
            │                                    GND
           ─┴─
           GND

Vout = 0.8V × (1 + R_top/R_bot)  →  5V = 0.8 × (1 + 200k/38.3k) ≈ 4.98V ✓
Fsw  = 57,400 / RT(kΩ) + 10.3    →  RT = 47kΩ → Fsw ≈ 1 MHz

Component Selection:
- IC:   TPS62933DRLR (SOT583, synchronous buck, 3.8–30V in, 3A, 200kHz–2.2MHz)
- L1:   4.7µH, 3A, DCR < 50mΩ (e.g. Würth 744043004)
- Cin:  10µF / 25V ceramic (X5R or X7R)
- Cout: 2×22µF / 10V ceramic (X5R or X7R)
- Cbst: 100nF / 10V ceramic (BST to SW)
- Css:  10nF (soft-start ≈ 1.5ms; minimum 6.8nF, do not float)
- Rrt:  47kΩ to GND → Fsw = 1MHz
- R_top: 200kΩ 1%
- R_bot:  38.3kΩ 1% (E96 series)
- No external compensation required (internal loop compensation)
- No external diode required (synchronous rectification)

Note: 12V rail powers pumps and ATO valve directly.
```

### 1.4 LDO (3.3V)

```
5V ──┬──[10µF]──┬──► VIN ┌─────────┐ VOUT ──┬──[10µF]──┬──► 3.3V
     │          │        │ AMS1117 │        │          │
    ─┴─        ─┴─       │  -3.3   │       ─┴─        ─┴─
    GND        GND       └────┬────┘       GND        GND
                              │
                             ─┴─
                             GND
```

---

## 2. ESP32-C6 Section

### 2.1 DevKit Pin Headers

The ESP32-C6-DevKitC-1-N8 mounts to the carrier PCB via 2×20 pin headers.
USB-C, boot/reset buttons, antenna, and power regulation are on the DevKit.

```
                    ┌─────────────────────────────────────┐
                    │        ESP32-C6-DevKitC-1-N8        │
                    │     (includes USB-C, antenna,       │
                    │      boot/reset buttons, RGB LED)   │
                    │                                     │
           3.3V ────┤ 3V3                            GND  ├──── GND
            5V ─────┤ 5V (from USB or external)           │
                    │                                     │
   FLOAT_FLOW ──────┤ GPIO0  (input)                      │
   FLOAT_HIGH ──────┤ GPIO1  (input)                      │
      ONE_WIRE ─────┤ GPIO2  (bidirectional)              │
       US_ECHO ─────┤ GPIO3  (input)                      │
       I2C_SDA ─────┤ GPIO4  (bidirectional)              │
       I2C_SCL ─────┤ GPIO5  (output)                     │
                    │                                     │
     ATO_VALVE ─────┤ GPIO7  (output)                     │
                    │                                     │
     (reserved) ────┤ GPIO8  (RGB LED on DevKit)          │
       US_TRIG ─────┤ GPIO9  (output, strapping pin)      │
     PUMP_MAIN ─────┤ GPIO10 (output)                     │
     PUMP_PH_UP ────┤ GPIO11 (output)                     │
                    │                                     │
     PUMP_PH_DN ────┤ GPIO15 (output)                     │
     (reserved) ────┤ GPIO17 (CP2102 UART TX)             │
    PUMP_NUT_A ─────┤ GPIO19 (output)                     │
    PUMP_NUT_B ─────┤ GPIO20 (output)                     │
                    │                                     │
     (reserved) ────┤ GPIO21 (future RS-485)              │
     (reserved) ────┤ GPIO22 (future RS-485)              │
     (reserved) ────┤ GPIO23 (future RS-485)              │
                    │                                     │
                    └─────────────────────────────────────┘

Signal Type Key:
  (input)         = Input only
  (output)        = Output only
  (bidirectional) = Bidirectional (I2C, 1-Wire)

Reserved Pins:
- GPIO8:  DevKit RGB LED (do not use)
- GPIO12/13: USB D+/D- for Serial/JTAG/Upload (do not use)
- GPIO17: CP2102 UART TX (do not use)
- GPIO21-23: Reserved for future RS-485 expansion

Strapping Pins:
- GPIO9:  Strapping pin with internal ~45kΩ pullup. Used for US_TRIG (non-critical
          output initialized after boot). Compatible with boot requirements.
- GPIO15: Strapping pin with weak pulldown. Used for PUMP_PH_DN. The 10kΩ pulldown
          in the MOSFET driver will disable ESP32 ROM boot messages (cosmetic only).
```

### 2.2 Carrier PCB Headers

```
Use 2×20 female headers (2.54mm pitch) on carrier PCB.
DevKit plugs in from above.

Header spacing: 22.86mm (900 mils) between rows
```

---

## 3. I2C Sensor Interface

### 3.1 I2C Bus

```
                3.3V
                 │
            ┌────┴────┐
            │         │
           R1        R2
          4.7k      4.7k
            │         │
GPIO4 ──────┼─────────┴──────────► SDA Bus (to all I2C devices)
            │
GPIO5 ──────┴────────────────────► SCL Bus (to all I2C devices)

Power Supply Decoupling (at each device):
    3.3V ──┬──[100nF]──┬──► VCC (to each I2C device)
           │           │
          ─┴─         ─┴─
          GND         GND

Component Selection:
- R1, R2: 4.7kΩ pullup resistors (standard for I2C)
- Decoupling: 100nF ceramic capacitor at each I2C device VCC pin
- Do NOT place capacitors on SDA/SCL data lines (degrades signal integrity)

Note: Maximum total bus capacitance is 400pF for I2C standard mode.
      Keep traces short and avoid adding extra capacitance to data lines.
```

### 3.2 EZO Circuit Connections

```
Atlas Scientific EZO circuits use standard I2C.
Default addresses:
- EZO-pH:  0x63
- EZO-EC:  0x64
- EZO-DO:  0x61 (may need address change to avoid conflict)
- BME280:  0x76
- BH1750:  0x23

Each EZO circuit:
┌──────────────────────────────────────┐
│  EZO-pH (or EC, DO)                  │
│                                      │
│   VCC ◄──── 3.3V (isolated)          │
│   GND ◄──── GND (isolated)           │
│   SDA ◄───► I2C SDA                  │
│   SCL ◄──── I2C SCL                  │
│   PRB ◄──── BNC panel-mount (probe uses SMA-to-BNC adapter) │
│                                      │
└──────────────────────────────────────┘

For probe isolation, power each EZO from isolated DC-DC:
3.3V ──► [B0303S-1WR2] ──► 3.3V_ISO ──► EZO VCC
```

### 3.3 I2C Connector

**OPNhydro uses Phoenix Contact 4-pin (3.5mm pitch) ✅**

```
Phoenix Contact 4-pin connector specification:
──────────────────────────────────────────────

Manufacturer: Phoenix Contact
PCB Header: 1803280 (4-position, through-hole, straight)
Plug Housing: 1803581 (4-position pluggable)
Pitch: 3.5mm (COMBICON series)
Wire Range: 28-16 AWG (0.08-1.5mm²)
Rated Voltage: 160V
Rated Current: 8A per contact
Contact Material: Copper alloy, tin-plated
Termination: Screw connection (plug side)
Mounting: Through-hole, solder pins
Cost: ~$1.50-2.50 per set (header + plug)

Pinout (standard I2C):
┌─────────────────────┐
│ Pin 1: GND (Black)  │ ◄── System GND
│ Pin 2: 3.3V (Red)   │ ◄── 3.3V power rail
│ Pin 3: SDA (Blue)   │ ◄── I2C Data (GPIO1 via pullup)
│ Pin 4: SCL (Yellow) │ ◄── I2C Clock (GPIO2 via pullup)
└─────────────────────┘

Advantages:
- Industrial-grade reliability and durability
- Screw terminals - no crimping required, field-serviceable
- Large pitch (3.5mm) - easy hand assembly
- High current rating (8A) - suitable for power distribution
- Positive locking mechanism - vibration resistant
- Through-hole mounting - very strong PCB attachment
- Color-coded options available for easier assembly
- Wide wire gauge acceptance (28-16 AWG)

PCB Layout:
- Place connector(s) on board edge for easy access
- Multiple connectors can be chained on same I2C bus
- Keep connector away from high-current traces (pump drivers)
- Typical placement: near ESP32-C6 header for short I2C traces
- Through-hole mount requires 1.0mm drill holes
- Recommended pad size: 1.7mm diameter (0.35mm annular ring)

Recommended usage:
- EZO pH circuit (I2C address 0x63)
- EZO EC circuit (I2C address 0x64)
- EZO DO circuit (I2C address 0x61)
- BME280 air temp/humidity sensor (I2C address 0x76/0x77)
- BH1750 light sensor (I2C address 0x23/0x5C)
- Optional OLED display (SSD1306, I2C address 0x3C/0x3D)
- Future I2C expansion modules

Ordering Information:
- DigiKey: Search "1803280" (header), "1803581" (plug)
- Mouser: Phoenix Contact COMBICON series
- Alternative: Use Phoenix Contact MC 1.5/4-ST-3.5 (generic equivalent)

**Note:** NOT compatible with Qwiic/STEMMA QT (which uses 1.0mm JST-SH).
          Requires field wiring with screw terminals on plug side.
          Excellent for industrial/commercial applications.
```

**Connector comparison:**
- 1-wire (DS18B20): JST-XH 3-pin (2.5mm pitch) - different pin count!
- Ultrasonic (HC-SR04): JST-XH 4-pin (2.5mm pitch) - smaller pitch!
- I2C sensors: Phoenix Contact 4-pin (3.5mm pitch) ✅

---

## 4. Temperature Sensor (1-Wire)

### 4.1 Basic Circuit

```
1-Wire Bus Connection:

    3.3V ───┬────────────────────────────► VDD to DS18B20 (Pin 3, Red)
            │
           [R1] 4.7kΩ pullup resistor
            │
            └──┬─────────────────────────► DQ to DS18B20 (Pin 2, Yellow)
               │
    GPIO2 ─────┘

    GND ────────────────────────────────► GND to DS18B20 (Pin 1, Black)


IMPORTANT: R1 connects between 3.3V and DQ (NOT to GND!)
           The pullup resistor pulls the 1-wire data line HIGH


Complete DS18B20 Wiring:

         3.3V rail
            │
            ├──────────────────────► Pin 3: VDD (Red wire)
            │
           [R1]
           4.7kΩ
            │
            ├─────┬────────────────► Pin 2: DQ (Yellow wire)
            │     │
    GPIO2 ────────┘
            │
    GND rail│
            └──────────────────────► Pin 1: GND (Black wire)
```

### 4.2 Component Selection

| Component | Value/Type | Purpose | Package |
|-----------|------------|---------|---------|
| **R1** | 4.7kΩ ±5% | 1-wire data line pullup | 0805 SMD |
| **C1** (optional) | 100nF | VDD decoupling near sensor | 0805 SMD |
| **D1** (optional) | 5.6V TVS | ESD protection for long cables | SOD-123 |
| **R2** (optional) | 100Ω | Series protection with TVS | 0805 SMD |

### 4.3 PCB Connector

**3-pin JST-XH connector (2.5mm pitch) for waterproof probe:**
```
┌─────────────────────┐
│ Pin 1: GND (Black)  │ ◄── To system GND
│ Pin 2: DQ (Yellow)  │ ◄── To GPIO2 via 4.7kΩ pullup to 3.3V
│ Pin 3: VDD (Red)    │ ◄── To 3.3V rail
└─────────────────────┘

Connector: JST-XH 3-pin S3B-XH-A (Right-angle, through-hole PCB mount)
Housing: JST XHP-3 (3-pin for cable assembly)
Contacts: JST SXH-001T-P0.6 (crimp terminals, 30-26 AWG)
```

### 4.4 How the 1-Wire Protocol Works

**Open-Drain Bidirectional Communication:**
- Both ESP32 and DS18B20 can only pull the line **LOW** (to GND)
- Neither device drives the line HIGH - the pullup resistor does this
- This allows bidirectional communication on a single wire
- Multiple devices can share the bus without conflict

**Why 4.7kΩ Pullup?**
```
Bus Capacitance: C_bus ≈ 200-400pF (typical 1-3m cable + sensor)
Pullup Resistor: R_pullup = 4.7kΩ
Time Constant: τ = R × C = 4.7kΩ × 400pF = 1.88µs
Rise Time (10-90%): t_rise = 2.2 × τ = 4.1µs

1-Wire Standard Speed Requirement: t_rise < 15µs ✓
Fast: 4.7kΩ works for cables up to 100m
```

**For longer cables or noisy environments:**
- Use 3.3kΩ pullup (faster rise time)
- Add 100Ω series resistor + TVS diode for ESD protection

### 4.5 Multiple Sensors on Same Bus

The 1-wire protocol supports **multiple DS18B20 sensors** on GPIO2:

```
         3.3V
          │
         R1
        4.7kΩ (single pullup for entire bus)
          │
GPIO2 ────┼──────┬──────────┬──────────┬──────────► (More sensors...)
                 │          │          │
               ┌─┴─┐      ┌─┴─┐      ┌─┴─┐
         GND   │DS1│      │DS2│      │DS3│
               └───┘      └───┘      └───┘
            Water Temp  Nutrient   Air Temp
                        Stock

Each sensor has unique 64-bit ROM ID for addressing:
- Sensor 1: 28-FF-64-1D-33-17-03-8C
- Sensor 2: 28-AA-12-5E-44-19-01-F3
- Sensor 3: 28-BB-34-6F-55-20-02-A1
```

**Important Notes:**
- Use **normal powered mode** (VDD connected to 3.3V) for multiple sensors
- Parasite power mode (VDD to GND) only works reliably with single sensor
- Firmware must address each sensor by its unique ROM ID

### 4.6 Typical OPNhydro Configuration

**Primary Use Case:**
- **Waterproof DS18B20 probe** in nutrient solution (required)
- Measures water temperature for EZO pH/EC/DO temperature compensation
- 3-wire cable: Red (VDD), Yellow (DQ), Black (GND)

**Optional Additional Sensors:**
- Ambient air temperature near grow area
- Nutrient stock solution temperature
- Root zone temperature (DWC systems)

### 4.7 Waterproof Probe Specifications

```
Recommended probe:
- Cable: 1-3 meters, silicone jacketed
- Wire colors: Red (VDD), Yellow (DQ), Black (GND)
- Probe tip: Stainless steel 304, 6mm × 30-50mm
- Connector: 3-pin JST-PH (compatible with carrier PCB)
- Temperature range: -55°C to +125°C
- Waterproof rating: IP68
- Response time: <10 seconds in water
- Accuracy: ±0.5°C (-10°C to +85°C)
```

### 4.8 Temperature Conversion Timing

**Resolution vs Speed Trade-off:**
| Resolution | Conversion Time | Temperature Step | Use Case |
|------------|-----------------|------------------|----------|
| 9-bit | 93.75ms | 0.5°C | Fast updates |
| 10-bit | 187.5ms | 0.25°C | Standard |
| 11-bit | 375ms | 0.125°C | Good accuracy |
| **12-bit** | **750ms** | **0.0625°C** | **Default (best accuracy)** ✅ |

**Firmware Timing Example:**
```c
// Request temperature conversion
ds18b20_trigger_conversion(GPIO2);

// Wait for conversion (12-bit resolution = 750ms)
vTaskDelay(pdMS_TO_TICKS(750));

// Read temperature
float water_temp = ds18b20_read_temp(GPIO2);

// Send to EZO circuits for automatic compensation
char cmd[16];
snprintf(cmd, sizeof(cmd), "T,%.1f", water_temp);
ezo_send_command(I2C_EZO_PH, cmd);  // pH compensation
ezo_send_command(I2C_EZO_EC, cmd);  // EC compensation
ezo_send_command(I2C_EZO_DO, cmd);  // DO compensation
```

### 4.9 Optional ESD Protection (Long Cables)

For cables **>3 meters** or **harsh EMI environments**:

```
         3.3V
          │
         R1
        4.7kΩ
          │
GPIO2 ────┼──────[R2 100Ω]────┬────► To DS18B20 DQ
          │                   │
         D1                 ──┴──
      (5.6V TVS)           ─ ─ ─  D2: 5.6V TVS diode
         │                 ──┬──
        ─┴─                  │
        GND                 ─┴─
                            GND

Component Selection:
- D1: TVS diode 5.6V bidirectional (e.g., SMAJ5.0CA)
- D2: TVS diode 5.6V bidirectional (at sensor end if possible)
- R2: 100Ω current-limiting resistor
```

### 4.10 Power Modes

**Normal (Powered) Mode** ✅ **Recommended for OPNhydro**
```
VDD (Pin 3) ──► 3.3V
DQ (Pin 2)  ──► GPIO2 + 4.7kΩ pullup
GND (Pin 1) ──► GND

Advantages:
- Reliable operation with multiple sensors
- Faster conversion times
- Recommended for permanent installations
```

**Parasite Power Mode** (Alternative)
```
VDD (Pin 3) ──► GND (tied to ground)
DQ (Pin 2)  ──► GPIO2 + 4.7kΩ pullup
GND (Pin 1) ──► GND

Power "stolen" from DQ line via internal capacitor

Use only when:
- Cable has only 2 wires available
- Single sensor only
- Temporary/portable applications

Note: OPNhydro uses normal powered mode for reliability
```

### 4.11 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No sensor detected | Incorrect wiring | Verify VDD, GND, DQ connections with multimeter |
| Intermittent readings | Weak pullup for cable length | Reduce R1 to 3.3kΩ or 2.2kΩ |
| CRC errors | Bus capacitance too high | Shorten cable or reduce pullup resistance |
| Multiple sensors conflict | Parasite power with >1 sensor | Use normal powered mode (VDD to 3.3V) |
| Slow thermal response | Large thermal mass | Use thin-wall stainless probe |
| Erratic readings | EMI/RFI interference | Add 100Ω series + TVS protection |
| Reading stuck at 85°C | Power-on reset default | Check power supply, add decoupling cap |

### 4.12 Why GPIO2 Was Selected

From ESP32-C6 pinout:
- **GPIO2**: Bidirectional, suitable for 1-wire protocol
- No boot strapping requirements (safe to use)
- Not shared with USB (D+/D-), UART, or SPI
- Located near I2C pins (GPIO4/5) for logical grouping on PCB
- Can be configured as input/output via software

### 4.13 Integration with EZO Sensors

**Temperature compensation is critical** for accurate pH/EC/DO measurements:

```
Temperature Effect on Sensors:
- pH: ±0.003 pH per °C (Nernst equation)
- EC: ±2% per °C (ion mobility changes)
- DO: ±2.3% per °C (oxygen solubility decreases with temp)

Firmware Integration:
void update_ezo_temperature_compensation(void) {
    // Read water temperature
    float water_temp = ds18b20_read_temp(GPIO2);

    // Format command
    char temp_cmd[16];
    snprintf(temp_cmd, sizeof(temp_cmd), "T,%.1f", water_temp);

    // Send to all EZO circuits
    ezo_send_command(I2C_EZO_PH, temp_cmd);  // Address 0x63
    ezo_send_command(I2C_EZO_EC, temp_cmd);  // Address 0x64
    ezo_send_command(I2C_EZO_DO, temp_cmd);  // Address 0x61

    // EZO circuits now automatically compensate all readings
}

Update Frequency:
- Every measurement cycle (recommended)
- Or only when temp changes >0.5°C (power saving)
```

---

## 5. Ultrasonic Sensor (HC-SR04)

### 5.1 Basic Circuit

```
HC-SR04 Ultrasonic Distance Sensor Connection:

    5V rail ────────────────────────────► VCC (HC-SR04)
                                           │
                                      ┌────┴────┐
    GND rail ───────────────────────► │ HC-SR04 │
                                      │         │
    GPIO9 ──────────────────────────► │ TRIG    │ (3.3V logic accepted)
    (US_TRIG)                         │         │
                                      │ ECHO    ├───► 5V output
                         ┌────────────┤         │
                         │            └─────────┘
                         │
                     ┌───┴───┐
                     │  5V   │
                     │ ECHO  │
                     └───┬───┘
                         │
                 ┌───[R1]───┬─────────────► GPIO3 (US_ECHO)
                 │   1kΩ    │                3.3V input
        ────────►│          │
    from ECHO    │        [R2]
                 │        2.2kΩ
                 │          │
                ─┴─        ─┴─
               (5V)       GND


Voltage Divider on ECHO Pin:
    V_out = V_in × R2 / (R1 + R2)
    V_out = 5V × 2.2kΩ / (1kΩ + 2.2kΩ)
    V_out = 5V × 0.6875 = 3.44V ✓ (safe for ESP32 3.3V GPIO)


Signal Flow:
1. ESP32 GPIO9 sends 10µs pulse to TRIG (3.3V HIGH)
2. HC-SR04 emits ultrasonic burst
3. HC-SR04 ECHO pin goes HIGH (5V) while waiting for reflection
4. Voltage divider reduces 5V → 3.44V for ESP32 GPIO3
5. ESP32 measures ECHO pulse width to calculate distance
```

### 5.2 Component Selection

| Component | Value/Type | Purpose | Package |
|-----------|------------|---------|---------|
| **HC-SR04** | Ultrasonic sensor | Distance measurement 2-400cm | 4-pin module |
| **R1** | 1kΩ ±5% | Upper resistor in voltage divider | 0805 SMD |
| **R2** | 2.2kΩ ±5% | Lower resistor in voltage divider | 0805 SMD |
| **C1** (optional) | 100µF electrolytic | HC-SR04 power supply filtering | Through-hole |
| **C2** (optional) | 100nF ceramic | High-frequency decoupling | 0805 SMD |

### 5.3 How the HC-SR04 Works

**Ultrasonic Ranging Principle:**

```
Step 1: Trigger Pulse
   ESP32 sends 10µs HIGH pulse to TRIG pin
              ┌────┐
   TRIG  ─────┘    └─────
              10µs

Step 2: Ultrasonic Burst
   HC-SR04 emits 8 cycles of 40kHz ultrasonic sound

   [Sensor] )))))))))) → → → (reflects off water surface) → → → )))))))))) [Sensor]

Step 3: Echo Detection
   ECHO pin goes HIGH when burst sent, LOW when echo received
                 ┌─────────────────┐
   ECHO  ────────┘                 └────────
                 ← Time = Distance →

Step 4: Distance Calculation
   Distance (cm) = (Echo pulse width in µs) × Speed of sound / 2
   Distance (cm) = (pulse_width_µs × 0.0343) / 2
   Distance (cm) = pulse_width_µs / 58.2
```

**Why the voltage divider?**
- HC-SR04 operates at 5V logic levels
- ESP32-C6 GPIOs are **3.3V** (NOT 5V tolerant on most pins)
- ECHO output is 5V when HIGH → must reduce to ~3.3V
- TRIG input accepts 3.3V as logic HIGH (TTL threshold ~2V)

### 5.4 Voltage Divider Design

**Calculation for R1 and R2:**

```
Target: Reduce 5V to ~3.3V for ESP32 GPIO3 (US_ECHO)

V_out = V_in × R2 / (R1 + R2)

Let R1 = 1kΩ, R2 = 2.2kΩ:
V_out = 5V × 2.2kΩ / (1kΩ + 2.2kΩ)
V_out = 5V × 2.2 / 3.2
V_out = 3.44V ✓

Tolerance Analysis (±5% resistors):
  Best case:  R1=0.95kΩ, R2=2.31kΩ → V_out = 3.54V (still safe)
  Worst case: R1=1.05kΩ, R2=2.09kΩ → V_out = 3.32V (safe)

ESP32-C6 V_IH (Input HIGH voltage): 2.0V minimum
Maximum safe input: 3.6V (absolute maximum rating)
Conclusion: 3.44V nominal is safe ✓

Current Draw Through Divider:
  I = V / R_total = 5V / 3.2kΩ = 1.56mA
  Power: P = V² / R = 25 / 3200 = 7.8mW (negligible)
```

**Alternative: Dedicated Level Shifter** (optional, higher cost)
- Use BSS138-based bidirectional level shifter
- Cleaner signal with faster rise/fall times
- More expensive (~$1-2 vs $0.10 for resistors)
- Recommended only for very long distances (>3m)

### 5.5 PCB Connector

**4-pin JST-XH connector (2.5mm pitch) for HC-SR04:**
```
┌─────────────────────┐
│ Pin 1: VCC (5V)     │ ◄── To 5V rail (from buck converter)
│ Pin 2: TRIG         │ ◄── To GPIO9 (US_TRIG)
│ Pin 3: ECHO         │ ◄── To voltage divider → GPIO3
│ Pin 4: GND          │ ◄── To system GND
└─────────────────────┘

Connector: JST-XH 4-pin B4B-XH-A (Right-angle, PCB mount)
Housing: JST XHP-4 (4-pin for cable assembly)
Contacts: JST SXH-001T-P0.6 (crimp terminals)

Standard HC-SR04 wire colors:
- VCC:  Red
- TRIG: Orange or White
- ECHO: Yellow or Orange
- GND:  Black or Brown
```

### 5.6 Timing and Measurement

**HC-SR04 Timing Specifications:**

```
Trigger Input:
- Minimum pulse width: 10µs
- Recommended: 10-15µs
- Logic level: >2V for HIGH (3.3V is adequate)

Echo Output:
- Range: 150µs to 25ms (corresponds to 2.5cm to 430cm)
- Timeout: 38ms if no echo received
- Update rate: Maximum 20Hz (50ms between measurements)

Measurement Cycle:
   ┌─10µs─┐
   │      │                          ┌─────── Echo ──────┐
───┘      └──────────────────────────┘                   └────
   TRIG                               ECHO (proportional to distance)

   ← 10µs → ←─────────── Varies 150µs - 25ms ───────────→
```

**Firmware Example (ESP-IDF):**

```c
// GPIO definitions
#define US_TRIG_GPIO    9
#define US_ECHO_GPIO    3

// Trigger measurement
void hcsr04_trigger(void) {
    gpio_set_level(US_TRIG_GPIO, 0);
    esp_rom_delay_us(2);  // Ensure clean LOW

    gpio_set_level(US_TRIG_GPIO, 1);
    esp_rom_delay_us(10);  // 10µs trigger pulse

    gpio_set_level(US_TRIG_GPIO, 0);
}

// Measure distance in cm
float hcsr04_read_distance_cm(void) {
    // Trigger measurement
    hcsr04_trigger();

    // Wait for ECHO to go HIGH (with timeout)
    uint32_t timeout = 0;
    while (gpio_get_level(US_ECHO_GPIO) == 0) {
        if (++timeout > 10000) return -1.0;  // Timeout
        esp_rom_delay_us(1);
    }

    // Measure ECHO pulse width
    uint64_t start = esp_timer_get_time();
    timeout = 0;

    while (gpio_get_level(US_ECHO_GPIO) == 1) {
        if (++timeout > 30000) return -1.0;  // Timeout (>5m)
        esp_rom_delay_us(1);
    }

    uint64_t end = esp_timer_get_time();
    uint32_t pulse_width_us = (uint32_t)(end - start);

    // Convert to distance
    // Speed of sound = 343 m/s = 0.0343 cm/µs
    // Distance = (time × speed) / 2  (divide by 2 for round trip)
    // Distance (cm) = (pulse_width_us × 0.0343) / 2
    // Simplified: Distance (cm) = pulse_width_us / 58.2

    float distance_cm = (float)pulse_width_us / 58.2;

    return distance_cm;
}

// Usage in main loop
void measure_water_level(void) {
    float distance_cm = hcsr04_read_distance_cm();

    if (distance_cm < 0) {
        ESP_LOGW(TAG, "Ultrasonic sensor timeout");
        return;
    }

    // Convert to water level
    // Assuming sensor mounted 50cm above full tank
    const float SENSOR_HEIGHT_CM = 50.0;
    float water_level_cm = SENSOR_HEIGHT_CM - distance_cm;

    // Validate range
    if (water_level_cm < 0 || water_level_cm > 40) {
        ESP_LOGW(TAG, "Water level out of range: %.1f cm", water_level_cm);
    } else {
        ESP_LOGI(TAG, "Water level: %.1f cm", water_level_cm);
    }
}
```

### 5.7 Distance to Water Level Conversion

**OPNhydro Tank Configuration:**

```
Sensor mounting (top of tank):

    [Ultrasonic Sensor] ← Mounted on lid/top
            ↓
            ↓ ← Distance measured by sensor
            ↓
    ─────────────────── ← Water surface
            │
            │ ← Water level (what we care about)
            │
    ═════════════════ ← Tank bottom


Calculation:
    Sensor_Height = Distance from sensor to tank bottom when empty
    Measured_Distance = Current ultrasonic reading
    Water_Level = Sensor_Height - Measured_Distance

Example:
    Sensor mounted 50cm above tank bottom
    Ultrasonic reads 35cm → Water level = 50 - 35 = 15cm
    Ultrasonic reads 10cm → Water level = 50 - 10 = 40cm (full)
```

### 5.8 Why GPIO9 and GPIO3 Were Selected

**GPIO9 (US_TRIG) - Output:**
- Can be used as output
- **NOTE: GPIO9 is a strapping pin with internal ~45kΩ pullup**
- Safe to use for TRIG because:
  - TRIG is an output (we drive it)
  - Non-critical timing (10µs pulse sent AFTER boot)
  - Internal pullup won't interfere with operation
  - Boot mode determined before ultrasonic code runs

**GPIO3 (US_ECHO) - Input:**
- Suitable for input
- Not a strapping pin (no boot conflicts)
- Not shared with USB, UART, or other critical functions
- 3.3V tolerant (with voltage divider from 5V HC-SR04)

**Pin Safety:**
- Both pins are located near each other on ESP32-C6 DevKit
- Easy PCB routing from header to ultrasonic connector
- No conflicts with I2C (GPIO4/5) or 1-wire (GPIO2)

### 5.9 Specifications and Limitations

**HC-SR04 Specifications:**
```
Operating Voltage: 5V DC
Operating Current: 15mA (typical), 2mA (idle)
Frequency: 40kHz ultrasonic
Detection Range: 2cm - 400cm
Accuracy: ±3mm (typical)
Measuring Angle: 15° cone
Trigger Input: 10µs TTL pulse
Echo Output: TTL pulse proportional to distance
Dimension: 45mm × 20mm × 15mm
```

**Limitations:**
- **Minimum distance:** 2cm (blind zone)
- **False readings near walls:** Reflections from tank walls can interfere
- **Temperature dependent:** Speed of sound varies with temperature
  - 20°C: 343 m/s
  - 25°C: 346 m/s (used in calculations)
  - 30°C: 349 m/s
  - Error: ~±1% per 5°C temperature change
- **Foam/bubbles:** Can absorb ultrasound, causing false readings
- **Turbulent water:** Aeration reduces accuracy

### 5.10 Temperature Compensation (Optional)

For improved accuracy, compensate for air temperature:

```c
// Accurate speed of sound calculation
float get_speed_of_sound_cm_us(float temp_celsius) {
    // Speed of sound (cm/µs) = (331.3 + 0.606 × T) / 10000
    // At 25°C: (331.3 + 0.606 × 25) / 10000 = 0.03465 cm/µs
    return (331.3 + 0.606 * temp_celsius) / 10000.0;
}

float hcsr04_read_distance_compensated(float air_temp) {
    uint32_t pulse_width_us = hcsr04_measure_pulse();

    float speed_cm_us = get_speed_of_sound_cm_us(air_temp);
    float distance_cm = (pulse_width_us * speed_cm_us) / 2.0;

    return distance_cm;
}

// Usage with BME280 air temperature
float air_temp = bme280_read_temperature();
float distance = hcsr04_read_distance_compensated(air_temp);
```

### 5.11 Alternative Sensors

For applications requiring higher accuracy or reliability:

**JSN-SR04T (Waterproof Ultrasonic)**
```
Advantages:
- Waterproof probe (IP67)
- Better for humid environments
- Less sensitive to temperature
- Same 5V interface as HC-SR04

Cost: ~$3-5 (vs $1-2 for HC-SR04)
Recommended for: Outdoor or very humid grow rooms
```

**VL53L0X/VL53L1X (Time-of-Flight Laser)**
```
Advantages:
- I2C interface (no voltage divider needed)
- Accurate to ±1mm
- Not affected by water vapor or temperature
- Faster measurement (up to 50Hz)
- Smaller size

Disadvantages:
- Shorter range (2m max vs 4m)
- Higher cost (~$5-10)
- Requires clear line of sight (no droplets on lens)

Recommended for: High-precision applications
```

### 5.12 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Always reads 0 or -1 | No echo received | Check wiring, ensure sensor has clear view |
| Reads maximum (400cm) | Timeout, no reflection | Check water surface is in range (>2cm) |
| Erratic readings | Turbulent water surface | Add averaging filter in firmware |
| Readings off by constant | Wrong calculation | Verify using distance / 58.2 formula |
| No readings at all | No power or bad TRIG | Check 5V supply, verify TRIG pulse with scope |
| Reads ~85cm constantly | ECHO stuck HIGH | Check voltage divider resistors |
| Intermittent readings | Weak 5V supply | Add 100µF cap near sensor VCC |
| Reading drifts | Temperature change | Implement temperature compensation |

**Firmware Filtering for Stable Readings:**

```c
// Median filter for ultrasonic readings
float get_stable_distance(void) {
    #define NUM_SAMPLES 5
    float samples[NUM_SAMPLES];

    // Take multiple readings
    for (int i = 0; i < NUM_SAMPLES; i++) {
        samples[i] = hcsr04_read_distance_cm();
        vTaskDelay(pdMS_TO_TICKS(60));  // 60ms between readings
    }

    // Sort samples
    for (int i = 0; i < NUM_SAMPLES - 1; i++) {
        for (int j = i + 1; j < NUM_SAMPLES; j++) {
            if (samples[i] > samples[j]) {
                float temp = samples[i];
                samples[i] = samples[j];
                samples[j] = temp;
            }
        }
    }

    // Return median (middle value)
    return samples[NUM_SAMPLES / 2];
}
```

### 5.13 PCB Layout Considerations

**Component Placement:**
```
1. Place voltage divider resistors (R1, R2) close to ESP32 GPIO3 pin
   - Minimize trace length from divider to GPIO
   - Reduces noise pickup

2. Optional decoupling capacitors:
   - C1 (100µF): Near HC-SR04 connector VCC pin
   - C2 (100nF): Parallel with C1 for high-frequency noise

3. Keep TRIG and ECHO traces separated
   - Prevent crosstalk between output and input signals
   - Route on opposite sides of board if possible

4. HC-SR04 connector placement:
   - Board edge for easy access
   - Away from BNC connectors (avoid physical interference)
```

**Trace Routing:**
```
- TRIG trace: Can be thin (0.3mm/12mil) - digital output
- ECHO trace: Should be short, 0.3mm minimum
- Keep voltage divider on same side as ESP32 header
- Use ground plane underneath for noise immunity
```

---

## 6. Float Switch Interface

```
Float Switch - FLOW (low level alarm):
        3.3V
         │
        R1
       10k (pullup)
         │
GPIO0 ───┼──────────────► Float Switch (FLOW) ──► GND
         │
        C1
       100nF (debounce)
         │
        ─┴─
        GND

Float Switch - HIGH (high level cutoff):
        3.3V
         │
        R1
       10k (pullup)
         │
GPIO1 ───┼──────────────► Float Switch (HIGH) ──► GND
         │
        C1
       100nF (debounce)
         │
        ─┴─
        GND
```

---

## 7. Pump Driver Circuits

All pumps and the ATO valve use the same 12V rail and identical driver circuits.

### 7.1 12V Main Pump Driver

```
                                    12V
                                     │
                        ┌────────────┤
                        │            │
                       D1          PUMP+
                    (SS34)          │
                        │          PUMP
                        │           │
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q1            ├───┴── PUMP-
        │      │  IRLZ44N       │
        │      │                │
        │      └───────┬────────┘
        │           SOURCE
        │              │
       R2             ─┴─
      100Ω            GND
        │
        │
GPIO10 ─┼────────┬─────────────────► Gate Drive
                 │
                R1
               10k
                 │
                ─┴─
                GND

Q1: IRLZ44N (Logic-level N-MOSFET)
- Vds = 55V, Id = 47A
- Vgs(th) = 1-2V (works with 3.3V logic)

D1: SS34 (3A Schottky flyback diode)
```

### 7.2 12V Dosing Pump Drivers (×4)

```
Same circuit as main pump, all on 12V rail.
Use separate MOSFET for each dosing pump.

GPIO11 ──► Pump pH Up
GPIO15 ──► Pump pH Down
GPIO19 ──► Pump Nutrient A
GPIO20 ──► Pump Nutrient B
```

### 7.3 ATO Solenoid Valve Driver

```
Same circuit as dosing pumps, connected to 12V rail.
Uses normally-closed (NC) solenoid valve for fail-safe operation.

GPIO7 ──► ATO Solenoid Valve (12V NC)

                                    12V
                                     │
                        ┌────────────┤
                        │            │
                       D1         VALVE+
                    (SS34)          │
                        │         VALVE
                        │        (NC)
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q6            ├───┴── VALVE-
        │      │  IRLZ44N       │
        │      │                │
        │      └───────┬────────┘
        │           SOURCE
        │              │
       R2             ─┴─
      100Ω            GND
        │
        │
GPIO7 ──┼────────┬─────────────────► Gate Drive
                 │
                R1
               10k
                 │
                ─┴─
                GND

Solenoid Valve Selection:
- Type: Normally Closed (NC) - fails safe (closed when power off)
- Voltage: 12V DC
- Current: 300-500mA typical
- Connection: 1/2" NPT or hose barb
- Material: Food-safe (brass or plastic body, EPDM seals)

Safety Notes:
- NC valve ensures no water flow if controller loses power
- Float switch (GPIO1 - FLOAT_HIGH) provides hardware backup cutoff
- Float switch (GPIO0 - FLOAT_FLOW) provides low-level alarm
- Software timeout prevents flooding if level sensor fails
```

---

## 8. Status LED (WS2812B)

```
        5V ──────┬────────────────────► VDD
                 │
               C1
              100nF
                 │
               ─┴┬─
              GND│
                 │
                 │    ┌─────────────┐
        GPIO13 ──┴──► │ DIN         │
                      │   WS2812B   │
                      │             │
        GND ────────► │ VSS         │
                      └─────────────┘

Note: WS2812B runs at 5V but data line works with 3.3V logic
      Add 100Ω series resistor on data line for signal integrity
```

---

## 9. Optional OLED Display

```
SSD1306 128x64 I2C OLED

4-pin header (2.54mm):
┌─────────────────────────┐
│ Pin 1: GND ──► GND      │
│ Pin 2: VCC ──► 3.3V     │
│ Pin 3: SCL ──► I2C_SCL  │
│ Pin 4: SDA ──► I2C_SDA  │
└─────────────────────────┘

I2C Address: 0x3C (default)
```

---

## 10. PCB Layout Guidelines

### 10.1 Layer Stack (2-layer)
- Top: Signal + Power
- Bottom: Ground plane (solid)

### 10.2 Critical Routing
1. Keep power traces wide (1mm min for logic, 2mm+ for pump circuits)
2. Star ground from single point near power input
3. Keep analog (I2C sensors) away from switching circuits
4. Keep 40mm clearance around ESP32-C6 antenna (no copper on top layer)

### 10.3 Connector Placement
- Power input on one edge
- Pump outputs grouped together
- BNC connectors on opposite edge from power
- USB-C accessible for programming

### 10.4 Thermal Considerations
- Add thermal vias under MOSFET source pads
- Use large copper pours for heatsinking
- Consider heatsinks on MOSFETs if continuous pump operation

---

## 11. Test Points

Add test points for debugging:
- TP1: 3.3V
- TP2: 5V
- TP3: 12V
- TP4: GND
- TP5: I2C SDA
- TP6: I2C SCL
- TP7: 1-Wire
