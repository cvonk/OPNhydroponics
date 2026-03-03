# Atlas Scientific EZO Isolated Circuit Design

> **✅ PROJECT DECISION:** OPNhydro will use **Option B: ADM3260** for EZO sensor isolation.
>
> **Selected: Option B - Analog Devices ADM3260** ✅ (Single-Chip Solution)
> - Integrated I2C isolator + DC-DC converter in one chip
> - 150mW isolated power, 1 MHz I2C, 2500 VRMS isolation
> - Requires 2 ferrite beads (BLM15HD182SN1) for optimal EMC
> - Reference: [EVAL-ADM3260MEBZ User Guide (UG-724)](https://www.analog.com/media/en/technical-documentation/user-guides/EVAL-ADM3260MEBZ_UG-724.pdf)
> - **Selected for:** Smallest PCB footprint, single-chip simplicity
> - **Total System Cost:** ~$204-205 (excluding probes)
>
> **Alternative: Option C - Recom RM-3.33.3S + TI ISO1640BDR** (Two-Chip Solution)
> - Separate DC-DC (RM-3.33.3S) + I2C isolator (ISO1640BDR)
> - 76mA isolated power, 1.7 MHz I2C, 3000 VRMS isolation
> - Standard components only (no specialized ferrite beads)
> - **Pros:** Higher I2C speed, higher isolation, standard components
> - **Cons:** Two chips, larger footprint (+$6 more expensive)
> - Documented as alternative option in this guide
>
> **⚠️ DESIGN NOTE:** Previously considered ISOW7741/ISOW7841, but these use unidirectional
> digital isolator channels (3 forward + 1 reverse) which are not suitable for bidirectional I2C.
> The selected ADM3260 provides proper bidirectional I2C isolation.

This document describes the galvanic isolation circuit for connecting Atlas Scientific EZO sensor boards (pH, EC, RTD) to the ESP32-C6 via I2C.

## What are EZO Mezzanine Boards?

Atlas Scientific EZO circuits are **intelligent probe interface modules** that sit between the raw sensor probe and your microcontroller. They are called "mezzanine boards" because they act as an intermediate layer in the system.

### Core Functions of EZO Circuits

**1. Signal Conditioning**
- High-impedance input buffer (>1TΩ) that doesn't load the probe
- Precision amplification of tiny probe signals (pH: ~59mV per pH unit)
- Advanced noise filtering and signal processing

**2. Analog-to-Digital Conversion**
- 16-bit precision ADC built-in
- Converts analog probe signals to accurate digital readings
- Handles temperature compensation automatically

**3. Data Processing and Communication**
- Stores calibration data in non-volatile EEPROM
- Performs automatic temperature compensation
- Provides simple I2C or UART interface to microcontroller
- Implements Atlas Scientific's standardized command protocol

**4. Why You Can't Connect Probes Directly to ESP32**

```
pH Probe Characteristics:
- Output: ~59mV per pH unit (very small voltage)
- Impedance: >100MΩ (extremely high)
- ESP32 ADC: 50kΩ input impedance
- Result: Would load the probe and give completely wrong readings

EC Probe Requirements:
- Needs AC excitation signal (1-10kHz)
- Measures impedance, calculates conductivity
- ESP32 cannot generate precise AC and measure impedance simultaneously

DO Probe Complexity:
- Optical: LED excitation + fluorescence phase detection
- Galvanic: µA-level currents requiring precision conversion
- Requires specialized optics and timing circuits
```

### EZO Circuit Block Diagram

```
┌─────────────────────────────────────────────────────┐
│         Atlas Scientific EZO Circuit                │
│                                                     │
│  BNC Input ──► High-Z Buffer ──► Precision Amp ──►  │
│                                                     │
│  ──► Temp Compensation ──► 16-bit ADC ──►           │
│                                                     │
│  ──► Microcontroller ──► I2C/UART Interface ──►     │
│       - Calibration engine                          │
│       - Data filtering                              │
│       - EEPROM storage                              │
│                                                     │
│  Simple I2C Command: "R" → Returns: "7.02"          │
└─────────────────────────────────────────────────────┘
```

### What EZO Boards Replace

Without EZO circuits, you would need to design:
- ❌ High-impedance instrumentation amplifiers
- ❌ Precision 16-bit ADCs
- ❌ AC excitation circuits (for EC probes)
- ❌ Temperature compensation algorithms (Nernst equation for pH)
- ❌ Calibration storage and management
- ❌ Multi-point calibration interpolation
- ❌ Signal filtering and noise rejection

**The EZO boards cost ~$48-58 but save weeks/months of analog design work** and provide proven, reliable sensor interfaces used in thousands of commercial and research applications.

---

## Why Isolation is Required

Atlas Scientific **strongly recommends** galvanic isolation when using multiple EZO circuits measuring the same solution to prevent:
- Ground loops between sensors
- Measurement interference
- Cross-contamination of readings
- Electrochemical interactions between probes

Without isolation, multiple probes in the same solution will create galvanic cells that interfere with accurate measurements.

---

## Design Overview

Each isolated EZO circuit (pH, EC) requires:
1. **Isolated DC-DC converter** - Provides isolated 3.3V power
2. **I2C isolator** (optional) - Isolates I2C communication
3. **BNC connector** - For probe connection
4. **Decoupling capacitors** - Power supply filtering
5. **Isolated ground plane** - Separate from main PCB ground

---

## Full Isolation Circuit (Recommended)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          NON-ISOLATED SIDE                                 │
│                                                                            │
│   3.3V ──┬────────────────────► To other I2C devices                       │
│          │                                                                 │
│          │    ┌───────────────────────────────────────┐                    │
│          │    │   Isolated DC-DC Converter            │                    │
│          │    │   B0303S-1WR2 (1W, 3.3V→3.3V)         │                    │
│          │    │                                       │                    │
│         ─┴─   │  VIN ─────────────────────────► VOUT  │                    │
│   C1   100nF  │                                       │                    │
│         ─┬─   │   GND ─┐                    ┌───► GND │                    │
│         GND   └────────┼────────────────────┼─────────┘                    │
│                        │                    │                              │
│                    ┌───┴────────────────────┴───┐ Isolation Barrier        │
│════════════════════════════════════════════════════════════════════════════│
│                    │                            │                          │
│   ┌────────────────┴────────────────────────────┴─────────────────────┐    │
│   │                    ISOLATED SIDE                                  │    │
│   │                                                                   │    │
│   │   3.3V_ISO ──┬────────┬────────────────────────────────► VCC      │    │
│   │              │        │                                           │    │
│   │             ─┴─      ─┴─                                          │    │
│   │       C2   100nF   100nF  C3                                      │    │
│   │             ─┬─      ─┬─                                          │    │
│   │            GND_ISO  GND_ISO                                       │    │
│   │                                                                   │    │
│   │              ┌─────────────────────────────────┐                  │    │
│   │              │   Atlas Scientific EZO-pH       │                  │    │
│   │              │   (Carrier Board)               │                  │    │
│   │              │                                 │                  │    │
│   │  3.3V_ISO ──►│ VCC                             │                  │    │
│   │  GND_ISO  ──►│ GND                             │                  │    │
│   │              │                                 │                  │    │
│   │   SDA_ISO ──►│ SDA    Address: 0x63 (default)  │                  │    │
│   │   SCL_ISO ──►│ SCL                             │                  │    │
│   │              │                                 │                  │    │
│   │              │ PRB ────────────────────────────┼──────────► BNC   │    │
│   │              │         (pH probe connection)   │           Panel  │    │
│   │              └─────────────────────────────────┘           Mount  │    │
│   │                                                                   │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Selection

### 1. Isolated DC-DC Converter Options

#### Option A: B0303S-1WR2 (Simple, Cost-Effective) ⚠️ OFAC Restricted

⚠️ **EXPORT COMPLIANCE WARNING:** This component is on OFAC's SDN List. Not recommended.

```
Specifications:
- Manufacturer: Mornsun or XP Power
- Input:  3.3V ±10%
- Output: 3.3V @ 300mA (1W)
- Isolation: 1000VDC
- Efficiency: ~75%
- Package: SIP-7
- Cost: ~$5-8 USD
- Availability: RESTRICTED - OFAC SDN List

Pinout (Top View):
  ┌─────────────┐
  │ B0303S-1WR2 │
  │             │
1 │ VIN         │ 7  +VOUT
2 │ VIN         │ 6  +VOUT
3 │ GND (in)    │ 5  GND (out)
4 │ GND (in)    │ 5  GND (out)
  └─────────────┘

Notes:
- Pins 1-2 are internally connected (VIN)
- Pins 3-4 are internally connected (GND_in)
- Pins 5-6 are isolated GND_out
- Pins 6-7 are isolated VOUT
```

#### Option B: ISOW7841 (All-in-One) ✅ Recommended for OPNhydro

```
Specifications:
- Manufacturer: Texas Instruments
- Integrated I2C isolation + isolated power
- Input: 3.0-5.5V
- Output: 3.3V @ 150mA
- Isolation: 5000Vrms
- I2C Speed: Up to 1MHz
- Single chip solution
- Package: SOIC-16W
- Cost: ~$3-5 USD

Advantages:
- Single chip replaces DC-DC + I2C isolator
- Lowest component count (3 components total)
- Smallest PCB footprint
- Integrated I2C pullups
- Lowest total cost ($3-5 vs $9-14)
- Fastest I2C speed (1MHz vs 400kHz)
- Simplest assembly

Disadvantages:
- Lower output current (150mA vs 300mA)
  Note: This is still plenty for single EZO circuit (~30-50mA)
- Requires careful PCB layout (wider SOIC-16W package)
```

---

### ISOW7841 vs ISOW7741 Comparison (TI Integrated Isolators)

Both are single-chip I2C isolators with integrated DC-DC power from Texas Instruments.

| Feature | **ISOW7741** 💰 | **ISOW7841** ✅ |
|---------|-----------------|-----------------|
| **Isolated Power Output** | 100mA max | 150mA max |
| **Input Voltage** | 3.0-5.5V | 3.0-5.5V |
| **Output Voltage** | 3.3V regulated | 3.3V regulated |
| **Isolation Rating** | 5000Vrms | 5000Vrms |
| **I2C Speed** | Up to 1MHz | Up to 1MHz |
| **Package** | SOIC-16W | SOIC-16W |
| **Pin Compatible** | Yes | Yes |
| **Cost (DigiKey)** | ~$2.50-3.50 | ~$3.50-5.00 |
| **Cost Savings** | **$1.00-1.50 cheaper** | - |
| **Power Efficiency** | ~70% | ~70-75% |

**EZO Circuit Power Requirements:**

```
Single EZO Circuit Current Draw:
─────────────────────────────────────────
Operating Mode    | Current | ISOW7741 Margin | ISOW7841 Margin
──────────────────┼─────────┼─────────────────┼────────────────
Active (reading)  | 20-35mA | 65-80mA (65%)   | 115-130mA (77%)
Idle (sleep)      | 5-10mA  | 90-95mA (90%)   | 140-145mA (93%)
With N-FET off    | <1µA    | 100mA (>99%)    | 150mA (>99%)
─────────────────────────────────────────────────────────────

Conclusion:
✅ ISOW7741 (100mA) is MORE than adequate for single EZO circuit
✅ ISOW7841 (150mA) provides extra margin but not necessary
```

**Which to Choose?**

**Choose ISOW7741 if:** 💰 Lower cost priority
- Building multiple units (cost per board matters)
- 100mA is sufficient for single EZO circuit (35mA max)
- Want to minimize BOM cost
- **Savings: ~$3-4.50 for 3 circuits (pH, EC, DO)**

**Choose ISOW7841 if:** 🛡️ Safety margin priority
- Want maximum design margin (150mA vs 100mA)
- Future-proofing for potential higher-power EZO variants
- Using OLED display on same isolated power rail
- Extra $1 per circuit is acceptable

**Recommendation for OPNhydro:**

```
Option 1: ADM3260 (Recommended) ✅ BEST CHOICE
──────────────────────────────────────────────────
- Proper bidirectional I2C isolation (not unidirectional)
- Integrated DC-DC converter (150mW) - single chip solution
- 150mW is more than adequate (35mA @ 3.3V = 115mW max)
- Proven design with extensive application notes
- Hot-swap capable
- Cost: ~$5-6 per circuit
- Isolation: 2500Vrms
- I2C Speed: Up to 1MHz (ADM3260E variant)
- Reference: EVAL-ADM3260MEBZ User Guide (UG-724)

Option 2: ISOW7741/ISOW7841 ⚠️ NOT RECOMMENDED
─────────────────────────────────────────────────
- Uses unidirectional digital isolator channels (3 forward + 1 reverse)
- Not designed for bidirectional I2C operation
- Would require complex wiring or external circuitry
- Push-pull outputs incompatible with I2C open-drain
- Better alternatives exist (ADM3260, ISO1540+DC-DC)
```

**Part Numbers:**

```
ISOW7741 (100mA):
─────────────────────────────────────────────────────────────
Recommended: ISOW7741BDFMR ✅ (Standard Industrial Grade)
- Temperature Range: -40°C to +105°C
- DigiKey P/N: 296-ISOW7741BDFMR-ND
- Mouser P/N: 595-ISOW7741BDFMR
- Cost: $8.94 USD

Alternative: ISOW7741FBDFMR (Automotive Grade - NOT needed for OPNhydro)
- Temperature Range: -40°C to +125°C (extra +20°C)
- Qualification: AEC-Q100 automotive
- DigiKey P/N: 296-ISOW7741FBDFMR-ND
- Mouser P/N: 595-ISOW7741FBDFMR
- Cost: $9.15 USD (+$0.21 premium)
- Only needed for: Outdoor extreme heat, automotive, or safety-critical apps

Temperature Grade Comparison:
- "B" variant: -40°C to +105°C (sufficient for hydroponics) 💰
- "FB" variant: -40°C to +125°C (automotive grade, overkill)
- Indoor hydroponics typically: 15-40°C (well within both ranges)

ISOW7841 (150mA):
─────────────────────────────────────────────────────────────
- Full Part: ISOW7841DFMR (SOIC-16W)
- Temperature Range: -40°C to +125°C
- DigiKey P/N: 296-38846-1-ND
- Mouser P/N: 595-ISOW7841DFMR
- Cost: ~$10-12 USD

Note: All variants are pin-compatible (same SOIC-16W footprint)
```

**Final Recommendation:**

**Use ADM3260ARMZ** ✅ (Hot-Swappable I2C Isolator with Integrated DC-DC)
- Proper bidirectional I2C isolation (vs ISOW77xx unidirectional channels)
- Integrated 150mW DC-DC converter - no external B0303S needed
- Single chip solution - simplest design, smallest footprint
- 150mW is sufficient for single EZO circuit (35mA @ 3.3V = 115mW max)
- Proven industrial design with extensive app notes
- Temperature range: -40°C to +85°C (perfect for indoor hydroponics 15-40°C)
- Reference design: [EVAL-ADM3260MEBZ User Guide (UG-724)](https://www.analog.com/media/en/technical-documentation/user-guides/EVAL-ADM3260MEBZ_UG-724.pdf)

**Part Numbers:**

```
ADM3260 (150mW isolated power, bidirectional I2C):
─────────────────────────────────────────────────────────────
Recommended: ADM3260ARMZ ✅ (Standard variant)
- Temperature Range: -40°C to +85°C
- Package: 20-lead SSOP
- DigiKey P/N: ADM3260ARMZ-ND
- Mouser P/N: 584-ADM3260ARMZ
- Cost: ~$5.50-6.00 USD

Alternative: ADM3260ARMZ-RL7 (Tape & Reel)
- Same specs as above
- DigiKey P/N: ADM3260ARMZ-RL7-ND
- For production quantities (500+ units)

Variant with Integrated Pull-ups:
ADM3260EARMZ (has integrated I2C pull-ups on isolated side)
- Saves external pull-up resistors
- DigiKey P/N: ADM3260EARMZ-ND
- Cost: ~$6.00-6.50 USD
```

---

#### Option C: ADM3260 (Integrated I2C + DC-DC) ✅ RECOMMENDED

```
Specifications:
- Manufacturer: Analog Devices
- Single-chip I2C isolator WITH integrated DC-DC converter
- Input: 3.0V to 5.5V
- Output: 3.15V to 5.25V @ 150mW isolated power
- Isolation: 2500Vrms
- I2C Speed: Up to 1MHz (with ADM3260E variant)
- Package: 20-lead SSOP
- Cost: ~$5-6 USD
- Reference Design: EVAL-ADM3260MEBZ (UG-724)

Advantages:
- ✅ Proper bidirectional I2C (not unidirectional channels)
- ✅ Integrated isolated DC-DC converter (no external B0303S needed)
- ✅ Single chip solution (simplest design)
- ✅ 150mW power sufficient for EZO circuits (35mA @ 3.3V = 115mW)
- ✅ Proven track record in industrial applications
- ✅ Extensive application notes available
- ✅ Multiple variants (ADM3260/ADM3260E with pullups)
- ✅ Hot-swap capable
- ✅ Robust design for harsh environments

Disadvantages:
- Slightly higher cost than ISOW77xx (~$5-6 vs $3-5)
- More components required (8 vs 3)
- Larger PCB footprint
- Lower I2C speed (400kHz vs 1MHz)
- More complex assembly and routing
- More BOM management (two different isolators)

When to use ADM3260:
- Need >150mA on isolated side (multiple devices)
- Industrial/commercial product requirements
- Already using ADM3260 in other designs
- Extreme reliability/longevity requirements
```

### 2. I2C Isolator (if using B0303S-1WR2)

#### ISO1540 / ISO1541 (Texas Instruments) ✓ Recommended

```
Specifications:
- Bidirectional I2C isolation
- Supports 100kHz / 400kHz / 1MHz
- Supply: 2.25V to 5.5V
- Isolation: 2500Vrms / 5000Vrms
- Package: SOIC-8
- Cost: ~$2-4 USD

Features:
- ISO1540: No internal pullups (use external)
- ISO1541: Integrated 1.2kΩ pullups (VCC2 side)
- Hot-swap capable
- Failsafe outputs
```

#### ADUM1250 / ADUM1251 (Analog Devices)

```
Specifications:
- Bidirectional I2C isolation
- Supports 100kHz / 400kHz
- Isolation: 2500Vrms
- Package: SOIC-8
- Cost: ~$3-5 USD

Features:
- ADUM1250: No internal pullups
- ADUM1251: Integrated pullups
- iCoupler technology (magnetic isolation)
```

#### ADM3260 / ADM3260E (Analog Devices)

```
Specifications:
- Bidirectional I2C isolation
- Supports 100kHz / 400kHz (NOT 1MHz)
- Supply: 2.7V to 5.5V
- Isolation: 2500Vrms
- Package: SOIC-16 (wider package)
- Cost: ~$4-6 USD

Features:
- ADM3260: No internal pullups (use external)
- ADM3260E: Integrated pullups on VISO side
- Hot-swap capable
- Temperature range: -40°C to +125°C
- Proven industrial design

Note: ADM3260 is a well-established design with extensive application
      notes, but offers lower I2C speed (400kHz vs 1MHz) and higher
      cost compared to ISO1540. Best for industrial applications
      requiring proven reliability.
```

---

## Current Consumption Specifications

Understanding the current draw of EZO circuits and probes is critical for selecting appropriate isolation components and power supplies.

### EZO Circuit Current Draw

All Atlas Scientific EZO circuits have similar current consumption characteristics:

```
EZO-pH Circuit:
- Active Reading: 20-30mA (during measurement)
- Idle Mode: 5-10mA (waiting for command)
- Sleep Mode: ~1mA (low power state enabled via "Sleep" command)
- Average: ~25mA during normal I2C operation
- Peak: 30mA maximum

EZO-EC Circuit:
- Active Reading: 25-35mA (higher due to AC excitation of EC probe)
- Idle Mode: 5-10mA
- Sleep Mode: ~1mA
- Average: ~30mA during normal operation
- Peak: 35mA maximum

EZO-DO Circuit (Optical):
- Active Reading: 20-30mA
- Idle Mode: 5-10mA
- Sleep Mode: ~1mA
- Average: ~25mA during normal operation
- Peak: 30mA maximum
```

### Probe Current Draw

The probes themselves consume negligible current - they are passive sensors:

```
pH Probe:
- Current: <1 µA (essentially ZERO)
- Impedance: >100 MΩ (extremely high impedance voltage source)
- The EZO circuit provides high-impedance buffering
- Probe is a voltage source, not a current consumer

EC Probe:
- Current: <1mA (only during measurement when AC excitation is applied)
- Between measurements: 0mA
- The EZO circuit generates the AC excitation signal

DO Probe (Optical):
- Current: 0mA (passive optical sensing)
- LED excitation provided by EZO circuit
- The probe is purely optical, no electrical connection to solution
```

### Power Budget Analysis

**Per Isolated Channel (worst case):**
```
Single EZO Circuit + Probe:
- EZO circuit: 30mA (peak)
- Probe: <1mA (negligible)
- Total per channel: ~30mA maximum
```

**ISOW7841 Power Capacity Verification:**
```
ISOW7841 Specifications:
- Maximum isolated output current: 150mA @ 3.3V
- Single EZO circuit load: 30mA
- Utilization: 30mA / 150mA = 20%
- Headroom: 120mA (80% unused capacity)
- Conclusion: ✅ ISOW7841 has more than sufficient capacity
```

**Complete System (3 isolated sensors):**
```
Three Isolated Channels:
- pH channel: 30mA max (dedicated ISOW7841)
- EC channel: 35mA max (dedicated ISOW7841)
- DO channel: 30mA max (dedicated ISOW7841)
- Total isolated power: 95mA (each powered by dedicated isolator)
- Total draw from ESP32 3.3V rail: ~100mA for all three isolators

ESP32-C6 3.3V Rail Capacity:
- Typical USB power: 500mA available
- ESP32-C6 consumption: ~50-150mA (depending on WiFi/BLE activity)
- EZO system: 100mA
- Headroom: 250-400mA remaining
- Conclusion: ✅ Sufficient power budget
```

### Power Optimization

For battery-powered applications, EZO circuits can be put into sleep mode:

```c
// Put EZO circuits to sleep between readings
void sleep_ezo_circuits(void) {
    ezo_send_command(I2C_EZO_PH, "Sleep");
    ezo_send_command(I2C_EZO_EC, "Sleep");
    ezo_send_command(I2C_EZO_DO, "Sleep");
    // Current drops from 90mA to 3mA total
}

// Wake up before taking readings
void wake_ezo_circuits(void) {
    // Any I2C transaction wakes the circuit
    ezo_send_command(I2C_EZO_PH, "Status");
    vTaskDelay(pdMS_TO_TICKS(10)); // Allow wake-up time
}

// Example power-saving measurement cycle:
// 1. Circuits sleep: 3mA for 60 seconds = 50µAh
// 2. Wake + measure: 90mA for 2 seconds = 50µAh
// 3. Total per minute: 100µAh (vs 1500µAh if always active)
// 4. Power savings: 93% reduction
```

### B0303S-1WR2 Power Capacity (Alternative Design)

If using the B0303S-1WR2 DC-DC converter instead of ISOW7841:

```
B0303S-1WR2 Specifications:
- Maximum isolated output current: 300mA @ 3.3V
- Single EZO circuit load: 30mA
- Utilization: 30mA / 300mA = 10%
- Headroom: 270mA (90% unused capacity)
- Conclusion: ✅ Significant overcapacity (could power multiple EZO per isolator)
```

### Key Takeaways

✅ **ISOW7841 is more than adequate** for single EZO circuit per isolator (20% utilization)

✅ **pH/EC/DO probes consume negligible current** (<1mA) - all power is consumed by the EZO circuit electronics

✅ **System total: ~100mA** for three isolated sensors (easily powered by ESP32 3.3V rail)

✅ **Sleep mode available** for battery-powered applications (reduces consumption from 90mA to 3mA)

✅ **No thermal concerns** - Low power dissipation means no heatsinking required for any component

---

## Isolator Comparison

### Side-by-Side Comparison

| Feature | **Option B: ADM3260** ✅ | **Option C: RM-3.33.3S + ISO1640BDR** | **ISOW7841** ⚠️ |
|---------|-------------------------|--------------------------------------|----------------|
| **Status** | **SELECTED** ✅ | Alternative | Not Recommended |
| **Solution Type** | All-in-One | I2C + Power (2-chip) | All-in-One |
| **I2C Type** | **Bidirectional** | **Bidirectional** | **Unidirectional** |
| **Chip Count** | 1 | 2 | 1 |
| **Isolated Power** | 150mW @ 3.3V | 76mA @ 3.3V | 150mA @ 3.3V |
| **I2C Speed** | Up to 1MHz | **Up to 1.7MHz** | 1MHz max |
| **Isolation Voltage** | 2500Vrms | **3000Vrms** | 5000Vrms |
| **Package** | 20-lead SSOP | SIP-4 + SOIC-8 | SOIC-16W |
| **Built-in Pullups** | ADM3260E option | External required | Yes |
| **Hot Swap** | Yes | Yes (ISO1640) | Yes |
| **Cost per Circuit** | **~$5.75** | ~$7.75 | ~$9-11 |
| **PCB Footprint** | **Smallest** | Medium | Smallest |
| **BOM Complexity** | Ferrite beads needed | **Standard parts only** | Unidirectional I2C |
| **Selection Reason** | **Smallest footprint** | Higher speed/isolation | Not for I2C |
| **Temperature Range** | -40 to +125°C | -40 to +125°C | -40 to +125°C |
| **Proven Track Record** | Recent design | Well established | Very established |

---

### Alternative: SI8600 + RFM-0505 Solution

**Component Overview:**
- **SI8600** (Silicon Labs): 6-channel digital isolator (I2C + GPIOs)
- **RFM-0505S** (RECOM): 5V→5V isolated DC-DC converter (1W, 200mA)
- **AMS1117-3.3**: 3.3V LDO regulator (requires on isolated side)

```
Circuit Architecture:

Non-Isolated Side:                      Isolated Side:
─────────────────                       ──────────────

3.3V ──► Level up to 5V                 5V_ISO ──► AMS1117 ──► 3.3V_ISO
         (resistor divider                              │
         or level shifter)                             ─┴─ EZO-pH VCC
         │                                             GND_ISO
         │
         ▼
    ┌─────────────┐                    ┌─────────────┐
5V ─┤             │                    │             ├─► 5V_ISO
    │  RFM-0505S  │                    │  SI8600     │
GND─┤  (DC-DC)    │                    │  (Digital   ├─► SDA_ISO
    └─────────────┘                    │  Isolator)  ├─► SCL_ISO
                                       │             │
SDA ────────────────────────────────►  │ SDA1   SDA2 ├─► To EZO
SCL ────────────────────────────────►  │ SCL1   SCL2 │
                                       └─────────────┘
```

**Detailed Specifications:**

**SI8600 Digital Isolator (Silicon Labs):**
```
Part Number: SI8600EC-B-IS (common variant)
Channels: 6 channels (configurable direction)
Data Rate: Up to 150 Mbps
Propagation Delay: 3ns typical
Isolation Voltage: 5000 Vrms (1 minute), 2500 Vrms (continuous)
Package: SOIC-16 (narrow body, 10.3mm × 7.5mm)
Operating Temperature: -40°C to +125°C
Supply Voltage: 1.8V - 5.5V (each side independent)
Supply Current: 1.2mA per channel typical (@ 1 Mbps)
I2C Support: Yes (open-drain compatible with external pullups)
Cost: ~$2.50-4.00 USD

Note: SI8600 requires external pullup resistors on both sides
      (similar to ISO1540, does NOT have integrated pullups)

I2C Configuration:
- Use 2 channels (SDA, SCL)
- Bidirectional capable
- Requires 4.7kΩ pullups on both sides
- Maximum I2C speed: ~1 MHz (limited by propagation delay)
```

**RFM-0505S Isolated DC-DC Converter (RECOM):**
```
Part Number: RFM-0505S
Input Voltage: 4.5V - 5.5V (nominal 5V)
Output Voltage: 5V ±10%
Output Current: 200mA maximum (1W)
Isolation Voltage: 1000 VDC
Efficiency: 76% typical
Regulation: ±1% (regulated output)
Package: SIP-7 (19.5mm × 9.8mm × 11.2mm)
Operating Temperature: -40°C to +85°C
Cost: ~$4-6 USD

CRITICAL ISSUE: ❌ OPNhydro uses 3.3V system
- RFM-0505S is 5V input → 5V output
- Requires TWO conversions:
  1. 3.3V → 5V boost converter (input side)
  2. 5V_ISO → 3.3V_ISO LDO regulator (output side)
- This adds complexity, cost, and inefficiency

Alternative: RFM-0303S (3.3V → 3.3V) - DISCONTINUED by RECOM
```

**Required Additional Components:**
```
1. Boost Converter (3.3V → 5V for RFM-0505S input):
   - TPS61200 boost converter or similar
   - Input caps, inductor, diode
   - Cost: ~$1.50 + passives
   - PCB space: ~15mm × 15mm

2. LDO Regulator (5V_ISO → 3.3V_ISO for EZO):
   - AMS1117-3.3 or LD1117V33
   - Input/output caps (10µF each)
   - Cost: ~$0.30 + caps
   - PCB space: ~8mm × 8mm

3. I2C Pullup Resistors:
   - 4× 4.7kΩ resistors (both sides of SI8600)
   - Cost: ~$0.20
```

**Complete SI8600 + RFM-0505S Design:**

| Feature | **SI8600 + RFM-0505S** | **ISOW7841** ✅ |
|---------|----------------------|-----------------|
| **Solution Type** | Multi-chip (4 ICs) | All-in-One |
| **Chip Count** | 4 (SI8600 + RFM-0505S + Boost + LDO) | 1 |
| **Isolated Power Output** | 200mA @ 5V (requires LDO → 3.3V) | 150mA @ 3.3V (native) |
| **Effective 3.3V Output** | ~165mA (after LDO dropout) | 150mA (direct) |
| **I2C Speed** | 1MHz (with careful layout) | 1MHz |
| **Isolation Voltage** | 1000VDC + 5000Vrms | 5000Vrms |
| **Package** | SOIC-16 + SIP-7 + SOT-223 + MSOP-8 | SOIC-16W |
| **Built-in Pullups** | No (external 4.7kΩ required) | Yes |
| **Hot Swap** | Yes | Yes |
| **Cost per Circuit** | **~$11-15** | **~$3-5** |
| **PCB Footprint** | **~800mm²** (very large) | **~200mm²** (compact) |
| **Design Complexity** | **Very High** (4 ICs, boost converter) | **Very Simple** (1 IC) |
| **Power Efficiency** | **~50-55%** (3.3V→5V→5V_ISO→3.3V_ISO) | **~70-75%** (direct) |
| **Component Count** | ~15 components | ~3 components |
| **BOM Line Items** | 8-10 unique parts | 2-3 unique parts |
| **Assembly Complexity** | High (SMD + through-hole mix) | Low (SMD only) |
| **Temperature Range** | -40 to +85°C (limited by RFM-0505S) | -40 to +125°C |
| **Supply Voltage** | Requires 5V rail (needs boost) | 3.3V native |
| **Proven Track Record** | SI8600: Established, RFM: Legacy | Recent but TI-backed |

**Power Efficiency Comparison:**

```
ISOW7841 Power Path:
    3.3V_ESP32 ──► [ISOW7841: 70-75% efficient] ──► 3.3V_ISO @ 150mA
    Input: 3.3V × 150mA / 0.72 = 689mW
    Loss: ~239mW (heat dissipation)

SI8600 + RFM-0505S Power Path:
    3.3V_ESP32 ──► [Boost: 85%] ──► 5V @ 200mA
                   ──► [RFM-0505S: 76%] ──► 5V_ISO @ 200mA
                   ──► [LDO: 66%] ──► 3.3V_ISO @ 150mA

    Input: 3.3V × (150mA × 3.3V / 5V) / 0.85 / 0.76
         ≈ 3.3V × 193mA = 637mW (boost input)
    Total efficiency: 3.3V × 150mA / 637mW = 78%

    BUT: More stages = more heat in multiple locations
    AND: Requires careful thermal design for LDO
```

**Cost Breakdown (per isolated circuit):**

```
SI8600 + RFM-0505S Solution:
────────────────────────────
- SI8600EC-B-IS digital isolator    : $3.00
- RFM-0505S isolated DC-DC           : $5.00
- TPS61200 boost converter           : $1.50
- AMS1117-3.3 LDO regulator          : $0.30
- Boost inductor 4.7µH               : $0.15
- Boost diode SS14                   : $0.05
- 4× 4.7kΩ pullup resistors          : $0.20
- 6× 100nF ceramic caps              : $0.60
- 2× 10µF ceramic caps (LDO)         : $0.40
- 2× 10µF ceramic caps (boost)       : $0.40
- BNC connector                      : $3.00
────────────────────────────────────────────
Total per circuit:                   ~$14.60

ISOW7841 Solution:
──────────────────
- ISOW7841DFMR                       : $4.00
- 3× 100nF ceramic caps              : $0.30
- BNC connector                      : $3.00
────────────────────────────────────────────
Total per circuit:                    ~$7.30

Savings with ISOW7841: $7.30 per circuit
Savings for 3 circuits: ~$22 total
```

**PCB Footprint Comparison:**

```
ISOW7841 Layout:
┌─────────────────────────────┐
│  [ISOW7841]  [C1][C2][C3]   │  ← 20mm × 10mm = 200mm²
│   SOIC-16W    0805 caps     │
└─────────────────────────────┘

SI8600 + RFM-0505S Layout:
┌────────────────────────────────────────────┐
│  [Boost Conv]  [RFM-0505S]  [SI8600]  [LDO]│
│   15×15mm       20×10mm     10×7mm    8×8mm│  ← 40mm × 20mm = 800mm²
│  [L][D][Caps]     [Caps]    [4×R]   [Caps] │
└────────────────────────────────────────────┘

PCB area increase: 4× larger footprint
```

**Advantages of SI8600 + RFM-0505S:**
```
✓ Higher isolated current capacity (200mA vs 150mA)
  - Could power 2× EZO circuits per isolator
  - Useful for future expansion

✓ SI8600 is very well established (>10 years in production)
  - Extensive application notes and support
  - Used in thousands of industrial designs

✓ Flexible channel configuration
  - 6 channels (can add extra signals if needed)
  - Could add enable pins, status flags, etc.

✓ Regulatory isolation (5000Vrms on SI8600)
  - Meets stringent industrial/medical standards
  - Better for commercial products requiring certifications
```

**Disadvantages of SI8600 + RFM-0505S:**
```
✗ Much higher cost ($14.60 vs $7.30 per circuit)
  - 2× more expensive than ISOW7841
  - Multiplied by 3 circuits = $22 extra for system

✗ Requires 5V rail (OPNhydro is 3.3V system)
  - Need boost converter on input
  - Need LDO regulator on output
  - Two extra voltage conversions = inefficiency

✗ Complex design with 4 ICs per circuit
  - Boost converter (TPS61200 + L + D + caps)
  - Isolated DC-DC (RFM-0505S)
  - Digital isolator (SI8600)
  - LDO regulator (AMS1117)
  - Total: ~15 components vs 3 for ISOW7841

✗ Larger PCB footprint (4× bigger)
  - 800mm² vs 200mm² per circuit
  - Harder to fit in compact enclosure

✗ More complex assembly and testing
  - Through-hole RFM-0505S (hand soldering or wave)
  - SMD components on both sides potential
  - More points of failure

✗ Lower power efficiency
  - Two extra conversion stages (boost + LDO)
  - More heat dissipation
  - LDO requires heatsinking for 150mA load

✗ Mixed package types (SMD + through-hole)
  - SI8600: SOIC-16 (SMD)
  - RFM-0505S: SIP-7 (through-hole)
  - Boost converter: MSOP-8 (SMD)
  - LDO: SOT-223 (SMD)
  - Complicates PCB assembly
```

**Alternative: SI8600 + RFM-0303S (IDEAL, but unavailable)**

```
If RECOM still made RFM-0303S (3.3V → 3.3V):

Advantages:
✓ No boost converter needed (3.3V input)
✓ No LDO regulator needed (3.3V output)
✓ Simpler design (only 2 ICs + passives)
✓ Better efficiency (~76% vs 55%)
✓ Lower cost (~$8 vs $14.60)

Unfortunately:
✗ RFM-0303S DISCONTINUED by RECOM
✗ Alternatives exist but are expensive:
  - RECOM RO-0303S: $8-12 (2W, overkill)
  - Murata MGJ2 series: $10-15 (medical grade)
  - These negate the cost advantage
```

### When to Use SI8600 + RFM-0505S

**Use SI8600 + RFM-0505S when:**
1. **Already have 5V rail in system**
   - No boost converter needed
   - Only need LDO for 3.3V_ISO
   - Reduces complexity significantly

2. **Need >150mA per isolated channel**
   - Powering 2+ EZO circuits per isolator
   - Future expansion requirements
   - Note: OPNhydro uses 30mA, so this is overkill

3. **Require extra isolated GPIO channels**
   - SI8600 has 6 channels (I2C uses 2)
   - 4 extra channels for enable pins, status, etc.
   - ISOW7841 only isolates I2C

4. **Industrial/commercial certification required**
   - SI8600 has extensive regulatory approvals
   - Proven track record in certified products
   - Note: Hobby projects don't need this

5. **Design reuse from existing SI8600 projects**
   - Already familiar with Silicon Labs parts
   - Existing PCB libraries and footprints

**DO NOT use SI8600 + RFM-0505S for OPNhydro because:**
❌ 2× cost ($14.60 vs $7.30 per circuit)
❌ 4× larger PCB footprint
❌ Requires boost converter (3.3V system)
❌ Requires LDO regulator (inefficiency)
❌ 15 components vs 3 (complexity)
❌ Lower power efficiency (55% vs 72%)
❌ No performance benefit (both support 1MHz I2C)
❌ Overkill current capacity (200mA vs needed 30mA)

### Recommendation by Use Case

| Application | Best Choice | Reason |
|-------------|------------|--------|
| **OPNhydro (hobby/DIY)** | ISOW7841 | Lowest cost, simplest design, adequate performance |
| **Single EZO per isolation** | ISOW7841 | All-in-one solution, minimal components |
| **Multiple EZO per isolation** | B0303S + ADM3260 | Higher current capacity (300mA) |
| **Industrial/commercial** | B0303S + ADM3260 | Proven reliability, extensive app notes |
| **Budget prototype** | B0303S only | Power isolation only (partial protection) |
| **High-speed I2C (>400kHz)** | ISOW7841 or ISO1540 | 1MHz I2C support |

### Cost Analysis (3 Isolated Circuits)

```
ISOW7841 Solution:
- 3× ISOW7841 @ $4 = $12
- 6× 100nF caps @ $0.10 = $0.60
- 3× BNC connector @ $3 = $9
- Total: ~$21.60 (excluding EZO boards)

B0303S + ISO1540 Solution:
- 3× B0303S-1WR2 @ $6 = $18
- 3× ISO1540 @ $3 = $9
- 12× 4.7kΩ resistors = $0.60
- 12× 100nF caps = $1.20
- 3× BNC connector @ $3 = $9
- Total: ~$37.80 (excluding EZO boards)

B0303S + ADM3260 Solution:
- 3× B0303S-1WR2 @ $6 = $18
- 3× ADM3260E @ $5 = $15
- 12× 4.7kΩ resistors = $0.60
- 12× 100nF caps = $1.20
- 3× BNC connector @ $3 = $9
- Total: ~$43.80 (excluding EZO boards)

SI8600 + RFM-0505S Solution:
- 3× SI8600EC-B-IS @ $3 = $9.00
- 3× RFM-0505S @ $5 = $15.00
- 3× TPS61200 boost converter @ $1.50 = $4.50
- 3× AMS1117-3.3 LDO @ $0.30 = $0.90
- 3× Boost inductor 4.7µH @ $0.15 = $0.45
- 3× SS14 diode @ $0.05 = $0.15
- 12× 4.7kΩ resistors = $0.60
- 18× 100nF ceramic caps @ $0.10 = $1.80
- 12× 10µF ceramic caps @ $0.20 = $2.40
- 3× BNC connector @ $3 = $9.00
- Total: ~$43.80 (excluding EZO boards)

Savings with ISOW7841: $16-22 for complete system
Cost disadvantage of SI8600+RFM: Same as B0303S+ADM3260 (~$22 more)
```

---

## Detailed Circuit Schematics

### Power Isolation using B0303S-1WR2

⚠️ **EXPORT COMPLIANCE WARNING:**
**B0303S-1WR2 is affected by OFAC's Specially Designated Nationals and Blocked Persons List (SDN List).**
This component has legal restrictions for purchase/use by US persons and export to certain countries.
**STRONGLY RECOMMEND using ISOW7841 instead** (Texas Instruments, no OFAC restrictions). ✅

```
Non-Isolated 3.3V Side:
────────────────────────────
                 ┌──────────────────────┐
3.3V ────┬──────►│1 VIN          VOUT 7 ├───┬──────► 3.3V_ISO
         │       │2                   6 ├───┤
        ─┴─      │                      │   │
  C1   100nF     │  B0303S-1WR2         │  ─┴─
        ─┬─      │                      │  100nF C2
        GND      │3 GND           GND 5 ├───┬─
                 │4                   4 ├───┤
                 └──────────────────────┘   │
                         │                 ─┴─
                        GND              GND_ISO

Component Values:
- C1: 100nF ceramic X7R 50V (input side)
- C2: 100nF ceramic X7R 50V (output side)
- Optional: Add 10µF tantalum on output for heavy load

Placement:
- C1 within 5mm of pins 1-4
- C2 within 5mm of pins 5-7
- Minimize trace length
```

### Complete EZO-pH Connection with B0303S-1WR2

```
Isolated Side (3.3V_ISO):
─────────────────────────────────────────────────

Power Distribution:
                3.3V_ISO ──────┬─────► To EZO-pH VCC
                               │
                          ┌────┴────┐
                          │         │
                         ─┴─       ─┴─
                   C3   100nF   10µF  C4 (tantalum, optional)
                         ─┬─       ─┬─
                       GND_ISO   GND_ISO

I2C Bus with Pullups:
                3.3V_ISO
                    │
               ┌────┴────┐
               │         │
              R1        R2
             4.7k      4.7k
               │         │
    SDA_ISO ───┼─────────┴──────────► To EZO-pH SDA
               │
    SCL_ISO ───┴────────────────────► To EZO-pH SCL

EZO-pH Board Connection:
             ┌──────────────────────────────────┐
             │  Atlas Scientific EZO-pH Circuit │
             │                                  │
     3.3V_ISO│► VCC   (red wire)                │
      GND_ISO│► GND   (black wire)              │
      SDA_ISO│► SDA   (I2C address 0x63)        │
       SCL_ISO│► SCL                            │
             │                       PRB ►──────┼──► To BNC
             └──────────────────────────────────┘

BNC Probe Connection:
┌──────────────────────────────┐
│  BNC Panel Mount Connector   │
│  (Female, PCB mount)         │
│                              │
│     ┌───┐                    │
│     │ ● │ ◄─────────────────────── pH Probe (BNC male plug)
│     └───┘                    │         (Atlas Scientific probe)
│      │                       │
│      └─── Shield ──► GND_ISO │
└──────────────────────────────┘

Notes:
- Use quality BNC connector (Amphenol or TE Connectivity)
- Shield connection to GND_ISO prevents EMI
- Keep BNC traces short and direct
```

### I2C Isolation using ISO1540

```
Complete I2C + Power Isolation:

Non-Isolated Side:                    Isolated Side:
──────────────────                    ──────────────

Power Rails and Pullups:
    3.3V                                  3.3V_ISO
     │                                       │
     ├──────┬──────┬──────────              ├──────┬──────┬──────
     │      │      │                        │      │      │
   [R1]   [R2]   [C1]                     [R3]   [R4]   [C2]
   4.7k   4.7k   100nF                    4.7k   4.7k   100nF
     │      │      │                        │      │      │
    SDA    SCL    GND                     SDA_ISO SCL_ISO GND_ISO
     │      │                                │      │
     │      │                                │      │
I2C Bus Connections to ISO1540:
                          ┌────────────┐
     SDA ────────────────►│1 SDA1  SDA2│8├──────────► SDA_ISO ──► To EZO-pH
    (from ESP32 + R1)     │            │
                          │            │
     SCL ────────────────►│2 SCL1  SCL2│7├──────────► SCL_ISO ──► To EZO-pH
    (from ESP32 + R2)     │            │
                          │  ISO1540   │
    3.3V ────────────────►│3 VCC1  VCC2│6├──────────► 3.3V_ISO
                          │            │
     GND ────────────────►│4 GND1  GND2│5├──────────► GND_ISO
                          └────────────┘

IMPORTANT - Pullup Resistor Connections:
- R1: Connected between 3.3V and SDA (NOT to GND!)
- R2: Connected between 3.3V and SCL
- R3: Connected between 3.3V_ISO and SDA_ISO
- R4: Connected between 3.3V_ISO and SCL_ISO
- These pull the I2C lines HIGH (I2C uses open-drain signaling)
- ● symbol = connection node where multiple signals meet

Component Values:
- R1, R2: 4.7kΩ (non-isolated side pullups)
- R3, R4: 4.7kΩ (isolated side pullups)
- All resistors: 1% tolerance, 0805 package
- Decoupling caps: 100nF ceramic X7R

Why 4.7kΩ Pullups?
- I2C uses open-drain (devices only pull LOW, never drive HIGH)
- Pullup resistors provide the HIGH logic level
- 4.7kΩ chosen for 400kHz I2C with ~400pF bus capacitance
- RC time constant: 4.7k × 400pF = 1.88µs (acceptable rise time)

Alternative: Use ISO1541 (has internal pullups on VCC2 side)
- Eliminates R3, R4 (built-in 1.2kΩ pullups)
- Slightly lower cost
```

### ADM3260 Integrated I2C Isolator + DC-DC (✅ RECOMMENDED)

```
Single Chip: Bidirectional I2C Isolation + Integrated DC-DC Converter

Reference: EVAL-ADM3260MEBZ User Guide (UG-724)
           https://www.analog.com/media/en/technical-documentation/user-guides/EVAL-ADM3260MEBZ_UG-724.pdf

ESP32 Side (Non-Isolated):          EZO Side (Isolated):
──────────────────────────          ────────────────────

    3.3V                                 VISO (3.3V_ISO)
     │                                      │
     ├────┬────                            ├────┬────
     │    │                                │    │
   100nF 10µF  ◄── VDD1 decoupling       100nF 10µF  ◄── VISO decoupling
   C1    C2       (per UG-724)           C3    C4       (per UG-724)
     │    │                                │    │
    GND  GND                             GND  GND
     │                                      │
     │    ┌──────────────────────┐          │
     ├───►│1  VDD1        VISO 20├──────────┤
     │    │                      │          │
     │    │12 VDD2       VISOIN19├──[FB1]───┤  ◄── Ferrite bead for DC-DC
     │    │                      │          │      (BLM15HD182SN1)
     │    │                      │          │
 SDA─┼───►│6  SDA1        SDA2 15├──────────┼───► SDA_ISO ──► EZO SDA
     │    │                      │          │
 SCL─┼───►│8  SCL1        SCL2 13├──────────┼───► SCL_ISO ──► EZO SCL
     │    │                      │          │
     │    │   ADM3260ARMZ        │          │
     │    │   (20-lead SSOP)     │          │
     │    │                      │     [FB2]◄── Ferrite bead on isolated GND
     │    │                      │      │       (BLM15HD182SN1)
 GND─┴───►│10 GND1   GND2 11,14  ├──────┴───┴───► GND_ISO ──► EZO GND
          │                      │
          └──────────────────────┘

Component Values (per UG-724 reference design):
- C1, C3: 0.1µF (100nF) ceramic X7R, 0805 package (place <1mm from pins)
- C2, C4: 10µF ceramic X7R, 0805 package (place close to pins)
- FB1: Murata BLM15HD182SN1 ferrite bead (Pin 12 to Pin 19)
  - High-impedance characteristics for DC-DC noise filtering
  - Prevents common-mode noise on isolated power rail
- FB2: Murata BLM15HD182SN1 ferrite bead (Pins 11/14 to GND plane)
  - Prevents common-mode noise from radiating on isolated ground
- Optional: 4.7kΩ pull-ups on SDA/SCL (use ADM3260E for integrated pull-ups)

Critical Layout Notes (per UG-724):
⚠️ Pin 12 (VDD2) must connect to Pin 19 (VISOIN) through ferrite bead FB1
⚠️ Pins 11/14 (GND2) should connect to ground plane through ferrite bead FB2
⚠️ Keep decoupling capacitors as close as possible to their respective pins
⚠️ Maintain proper isolation spacing on PCB between non-isolated and isolated sides

Key Features:
✅ Bidirectional I2C isolation (proper I2C, not unidirectional channels)
✅ Integrated isolated DC-DC converter (150mW @ 3.3V isolated output)
✅ Single chip solution - no external B0303S needed
✅ Hot-swap capable
✅ 2500Vrms isolation rating
✅ Up to 1MHz I2C speed
✅ Temperature: -40°C to +85°C

Advantages:
✅ Simplest single-chip design (vs ISOW77xx problematic I2C)
✅ Proven industrial track record (widely used)
✅ Proper bidirectional I2C support
✅ 150mW power sufficient for EZO (35mA @ 3.3V = 115mW)
✅ Extensive application notes and reference designs
✅ Multiple variants (ADM3260/ADM3260E)

Power Output:
- VISO: 3.15V to 5.25V regulated output
- Maximum: 150mW isolated power
- EZO load: ~115mW (35mA @ 3.3V)
- Margin: ~30% headroom

Use ADM3260 when:
✅ Need proper bidirectional I2C isolation
✅ Want single-chip integrated solution
✅ Need proven industrial-grade design
✅ Want hot-swap capability
✅ Building commercial/industrial products
```

---

### Option B: Recom RM-3.33.3S + TI ISO1640BDR (Two-Chip Solution)

```
Two Chips: Isolated DC-DC + Bidirectional I2C Isolator

Reference: Recom RM-3.33.3S Datasheet + ISO1640 Datasheet
           https://www.ti.com/lit/ds/symlink/iso1640.pdf

ESP32 Side (Non-Isolated):          EZO Side (Isolated):
──────────────────────────          ────────────────────

    3.3V                                 3.3V_ISO
     │                                      │
     │    ┌──────────────┐                  │
     ├───►│1 VIN   VOUT 4├──────────────────┼──► 3.3V_ISO (76mA max)
     │    │              │                  │
     │    │  RM-3.33.3S  │                  ├────┬────
     │    │   (SIP-4)    │                  │    │
     │    │              │                10µF  0.1µF  ◄── Output caps
 GND─┼───►│2 GND    GND 3├──────────┐       │    │       (typical)
     │    └──────────────┘          │      GND  GND
     │                               │       │
     ├────┬────                      │       │
     │    │                          │       │
   10µF  0.1µF  ◄── Input caps       │       │
     │    │       (typical)          │       │
    GND  GND                         │       │
     │                               │       │
     │    ┌──────────────────────┐   │       │
     ├───►│1  VCC1        VCC2  8├───┼───────┤
     │    │                      │   │       │
 SDA─┼───►│2  SDA1        SDA2  7├───┼───────┼───► SDA_ISO ──► EZO SDA
     │    │                      │   │       │
 SCL─┼───►│4  SCL1        SCL2  5├───┼───────┼───► SCL_ISO ──► EZO SCL
     │    │                      │   │       │
     │    │   ISO1640BDR         │   │       │
     │    │   (SOIC-8)           │   │       │
 GND─┴───►│3  GND1        GND2  6├───┴───────┴───► GND_ISO ──► EZO GND
          │                      │
          └──────────────────────┘

I2C Pull-up Resistors (4.7kΩ):
     3.3V                            3.3V_ISO
      │                                 │
      ├────┬────                       ├────┬────
      │    │                           │    │
    4.7k 4.7k                         4.7k 4.7k
      │    │                           │    │
     SDA  SCL                        SDA_ISO SCL_ISO

Component Values:
- RM-3.33.3S input: 10µF + 0.1µF ceramic X7R (typical for SIP DC-DC)
- RM-3.33.3S output: 10µF + 0.1µF ceramic X7R (typical for SIP DC-DC)
- ISO1640 VCC1, VCC2: 0.1µF ceramic X7R (per datasheet)
- Pull-ups: 4× 4.7kΩ resistors (both sides)

Key Features:
✅ Proper bidirectional I2C isolation (not unidirectional channels)
✅ Higher I2C speed: Up to 1.7 MHz (vs 1 MHz for ADM3260)
✅ Higher isolation: 3000 VRMS (vs 2500 VRMS for ADM3260)
✅ Enhanced EMC performance
✅ Hot-swap capable (ISO1640)
✅ Standard components only - no specialized ferrite beads
✅ Temperature: -40°C to +85°C

Advantages:
✅ Simpler BOM - all standard capacitors and resistors
✅ No specialized ferrite beads required
✅ Higher I2C speed and isolation ratings
✅ Enhanced EMC (ISO1640 vs ISO1540)
✅ Proven industrial designs (both chips widely used)
✅ Easy to source - common components

Disadvantages:
⚠️ Two chips instead of one
⚠️ Lower power output (76mA vs 150mA) - but sufficient for EZO (35mA)
⚠️ Slightly larger PCB footprint
⚠️ More soldering/assembly

Power Output:
- RM-3.33.3S: 3.3V @ 76mA (0.25W)
- EZO load: ~115mW (35mA @ 3.3V)
- Margin: 76mA - 35mA = 41mA (54% headroom)
- Sufficient for single EZO per isolator

Use RM-3.33.3S + ISO1640BDR when:
✅ Want simpler BOM with standard components only
✅ Need higher I2C speed (>1 MHz)
✅ Need higher isolation voltage (3000 VRMS)
✅ Prefer to avoid specialized ferrite beads
✅ Assembly simplicity is priority
✅ Building DIY/hobby projects with easy-to-source parts
```

---

### ISOW7741/ISOW7841 (⚠️ NOT RECOMMENDED for I2C)

⚠️ **Design Note:** ISOW77xx family uses unidirectional digital isolator channels (3 forward + 1 reverse),
which are not ideal for bidirectional I2C communication. Use ADM3260 instead for proper I2C isolation.

```
ISOW7841 - Single Chip but Problematic for I2C:

         ┌─────────────────────────────────────┐
         │            ISOW7841                 │
         │       (SOIC-16W package)            │
         │                                     │
3.3V ───►│1  VCC1                     VCC2  16 ├──┬──► 3.3V_ISO ──► EZO-pH VCC
    ┌───►│2  GND1                     GND2  13 ├──┼──► GND_ISO ──► EZO-pH GND
    │    │                                     │  │
 SDA├───►│6  SDA1                     SDA2  11 ├──┼──► SDA_ISO ──► EZO-pH SDA
    │    │                                     │  │
 SCL├───►│5  SCL1                     SCL2  12 ├──┼──► SCL_ISO ──► EZO-pH SCL
    │    │                                     │  │
 GND├───►│4  (other GND pins)                  │  │
    │    └─────────────────────────────────────┘  │
    │                                             │
   ─┴─                                  ┌─────────┴─────────┐
   GND                                  │  Decoupling Caps  │
                                        │                   │
                                   3.3V_ISO ──┬──► 100nF ──┬──► GND_ISO
                                              │            │
                                             ─┴─          ─┴─
                                            10µF         GND_ISO
                                            (optional)

Pinout Summary:
Pin 1:  VCC1  (3.3V input)
Pin 2:  GND1
Pin 3:  EN    (enable, tie to VCC1 for always-on)
Pin 4:  GND1
Pin 5:  SCL1  (input from ESP32)
Pin 6:  SDA1  (input from ESP32)
Pin 7:  GND1
Pin 8:  N/C

Pin 9:  N/C
Pin 10: GND2
Pin 11: SDA2  (output to EZO)
Pin 12: SCL2  (output to EZO)
Pin 13: GND2
Pin 14: READY (output status)
Pin 15: GND2
Pin 16: VCC2  (3.3V isolated output, 150mA max)

Features:
- No external components needed (except decoupling caps)
- Built-in pullup resistors
- Hot-swap protection
- Failsafe outputs
- Undervoltage lockout
```

---

### TI Reference Design: Additional Filtering Components

**Reference: TI SLAU845** - ISOW77xx Evaluation Module User's Guide

The TI SLAU845 application note provides the authoritative reference design. Here's the analysis:

```
TI Reference Design (per SLAU845):
──────────────────────────────────────────────

Input Side (Non-Isolated):          Output Side (Isolated):
─────────────────────────           ────────────────────────

    Input Side:                       Output Side (Isolated):

    3.3V (VDD)                        3.3V_ISO (VDD)
     │                                      │
     │                                     [FB] Ferrite Bead ◄── Only on OUTPUT
     ├──────┬─────                         │
     │      │                              ├──────┬─────
   [C1]   [C2]                            [C4]   [C5]
   10nF   10µF   ◄── VCC1/2 power         10nF   10µF   ◄── VCC1/2 power
  (VDD)  (VDD)                           (VDD)  (VDD)
     │      │                              │      │
    ─┴─    ─┴─                            ─┴─    ─┴─
   GND    GND                           GND_ISO GND_ISO

    3.3V (VIO)                        3.3V_ISO (VIO)
     │                                      │
    [C3]                                   [C6]
   100nF   ◄── VIO1/2 I/O power           100nF   ◄── VIO1/2 I/O power
   (VIO)                                  (VIO)
     │                                      │
    ─┴─                                    ─┴─
   GND                                   GND_ISO

Key Points:
- Ferrite bead ONLY on isolated output (VCC2)
- VDD domain (VCC1/VCC2): 10nF + 10µF per side for DC-DC converter
- VIO domain (VIO1/VIO2): 100nF per side for I2C I/O power
- All capacitors are MLCC X7R ceramic
- Follows TI SLAU845 reference implementation
```

#### Component Analysis:

**Capacitors:**

```
┌─────────────┬──────────┬─────────────┬────────────────┬─────────────────┐
│ Component   │ Value    │ Type        │ Pin/Purpose    │ Recommendation  │
├─────────────┼──────────┼─────────────┼────────────────┼─────────────────┤
│ C1/C4       │ 10nF     │ MLCC X7R    │ VDD (VCC1/2)   │ ✅ REQUIRED     │
│ C2/C5       │ 10µF     │ MLCC X7R    │ VDD (VCC1/2)   │ ✅ REQUIRED     │
│ C3/C6       │ 100nF    │ MLCC X7R    │ VIO (VIO1/2)   │ ✅ REQUIRED     │
└─────────────┴──────────┴─────────────┴────────────────┴─────────────────┘

Per TI SLAU845 Reference Design:

VDD Power (DC-DC Converter):
──────────────────────────────
C1, C4 (10nF / 0.01µF):
- REQUIRED - HF bypass for VCC1/VCC2 pins
- Place within 1mm of VCC pin (critical!)
- Handles high-frequency switching currents from DC-DC
- Ceramic X7R or C0G/NP0 (C0G preferred for 10nF)
- 0805 or 0603 package
- Cost: ~$0.05 each

C2, C5 (10µF):
- REQUIRED - Bulk capacitance for VCC1/VCC2
- Place within 2-4mm of VCC pin
- Handles load switching and DC-DC transients
- Ceramic MLCC X7R
- 0805 package
- Cost: ~$0.30 each

VIO Power (I2C Digital Isolator):
──────────────────────────────────
C3, C6 (100nF / 0.1µF):
- REQUIRED - Decoupling for VIO1/VIO2 pins
- Place as close to pin as possible (<1mm ideal)
- Filters logic-level noise on I2C signals
- Ceramic MLCC X7R
- 0805 package
- Cost: ~$0.08 each
```

**Ferrite Beads (per TI SLAU845):**

```
┌─────────────┬──────────┬────────────┬─────────────────┐
│ Component   │ Value    │ Location   │ Recommendation  │
├─────────────┼──────────┼────────────┼─────────────────┤
│ FB (Output) │ 100Ω@100MHz│ VCC2 only│ ⚠️ OPTIONAL   │
└─────────────┴──────────┴────────────┴─────────────────┘

Per TI SLAU845 Reference Design:
- Ferrite bead ONLY on isolated output (VCC2)
- NOT on input side (VCC1)
- Filters DC-DC switching noise before it reaches EZO circuits

Purpose:
- Filter high-frequency switching noise from internal DC-DC converter
- Prevent switching artifacts from coupling into EZO analog circuits
- Switching noise is generated inside ISOW7741 and appears on VCC2
- Input side (VCC1) already has clean regulated 3.3V from ESP32

Typical Part: Murata BLM18PG101SN1D (0603, 100Ω@100MHz, $0.10)
Alternative: Any 100-300Ω@100MHz ferrite bead in 0603/0805 package

When to use:
✅ Commercial product (EMC compliance)
✅ Maximum measurement accuracy required
✅ Shared power rails with multiple EZO circuits
✅ Near RF transmitters (WiFi/Bluetooth on ESP32)
⚠️ Prototyping (add if noise issues found)
❌ Simple DIY build (probably not needed initially)
```

#### Recommendations for OPNhydro:

**Standard Build (per TI SLAU845):** ✅
```
Input Side:                    Output Side (Isolated):
  3.3V (VDD)                      3.3V_ISO (VDD)
   │                                │
   ├────┬────                       ├────┬────
   │    │                           │    │
  10nF 10µF  ◄── VCC1/2 power      10nF 10µF  ◄── VCC1/2 power
  C1   C2                          C4   C5
   │    │                           │    │
  GND  GND                       GND_ISO GND_ISO

  3.3V (VIO)                      3.3V_ISO (VIO)
   │                                │
  100nF  ◄── VIO1/2 I/O power      100nF  ◄── VIO1/2 I/O power
  C3                               C6
   │                                │
  GND                            GND_ISO
                                    │
                                    └──► To EZO pH/EC/DO

Components (per TI SLAU845 reference):
- C1, C4: 10nF (VCC1/VCC2) - within 1mm of pin
- C2, C5: 10µF (VCC1/VCC2) - within 2-4mm of pin
- C3, C6: 100nF (VIO1/VIO2) - as close as possible to pin
- All capacitors MLCC X7R ceramic
- No ferrite bead in standard build
- Total cost: ~$0.86 per circuit (6 caps)
```

**Enhanced Build (with output ferrite bead):** ⚡
```
Input Side:                    Output Side (Isolated):
  3.3V (VDD)                      3.3V_ISO (VDD)
   │                                │
   │                               [FB] ◄── Ferrite bead (output only)
   ├────┬────                       │
   │    │                           ├────┬────
  10nF 10µF  ◄── VCC1/2 power      10nF 10µF  ◄── VCC1/2 power
  C1   C2                          C4   C5
   │    │                           │    │
  GND  GND                       GND_ISO GND_ISO

  3.3V (VIO)                      3.3V_ISO (VIO)
   │                                │
  100nF  ◄── VIO1/2 I/O power      100nF  ◄── VIO1/2 I/O power
  C3                               C6
   │                                │
  GND                            GND_ISO
                                    │
                                    └──► To EZO pH/EC/DO

Additional Components (per TI SLAU845):
- FB: ONE ferrite bead per circuit (output side only)
- Murata BLM18PG101SN1D (0603, 100Ω@100MHz)
- Total added cost: +$0.10 per circuit
- Benefits: Filters DC-DC switching noise at source

Use enhanced build if:
- Building commercial product (EMC compliance)
- Maximum measurement accuracy required
- Shared power rails between multiple EZO circuits
- Can be added later if noise issues detected
```

**Maximum Build (Overkill for most):** ⚠️
```
As shown in datasheet with 100µF electrolytics
- Only needed for extreme noise environments
- Not recommended unless specific problems found
- Adds cost and board space unnecessarily
```

#### BOM Impact:

```
Standard Build (per TI SLAU845):
- C1, C4: 10nF ceramic (2× @ $0.05 = $0.10) ◄── VDD (VCC1/VCC2)
- C2, C5: 10µF ceramic (2× @ $0.30 = $0.60) ◄── VDD (VCC1/VCC2)
- C3, C6: 100nF ceramic (2× @ $0.08 = $0.16) ◄── VIO (VIO1/VIO2)
- Total per circuit: $0.86
- Total for 3 circuits: $2.58

Enhanced Build (with output ferrite bead):
- Add: 1× ferrite bead (output only) @ $0.10 = $0.10
- Total per circuit: $0.96
- Total for 3 circuits: $2.88
- Benefit: Filters DC-DC switching noise, EMI compliance

Specific Parts (per TI SLAU845):
- C1, C4: Murata GRM21BR71A103KA01L (0805, 10nF X7R) - VDD domain
- C2, C5: Murata GRM21BR71A106KE15L (0805, 10µF X7R) - VDD domain
- C3, C6: Murata GRM21BR71H104KA12L (0805, 100nF X7R) - VIO domain
- FB (output): Murata BLM18PG101SN1D (0603, 100Ω@100MHz)

Reference: TI SLAU845 - ISOW77xx Evaluation Module User's Guide
```

#### Final Recommendation:

**For OPNhydro:**

1. **Use standard TI reference design** (VDD + VIO power domains)
   - VDD domain (VCC1/VCC2): 10nF + 10µF per side for DC-DC converter
   - VIO domain (VIO1/VIO2): 100nF per side for I2C I/O power
   - Follows manufacturer recommendations exactly
   - Proven design for stable operation

2. **Add ferrite beads if:**
   - Building commercial product (EMC compliance)
   - Notice EMI or measurement noise issues
   - Shared power rails between multiple circuits
   - Can be added later if needed

3. **Capacitor selection tips:**
   - 10nF (VDD): Use within 1mm of pin for high-frequency switching
   - 10µF (VDD): Use within 2-4mm of pin for bulk capacitance
   - 100nF (VIO): Use as close as possible to pin for I/O filtering
   - All capacitors: MLCC X7R ceramic

**Updated schematic with optional ferrite beads in next section.**

---

### Power Management: N-FET Ground Switching

**Inspired by Atlas Scientific EZO Carrier Board Gen 2**

To reduce idle power consumption, add an N-channel MOSFET in the ground return path of each isolated EZO circuit. This allows the ESP32 to completely power down sensors when not in use.

```
ISOW7841 with N-FET Power Control:

         ┌─────────────────────────────────────┐
         │            ISOW7841                 │
         │       (SOIC-16W package)            │
         │                                     │
3.3V ───►│1  VCC1                    VCC2  16 ├──┬──► 3.3V_ISO ──► EZO-pH VCC
    ┌───►│2  GND1                    GND2  13 ├──┤
    │    │                                     │  │
 SDA├───►│6  SDA1                    SDA2  11 ├──┼──► SDA_ISO ──► EZO-pH SDA
    │    │                                     │  │
 SCL├───►│5  SCL1                    SCL2  12 ├──┼──► SCL_ISO ──► EZO-pH SCL
    │    │                                     │  │
 GND├───►│4  (other GND pins)                 │  │
    │    └─────────────────────────────────────┘  │
    │                                             │
   ─┴─                                  ┌─────────┴──────────┐
   GND                                  │  Isolated Ground   │
                                        │  with N-FET Switch │
                                        │                    │
                              3.3V_ISO ─┼──► 100nF ───┬──► GND_ISO
                                        │              │
                                        │             ─┴─
                                        │            10µF
                                        │              │
                         EZO-pH GND ────┴──────────────┤
                                                        │
                                                     ┌──┴──┐
                                                     │  D  │  N-FET
                                    GPIO_EN_PH ─────►│  G  │  (2N7002K)
                                              10kΩ   │  S  │
                                          ┌──────────┤     │
                                          │          └─────┘
                                         ─┴─            │
                                         GND           GND (system ground)
                                       Pull-down

N-FET Switching Circuit Detail:
──────────────────────────────────

                         EZO Circuit (isolated side)
                              │
                              │ GND_ISO
                              │
                              ▼
                         ┌────────┐
                         │    D   │ ◄── Drain to isolated ground
                         │        │
  GPIO_EN_PH (ESP32) ────┤    G   │ ◄── Gate (control signal)
         3.3V logic      │  Q1    │
                         │2N7002K │
                    R1   │    S   │ ◄── Source to system GND
             10kΩ ──┬────┤        │
                    │    └────┬───┘
                   ─┴─        │
                   GND       GND (system ground)

Component Selection:
──────────────────────
Q1: N-channel MOSFET (logic-level) ✅ RECOMMENDED
  - Manufacturer: Nexperia (NXP)
  - Part Number: 2N7002K,215
  - DigiKey P/N: 1727-2521-1-ND
  - Mouser P/N: 771-2N7002K215
  - Package: SOT-23
  - Cost: ~$0.10 USD

  Specifications:
  - VDS(max): 60V
  - ID(max): 300mA continuous (EZO draws ~35mA max)
  - RDS(on): 1.3Ω typ @ VGS=4.5V
            2.5Ω max @ VGS=2.5V (3.3V logic compatible!)
  - VGS(th): 0.9-2.1V (guaranteed logic-level)
  - Power: 350mW
  - Voltage drop: 35mA × 1.3Ω = 45.5mV (negligible)

  Alternatives:
  - BSS138 (ON Semi): More common, slightly higher RDS(on)
  - DMG2302UK-7 (Diodes Inc): Very low RDS(on), higher cost

R1: Pull-down resistor
  - Value: 10kΩ ±5% (ensures FET off when GPIO floating)
  - Power: 1/8W
  - Package: 0805 SMD
  - Part: Generic thick-film resistor
  - Cost: ~$0.01 USD

Optional: R2 gate series resistor (100Ω)
  - Reduces switching noise
  - Prevents oscillation
  - Limits gate charge current
  - Package: 0805 SMD
```

**Power Savings Analysis:**

```
Power Consumption Comparison:
────────────────────────────────────────────────────────
Scenario                    | Current Draw | Power @ 3.3V
────────────────────────────┼──────────────┼─────────────
EZO Circuit (always on)     | 20-35mA      | 66-116mW
EZO Circuit (idle, sleep)   | 5-10mA       | 17-33mW
EZO Circuit (N-FET off)     | <1µA         | <3µW ✓
────────────────────────────┴──────────────┴─────────────

Daily Power Savings (per circuit):
- Assuming 1 reading per hour (active 5 sec/hour)
- Active time: 5 sec × 24 = 120 sec/day = 2 min/day
- Idle time: 24 hours - 2 min = 23h 58min

Without N-FET (always powered):
  23h 58min × 10mA = 239.7 mAh/day

With N-FET (powered only when reading):
  2min × 35mA = 1.17 mAh/day
  23h 58min × 0.001mA = 0.024 mAh/day
  Total: ~1.2 mAh/day

Savings: 239.7 - 1.2 = 238.5 mAh/day per circuit
For 3 circuits (pH, EC, DO): ~715 mAh/day savings
```

**ESP32 Firmware Control:**

```cpp
// GPIO assignments for N-FET power control
#define EZO_PH_ENABLE_PIN  GPIO_NUM_22
#define EZO_EC_ENABLE_PIN  GPIO_NUM_23
#define EZO_DO_ENABLE_PIN  GPIO_NUM_24

// Startup time for EZO circuits (datasheet: 1 second)
#define EZO_POWERUP_DELAY_MS  1200  // 1.2 sec for safety margin

void ezo_power_on(gpio_num_t enable_pin) {
    gpio_set_level(enable_pin, 1);  // Turn on N-FET
    vTaskDelay(pdMS_TO_TICKS(EZO_POWERUP_DELAY_MS));  // Wait for EZO boot
}

void ezo_power_off(gpio_num_t enable_pin) {
    gpio_set_level(enable_pin, 0);  // Turn off N-FET
}

// Example: Read pH with power management
float read_ph_with_power_mgmt(void) {
    ezo_power_on(EZO_PH_ENABLE_PIN);

    // Send temperature compensation
    ezo_send_temp_compensation(i2c_bus, EZO_PH_ADDR, water_temp);
    vTaskDelay(pdMS_TO_TICKS(300));

    // Trigger reading
    ezo_send_command(i2c_bus, EZO_PH_ADDR, "R");
    vTaskDelay(pdMS_TO_TICKS(900));  // EZO pH reading time

    // Read result
    float ph_value = ezo_read_value(i2c_bus, EZO_PH_ADDR);

    ezo_power_off(EZO_PH_ENABLE_PIN);  // Power down until next reading

    return ph_value;
}
```

**Design Considerations:**

```
Pros:
✓ Reduces idle power by >99% (10mA → <1µA per circuit)
✓ Extends battery life significantly if using battery backup
✓ Proven design (used in Atlas Scientific carrier boards)
✓ Simple circuit (one MOSFET + one resistor per circuit)
✓ Low cost (<$0.15 per circuit)
✓ Can disable faulty sensors in software

Cons:
✗ Adds 1.2 second startup delay per reading
✗ EZO circuits lose RAM state when powered off
✗ Requires careful firmware sequencing
✗ Slightly more complex PCB routing

Best For:
- Battery-powered systems
- Infrequent readings (hourly/daily)
- Systems with many EZO circuits
- Cost-sensitive projects

Skip If:
- Mains powered with no power budget concerns
- Need rapid continuous readings (<5 second intervals)
- Prefer maximum simplicity
```

**PCB Routing Notes:**

```
Ground Switching Placement:
──────────────────────────────

Isolated Section:
                    [ISOW7841]
                        │
                  3.3V_ISO  GND2
                        │     │
                        ▼     ▼
                   [EZO-pH Circuit]
                        │     │
                       VCC   GND
                              │
                              │  ◄── GND_ISO (isolated ground)
                              │
                              ▼
                         ┌────────┐
                         │ D      │
  GPIO_EN_PH ───────────►│ G  Q1  │  ◄── Place near isolation barrier
         (3.3V)     R1   │ S      │       Keep traces short
                10kΩ│    └────────┘
                    │         │
                   GND       GND (system ground)

Critical:
- Place Q1 on isolated side of PCB (near GND_ISO pour)
- Keep drain connection to GND_ISO short (<5mm)
- Keep source connection to system GND short
- Gate trace can cross isolation barrier (low current)
- Use ground plane pour for source connection
```

---

## PCB Layout Guidelines

### Board Layout Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    PCB Top View                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         NON-ISOLATED SECTION                        │    │
│  │  (ESP32-C6, main power, other I2C devices)          │    │
│  │                                                     │    │
│  │  Components:                                        │    │
│  │  - ESP32-C6 DevKit headers                          │    │
│  │  - 3.3V power supply                                │    │
│  │  - I2C pullup resistors (if not using isolator)     │    │
│  │  - Other sensors (BME280, BH1750)                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ═══════════════════════════════════════════════════════    │
│  ║  ISOLATION BARRIER - Minimum 5mm clearance          ║    │
│  ═══════════════════════════════════════════════════════    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ISOLATED SECTION - EZO pH                   │    │
│  │                                                     │    │
│  │  Components:                                        │    │
│  │  - B0303S-1WR2 (or ISOW7841)                        │    │
│  │  - ISO1540 I2C isolator (if using B0303S)           │    │
│  │  - EZO-pH circuit board                             │    │
│  │  - BNC panel mount connector                        │    │
│  │  - Decoupling capacitors                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ISOLATED SECTION - EZO EC                   │    │
│  │  (Same layout as pH section)                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ISOLATED SECTION - EZO DO                   │    │
│  │  (Same layout as pH section)                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ground Plane Design

```
Layer Stack (2-layer PCB):

TOP LAYER:
┌───────────────────────────────────────────────────┐
│  Signal traces, components, selective copper      │
│                                                   │
│  GND pour (with keepout around isolation barrier) │
│                                                   │
│  ═══════════ Isolation gap (5mm) ═══════════      │
│                                                   │
│  GND_ISO pour for EZO-pH                          │
│  GND_ISO pour for EZO-EC                          │
│  GND_ISO pour for EZO-DO                          │
└───────────────────────────────────────────────────┘

BOTTOM LAYER:
┌───────────────────────────────────────────────────┐
│  Solid GND plane (non-isolated section)           │
│                                                   │
│  ═══════════ Isolation gap (5mm) ═══════════      │
│                                                   │
│  Solid GND_ISO plane for EZO-pH                   │
│  Solid GND_ISO plane for EZO-EC                   │
│  Solid GND_ISO plane for EZO-DO                   │
└───────────────────────────────────────────────────┘

Critical Rules:
1. GND and GND_ISO planes DO NOT connect (except inside isolator)
2. Minimum 5mm clearance between isolated and non-isolated copper
3. No traces cross the isolation barrier (except through isolator)
4. Thermal reliefs on ground vias to ease soldering
```

### Component Placement

```
Isolated Section Detail (per EZO circuit):

     5mm clearance
         │
         ▼
    ═════════════════════ Isolation Barrier
         │
         │    [C1]        ┌────────────────┐
         │    100nF       │  B0303S-1WR2   │
         │     ●          │  (DC-DC conv)  │
         │                └────────────────┘
         │                        │
         │                    [C2] ● 100nF
         │                        │
         │                ┌───────┴────────┐
         │                │   ISO1540      │
         │                │  (I2C isolator)│
         │                └────────────────┘
         │                        │
         │                    [C3] ● 100nF
         │                        │
         │                ┌───────┴──────────────┐
         │                │   EZO-pH Circuit     │
         │                │  ┌────────────────┐  │
         │                │  │ Atlas PCB      │  │
         │                │  └────────────────┘  │
         │                └──────┬───────────────┘
         │                       │
         │                   ┌───┴───┐
         └───────────────────│  BNC  │  ◄── Board edge
                             └───────┘

Placement Guidelines:
1. C1 within 5mm of DC-DC input pins
2. C2 within 5mm of DC-DC output pins
3. C3 within 5mm of EZO VCC pin
4. Isolator centered between DC-DC and EZO
5. BNC connector at board edge for easy access
6. Keep all components in isolated section
```

### Trace Routing

```
I2C Trace Guidelines:
- Width: 0.3mm minimum (10 mil)
- Spacing: 0.3mm minimum (10 mil)
- Length matching: SDA and SCL within 10mm
- Route parallel where possible
- Avoid routing under BNC connector
- Avoid routing near switching power supply

Power Trace Guidelines:
- 3.3V: 0.5mm width (20 mil) minimum
- GND: Use ground pour, not traces
- 3.3V_ISO: 0.5mm width (20 mil)
- Keep power traces short

Critical Spacing:
- Isolation barrier: 5mm clearance minimum
- High voltage (if present): 2mm clearance
- BNC to digital signals: 5mm spacing
```

### Via Usage

```
Via Specifications:
- Finished hole: 0.3mm (12 mil)
- Pad diameter: 0.6mm (24 mil)
- Solder mask opening: 0.65mm

Via Placement:
- Ground vias: One per component ground pin
- Power vias: One per VCC pin
- Thermal vias under power components
- DO NOT place vias in isolation gap

Thermal Management:
     Component
         │
    ┌────┴────┐
    │         │
    │  [PAD]  │
    │ ● ● ● ● │ ◄── Thermal vias (0.5mm spacing)
    └─────────┘
         │
    GND plane (bottom)
```

---

## Recommended Component Part Numbers

### BNC Connector (Board Edge Mount)

#### TE Connectivity 5227161-6
```
Manufacturer: TE Connectivity (Tyco)
Part Number: 5227161-6
Alternative: CONBNC002 (newer TE part, same specs)
Type: Female BNC, PCB edge mount
Mounting: Through-hole, right-angle
Impedance: 50Ω
Voltage Rating: 500V
Frequency: DC-4GHz
PCB Edge Thickness: 1.57mm (0.062")
Cost: ~$2.50-4.00 USD
Availability: DigiKey, Mouser, Newark

Features:
- Gold-plated contacts
- Beryllium copper shell
- Proven reliability for sensor applications
- Easy hand soldering
- Secure mechanical retention

PCB Footprint:
- Through-hole pins for GND connection
- Requires PCB edge cutout
- Recommended edge clearance: 5mm from components
```

### ISOW7841 Isolator

#### Texas Instruments ISOW7841DFMR
```
Manufacturer: Texas Instruments
Part Number: ISOW7841DFMR (or ISOW7841DFM)
Package: SOIC-16W (10.30mm × 7.50mm)
Pitch: 1.27mm
Cost: ~$3.50-5.00 USD
Availability: DigiKey, Mouser, TI Direct

Alternatives:
- ISOW7841DCAR (SOIC-16 narrow body, different pinout)
- Ensure you select the DFM variant for the wide body SOIC-16

Note: Check TI's parametric search for current availability,
as semiconductor stock fluctuates. The ISOW7841 family has
several package options - verify pinout before ordering.
```

### Decoupling Capacitors

#### 100nF Ceramic Capacitors
```
Manufacturer: Murata, Samsung, Yageo, Kemet
Recommended: Murata GRM21BR71H104KA01L
Package: 0805 (2012 metric)
Capacitance: 100nF (0.1μF)
Voltage: 50V
Dielectric: X7R (stable over temperature)
Tolerance: ±10%
Cost: ~$0.05-0.10 USD each

Alternative (budget): Any X7R or X5R 100nF 50V 0805 capacitor
```

#### 10μF Tantalum Capacitor (Optional)
```
Manufacturer: AVX, Kemet, Vishay
Recommended: AVX TAJB106K010RNJ
Package: SMD Tantalum Case B (3528 metric)
Capacitance: 10μF
Voltage: 10V
Tolerance: ±10%
ESR: Low ESR type
Cost: ~$0.25-0.50 USD

Alternative: 10μF ceramic X5R or X7R if space allows
(larger package, but no polarity concerns)
```

### EZO Circuit Boards

```
Manufacturer: Atlas Scientific
Available from: Atlas-Scientific.com, Amazon, Adafruit, etc.

EZO-pH Circuit:
- Part: ENV-EZO-pH
- Cost: ~$48 USD
- I2C Address: 0x63 (default)

EZO-EC Circuit (Electrical Conductivity):
- Part: ENV-EZO-EC
- Cost: ~$48 USD
- I2C Address: 0x64 (default)

EZO-DO Circuit (Dissolved Oxygen):
- Part: ENV-EZO-DO
- Cost: ~$58 USD
- I2C Address: 0x61 (default)

Note: Purchase EZO circuits without carrier boards
(just the bare EZO circuit board with header pins)
```

### PCB Fabrication Recommendations

```
Recommended PCB Specs:
- Board Thickness: 1.6mm (standard)
- Copper Weight: 1oz (35μm)
- Min Trace/Space: 0.15mm/0.15mm (6/6mil)
- Min Hole Size: 0.3mm
- Surface Finish: ENIG (gold) for BNC reliability
  Alternative: HASL (lead-free) for budget builds

Isolation Barrier Requirements:
- Minimum slot/gap: 0.5mm (larger is better)
- Recommended: 5mm clearance between isolated zones
- Consider ordering "slots" or "cutouts" to physically
  separate GND from GND_ISO planes for maximum isolation

Recommended Fab Houses:
- JLCPCB: Low cost, fast turnaround (~1 week)
- PCBWay: Good quality, reasonable price
- OSH Park: Premium quality, made in USA (slower)
- ALLPCB: Good for prototypes
```

---

## Bill of Materials (BOM)

### Per Isolated EZO Circuit (pH, EC, or DO)

#### Option A: Using B0303S-1WR2 + ISO1540 ⚠️ NOT RECOMMENDED (OFAC Restricted)

⚠️ **B0303S-1WR2 is on OFAC's SDN List** - Legal restrictions apply. Use Option B instead.

| Qty | Reference | Part Number | Description | Package | Cost (USD) |
|-----|-----------|-------------|-------------|---------|------------|
| 1 | U1 | B0303S-1WR2 | Isolated DC-DC (⚠️ OFAC restricted) | SIP-7 | $5-8 |
| 1 | U2 | ISO1540 | I2C Digital Isolator | SOIC-8 | $2-4 |
| 1 | U3 | EZO-pH/EC/DO | Atlas Scientific EZO Circuit | Board | $45-50 |
| 1 | J1 | BNC-F-PCB | BNC Panel Mount Female | - | $2-5 |
| 4 | C1-C4 | 100nF | Ceramic Cap X7R 50V | 0805 | $0.10 ea |
| 1 | C5 | 10µF | Tantalum Cap 10V (optional) | SMD | $0.25 |
| 4 | R1-R4 | 4.7kΩ | Resistor 1% | 0805 | $0.05 ea |
| **Total per circuit** | | | **(without probe)** | | **$55-65** |

#### Option B: Using ADM3260 (Single-Chip: Integrated I2C + DC-DC)

Single-chip solution with proper bidirectional I2C and integrated 150mW DC-DC converter.

| Qty | Reference | Part Number | Description | Package | Cost (USD) |
|-----|-----------|-------------|-------------|---------|------------|
| 1 | U1 | ADM3260ARMZ ✅ | Analog Devices I2C Isolator + DC-DC | 20-lead SSOP | $5.50-6.00 |
| 1 | U1 alt | ADM3260EARMZ | With integrated I2C pull-ups | 20-lead SSOP | $6.00-6.50 |
| 1 | U2 | ENV-EZO-pH/EC/DO | Atlas Scientific EZO Circuit | Board | $48-58 |
| 1 | Q1 | 2N7002K,215 | N-FET for power switching (optional) | SOT-23 | $0.10 |
| 1 | J1 | TE 5227161-6 | BNC Female, PCB edge mount | TH R/A | $2.50-4 |
| 2 | C1, C3 | Generic | 100nF X7R 50V Ceramic (VDD1, VISO) | 0805 | $0.05 ea |
| 2 | C2, C4 | Generic | 10µF X7R 25V Ceramic (VDD1, VISO) | 0805 | $0.30 ea |
| 2 | FB1, FB2 | BLM15HD182SN1 | Murata ferrite bead (per UG-724) | 0603 | $0.15 ea |
| 1 | R1 | Generic | 10kΩ pull-down for Q1 gate (optional) | 0805 | $0.01 |
| 2 | R2, R3 | Generic | 4.7kΩ I2C pull-ups (optional, see notes) | 0805 | $0.05 ea |
| **Total per circuit (standard)** | | | **(per UG-724)** | | **$56-67** |
| **Total per circuit (enhanced)** | | | **(with N-FET switching)** | | **$56.10-67.10** |

Notes:
- Capacitors per EVAL-ADM3260MEBZ User Guide (UG-724):
  - C1: 100nF + C2: 10µF on VDD1 (input power)
  - C3: 100nF + C4: 10µF on VISO (isolated output power)
  - Place as close as possible to pins (<1mm ideal)
- Ferrite beads per UG-724 reference design:
  - FB1: Connect Pin 12 (VDD2) to Pin 19 (VISOIN) - critical for DC-DC operation
  - FB2: Connect Pins 11/14 (GND2) to ground plane - prevents common-mode noise
  - Part: Murata BLM15HD182SN1 (high-impedance characteristics)
- I2C pull-ups:
  - Not needed if using ADM3260EARMZ variant (has integrated pull-ups)
  - Use external 4.7kΩ pull-ups on both sides if using ADM3260ARMZ
- Q1 and R1 are optional for power management (see N-FET Power Switching section)

Reference Design: https://www.analog.com/media/en/technical-documentation/user-guides/EVAL-ADM3260MEBZ_UG-724.pdf

#### Option C: Using Recom RM-3.33.3S + ISO1640BDR (Two-Chip Solution)

Two-chip solution: separate DC-DC converter + I2C isolator with standard components only.

| Qty | Reference | Part Number | Description | Package | Cost (USD) |
|-----|-----------|-------------|-------------|---------|------------|
| 1 | U1 | RM-3.33.3S | Recom Isolated DC-DC 3.3V→3.3V @ 76mA | SIP-4 | $4.00-5.00 |
| 1 | U2 | ISO1640BDR | TI I2C Isolator, 1.7 MHz, 3000 VRMS | SOIC-8 | $3.25 |
| 1 | U3 | ENV-EZO-pH/EC/DO | Atlas Scientific EZO Circuit | Board | $48-58 |
| 1 | Q1 | 2N7002K,215 | N-FET for power switching (optional) | SOT-23 | $0.10 |
| 1 | J1 | TE 5227161-6 | BNC Female, PCB edge mount | TH R/A | $2.50-4 |
| 4 | C1-C4 | Generic | 100nF X7R 50V Ceramic | 0805 | $0.05 ea |
| 2 | C5, C6 | Generic | 10µF X7R 25V Ceramic | 0805 | $0.30 ea |
| 1 | R1 | Generic | 10kΩ pull-down for Q1 gate (optional) | 0805 | $0.01 |
| 4 | R2-R5 | Generic | 4.7kΩ I2C pull-ups (both sides) | 0805 | $0.05 ea |
| **Total per circuit (standard)** | | | **(standard components only)** | | **$58-71** |
| **Total per circuit (with N-FET)** | | | **(with power switching)** | | **$58.11-71.11** |

Notes:
- DC-DC converter (RM-3.33.3S):
  - C5: 10µF on input (VIN)
  - C6: 10µF on output (VOUT)
  - Place close to module pins
- I2C isolator (ISO1640BDR):
  - C1, C2: 0.1µF bypass caps on VCC1, VCC2 (per datasheet)
  - C3, C4: Additional 0.1µF if needed for stability
- I2C pull-ups: 4× 4.7kΩ (both sides of isolation barrier)
- **No ferrite beads required** - all standard components
- Higher I2C speed: 1.7 MHz vs 1 MHz (ADM3260)
- Higher isolation: 3000 VRMS vs 2500 VRMS (ADM3260)

Reference Designs:
- Recom RM-3.33.3S Datasheet
- ISO1640 Datasheet: https://www.ti.com/lit/ds/symlink/iso1640.pdf

#### Option D: Using ISOW77xx ⚠️ NOT RECOMMENDED for I2C

⚠️ **Design Issue:** ISOW7741/ISOW7841 use unidirectional digital isolator channels (3 forward + 1 reverse),
which are not designed for bidirectional I2C. Use ADM3260 instead.

| Qty | Reference | Part Number | Description | Package | Cost (USD) |
|-----|-----------|-------------|-------------|---------|------------|
| 1 | U1 | ISOW7741BDFMR | TI Digital Isolator + DC-DC (⚠️ unidirectional) | SOIC-16W | $8.94 |
| 1 | U1 | ISOW7841DFMR | TI Digital Isolator + DC-DC (⚠️ unidirectional) | SOIC-16W | $10.50 |

Note: Not recommended for I2C applications. Use Option B or Option C for proper bidirectional I2C isolation.

### Complete System (3 isolated circuits: pH, EC, DO)

**Option A Total:** ~$165-195 (without probes) - ⚠️ OFAC restricted (B0303S)
**Option B Total (ADM3260):** ~$168-201 (without probes) - Single chip, needs ferrite beads
**Option C Total (RM-3.33.3S + ISO1640BDR):** ~$174-213 (without probes) - Two chips, standard components
**Option D Total (ISOW77xx):** ~$158-201 (without probes) - ⚠️ NOT RECOMMENDED (unidirectional I2C)

---

## Shopping Lists for Option B and Option C

### Option B: Complete BOM using ADM3260 (Single-Chip)

**Complete BOM for 3 Isolated Sensors using ADM3260:**

| Qty | Part Number | Description | Supplier | Unit Cost | Total |
|-----|-------------|-------------|----------|-----------|-------|
| 3 | ADM3260ARMZ ✅ | Analog Devices I2C Isolator + DC-DC | DigiKey/Mouser | $5.75 | $17.25 |
| - | *or* ADM3260EARMZ | With integrated pull-ups (optional) | DigiKey/Mouser | $6.25 | $18.75 |
| 1 | ENV-EZO-pH | Atlas pH EZO Circuit | Atlas-Scientific | $48.00 | $48.00 |
| 1 | ENV-EZO-EC | Atlas EC EZO Circuit | Atlas-Scientific | $48.00 | $48.00 |
| 1 | ENV-EZO-DO | Atlas DO EZO Circuit | Atlas-Scientific | $58.00 | $58.00 |
| 3 | 5227161-6 | TE BNC Connector (edge mount) | DigiKey/Mouser | $3.00 | $9.00 |
| 3 | 2N7002K,215 | N-FET power switch (optional) | DigiKey/Mouser | $0.10 | $0.30 |
| 6 | Generic | 100nF X7R 50V 0805 Cap (VDD1, VISO) | DigiKey/Mouser | $0.05 | $0.30 |
| 6 | Generic | 10µF X7R 25V 0805 Cap (VDD1, VISO) | DigiKey/Mouser | $0.30 | $1.80 |
| 6 | BLM15HD182SN1 | Murata ferrite bead (per UG-724) | DigiKey/Mouser | $0.15 | $0.90 |
| 3 | Generic | 10kΩ 0805 resistor (pull-down, optional) | DigiKey/Mouser | $0.01 | $0.03 |
| 6 | Generic | 4.7kΩ 0805 I2C pull-ups (if using ADM3260ARMZ) | DigiKey/Mouser | $0.05 | $0.30 |
| 1 | Custom PCB | 2-layer PCB (see specs above) | JLCPCB/PCBWay | $20.00 | $20.00 |

**Cost Comparison (excluding probes):**
| Configuration | ADM3260ARMZ | ADM3260EARMZ (w/ pull-ups) |
|---------------|-------------|----------------------------|
| **Standard (per UG-724)** | **$203.88** 💰 | **$205.38** ✅ |
| **Enhanced (+N-FET)** | **$204.18** | **$205.68** |

**Option B Summary:**
- **Single-chip solution** - smallest footprint
- **Integrated DC-DC converter** - no external isolated power supply needed
- **Requires specialized ferrite beads** (BLM15HD182SN1)
- **I2C Speed:** Up to 1 MHz
- **Isolation:** 2500 VRMS
- **Total cost:** $203.88 (ADM3260ARMZ) or $205.38 (ADM3260EARMZ with integrated pull-ups)
- **Reference:** [EVAL-ADM3260MEBZ UG-724](https://www.analog.com/media/en/technical-documentation/user-guides/EVAL-ADM3260MEBZ_UG-724.pdf)

**Pros:**
✅ Smallest PCB footprint (single chip)
✅ Integrated power + I2C isolation
✅ Hot-swap capable
✅ Proven industrial design

**Cons:**
⚠️ Requires specialized ferrite beads (BLM15HD182SN1)
⚠️ Lower I2C speed (1 MHz)
⚠️ Lower isolation voltage (2500 VRMS)

---

### Option C: Complete BOM using RM-3.33.3S + ISO1640BDR (Two-Chip)

**Complete BOM for 3 Isolated Sensors using RM-3.33.3S + ISO1640BDR:**

| Qty | Part Number | Description | Supplier | Unit Cost | Total |
|-----|-------------|-------------|----------|-----------|-------|
| 3 | RM-3.33.3S | Recom Isolated DC-DC 3.3V @ 76mA | DigiKey/Mouser | $4.50 | $13.50 |
| 3 | ISO1640BDR | TI I2C Isolator 1.7MHz, 3000 VRMS | DigiKey/Mouser | $3.25 | $9.75 |
| 1 | ENV-EZO-pH | Atlas pH EZO Circuit | Atlas-Scientific | $48.00 | $48.00 |
| 1 | ENV-EZO-EC | Atlas EC EZO Circuit | Atlas-Scientific | $48.00 | $48.00 |
| 1 | ENV-EZO-DO | Atlas DO EZO Circuit | Atlas-Scientific | $58.00 | $58.00 |
| 3 | 5227161-6 | TE BNC Connector (edge mount) | DigiKey/Mouser | $3.00 | $9.00 |
| 3 | 2N7002K,215 | N-FET power switch (optional) | DigiKey/Mouser | $0.10 | $0.30 |
| 12 | Generic | 100nF X7R 50V 0805 Cap (standard) | DigiKey/Mouser | $0.05 | $0.60 |
| 6 | Generic | 10µF X7R 25V 0805 Cap (standard) | DigiKey/Mouser | $0.30 | $1.80 |
| 12 | Generic | 4.7kΩ 0805 I2C pull-ups (both sides) | DigiKey/Mouser | $0.05 | $0.60 |
| 3 | Generic | 10kΩ 0805 resistor (pull-down, optional) | DigiKey/Mouser | $0.01 | $0.03 |
| 1 | Custom PCB | 2-layer PCB (see specs above) | JLCPCB/PCBWay | $20.00 | $20.00 |

**Cost Total (excluding probes):** $209.58

**Option C Summary:**
- **Two-chip solution** - larger footprint than Option B
- **Standard components only** - all common caps/resistors, no specialized ferrite beads
- **Higher I2C speed:** Up to 1.7 MHz (vs 1 MHz for ADM3260)
- **Higher isolation:** 3000 VRMS (vs 2500 VRMS for ADM3260)
- **Enhanced EMC:** ISO1640 has better electromagnetic compatibility
- **Total cost:** $209.58 (about $6 more than Option B)

**Pros:**
✅ Standard components only - no specialized ferrite beads
✅ Higher I2C speed (1.7 MHz vs 1 MHz)
✅ Higher isolation voltage (3000 VRMS vs 2500 VRMS)
✅ Enhanced EMC performance
✅ Hot-swap capable (ISO1640)
✅ Easy to source - all common parts

**Cons:**
⚠️ Two chips instead of one
⚠️ Larger PCB footprint
⚠️ More soldering/assembly
⚠️ Slightly higher cost (+$6)

---

## Decision Guide: Option B vs Option C

| Criteria | Option B (ADM3260) | Option C (RM-3.33.3S + ISO1640BDR) |
|----------|-------------------|-----------------------------------|
| **Chip Count** | 1 chip | 2 chips |
| **PCB Footprint** | Smallest | Medium |
| **BOM Complexity** | Specialized ferrite beads | All standard components |
| **I2C Speed** | 1 MHz | **1.7 MHz** |
| **Isolation** | 2500 VRMS | **3000 VRMS** |
| **EMC Performance** | Good | **Enhanced** |
| **Cost** | **$203.88** | $209.58 (+$6) |
| **Assembly** | **Fewer solder joints** | More solder joints |
| **Sourcing** | Need specialized parts | **All common parts** |

**Choose Option B (ADM3260) if:**
- Smallest PCB footprint is priority
- Single-chip simplicity desired
- Comfortable sourcing specialized ferrite beads
- 1 MHz I2C speed is sufficient

**Choose Option C (RM-3.33.3S + ISO1640BDR) if:**
- Want all standard, easy-to-source components
- Need higher I2C speed (1.7 MHz)
- Need higher isolation voltage (3000 VRMS)
- Building DIY/hobby project with common parts
- Want to avoid specialized ferrite beads

---

**Capacitor Configuration (per TI SLAU845):**
- 6× 10nF caps (GRM21BR71A103KA01L): $0.30 total - VDD domain (VCC1/VCC2)
- 6× 10µF caps (GRM21BR71A106KE15L): $1.80 total - VDD domain (VCC1/VCC2)
- 6× 100nF caps (GRM21BR71H104KA12L): $0.48 total - VIO domain (VIO1/VIO2)
- All caps are MLCC X7R ceramic
- Total capacitor cost: $2.58 for 3 circuits (6 caps each)

**Optional Ferrite Beads (per TI SLAU845):**
- 3× Ferrite beads (BLM18PG101SN1D): $0.30 total
- One per circuit, isolated output (VCC2) only
- Filters DC-DC switching noise before EZO circuits

Notes:
- All six capacitors required per TI SLAU845:
  - VDD domain (VCC1/VCC2): 10nF + 10µF per side for DC-DC converter
  - VIO domain (VIO1/VIO2): 100nF per side for I2C I/O power
- N-FET (2N7002K) and pull-down resistors are optional for power management
- Ferrite beads are optional, ONE per circuit on output side only (per TI SLAU845)

**Probes (purchase separately):**
- pH Probe: Atlas Scientific pH probe with BNC (~$60-120)
- EC Probe: Atlas Scientific EC K1.0 probe with BNC (~$70-150)
- DO Probe: Atlas Scientific Optical DO probe with BNC (~$200-300)
- Calibration Solutions: pH 4/7/10, EC 1413µS (~$20-40)

**Optional/Additional:**
- Header pins for EZO boards (if not included)
- Wire/connectors for power distribution on PCB
- Standoffs and mounting hardware

### Where to Buy Components

**Electronic Components (ISOW7841, BNC, Capacitors):**
```
DigiKey (digikey.com):
- ISOW7741BDFMR: Search "296-ISOW7741BDFMR-ND" (recommended)
- ISOW7841DFMR: Search "296-38846-1-ND" (alternative)
- TE BNC 5227161-6: Search "5227161-6"
- 2N7002K,215: Search "1727-2521-1-ND" (N-FET for power switching)
- BLM18PG101SN1D: Search "490-1037-1-ND" (ferrite bead, optional)
- GRM21BR61A476ME15L: Search "490-10748-1-ND" (47µF cap, optional)
- Murata 100nF/10µF caps: Search part numbers above
- Fast shipping, excellent stock availability
- Recommended for USA/international

Mouser Electronics (mouser.com):
- Same part numbers as DigiKey
- Good for Europe/Asia
- Competitive pricing

LCSC (lcsc.com):
- Lower cost for bulk orders
- Good for China/Asia region
- May have longer lead times
```

**EZO Circuits and Probes:**
```
Atlas Scientific Direct (atlas-scientific.com):
- Official manufacturer
- Full product line
- Technical support available
- Calibration solutions in stock

Amazon:
- Atlas Scientific official store
- Faster shipping (Prime available)
- Slightly higher prices

Adafruit (adafruit.com):
- Carries EZO circuits
- Good tutorials and support
- USA-based

SparkFun (sparkfun.com):
- Alternative source for EZO boards
```

**PCB Fabrication:**
```
JLCPCB (jlcpcb.com): ✅ Recommended for OPNhydro
- 5 PCBs for ~$2-5 + shipping
- PCBA service available (SMT assembly)
- ~7-10 days total (fab + shipping)
- ENIG finish: add ~$15-20

PCBWay (pcbway.com):
- Slightly higher quality
- Good customer service
- ~10-15 days total

OSH Park (oshpark.com):
- Premium quality, made in USA
- ~2-3 weeks lead time
- Higher cost ($5/sq inch)
- Purple soldermask (distinctive look)
```

### Additional Items (not included above)

| Item | Part Number | Description | Cost (USD) |
|------|-------------|-------------|------------|
| pH Probe | Various | Atlas Scientific pH Probe (BNC) | $60-120 |
| EC Probe | Various | Atlas Scientific EC K1.0 Probe (BNC) | $70-150 |
| DO Probe | Various | Atlas Scientific Optical DO Probe (BNC) | $200-300 |
| Calibration Solutions | Various | pH 4.0, 7.0, 10.0 / EC 1413µS | $20-40 |

---

## Testing and Verification

### Power Supply Test

```
1. Measure Input Voltage:
   - Apply 3.3V to VIN
   - Measure at DC-DC input: Should be 3.3V ±5%

2. Measure Isolated Output:
   - Measure at VCC2 (isolated side): Should be 3.3V ±5%
   - Load with 100mA: Voltage should remain >3.2V
   - Check isolation resistance (VIN to VOUT): >10MΩ

3. Ripple and Noise:
   - Use oscilloscope on VCC2
   - AC coupling, 10mV/div
   - Should be <50mV pk-pk
```

### I2C Communication Test

```
1. Bus Voltage Check:
   - SDA idle: Should be 3.3V (pulled high)
   - SCL idle: Should be 3.3V (pulled high)

2. I2C Scan (Arduino or ESP-IDF):
   ```c
   // Scan for EZO devices
   for (uint8_t addr = 0x01; addr < 0x7F; addr++) {
       i2c_cmd_handle_t cmd = i2c_cmd_link_create();
       i2c_master_start(cmd);
       i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
       i2c_master_stop(cmd);
       if (i2c_master_cmd_begin(I2C_NUM_0, cmd, 100) == ESP_OK) {
           printf("Found device at 0x%02X\n", addr);
       }
       i2c_cmd_link_delete(cmd);
   }

   // Expected results:
   // EZO-pH: 0x63
   // EZO-EC: 0x64
   // EZO-RTD: 0x66
   ```

3. Read Device Info:
   ```c
   // Send "i" command to get device info
   uint8_t cmd[] = {'i', '\0'};
   i2c_master_write_to_device(I2C_NUM_0, 0x63, cmd, 2, 1000);

   // Wait 300ms for response
   vTaskDelay(pdMS_TO_TICKS(300));

   // Read response
   uint8_t data[40];
   i2c_master_read_from_device(I2C_NUM_0, 0x63, data, 40, 1000);

   // Expected: "?I,pH,2.1" (or similar version info)
   ```
```

### Isolation Verification

```
1. Ground Isolation Test:
   - Disconnect power
   - Use multimeter in resistance mode
   - Measure between GND and GND_ISO: Should be >10MΩ
   - Measure between VCC and VCC_ISO: Should be >10MΩ

2. Capacitive Coupling Test (advanced):
   - Use LCR meter
   - Measure capacitance GND to GND_ISO: Should be <10pF
   - Lower is better for noise isolation

3. Voltage Isolation Test (use isolation tester):
   - Apply 1000VDC between input and output
   - Should not break down
   - **WARNING: This test requires specialized equipment**
   - **Do NOT perform without proper safety equipment**
```

### Functional Test with Probe

```
1. pH Probe Test:
   - Connect calibrated pH probe to BNC
   - Place in pH 7.0 buffer solution
   - Send "R" command to read
   - Expected: "7.00" ±0.05

2. EC Probe Test:
   - Connect K1.0 EC probe to BNC
   - Place in 1413µS calibration solution
   - Send "R" command
   - Expected: "1413" ±50µS

3. DO Probe Test:
   - Connect optical DO probe to BNC
   - Place in air-saturated water (100% saturation)
   - Send "R" command
   - Expected: "8.2" mg/L (at 25°C, sea level)
```

---

## Common Issues and Troubleshooting

### Issue: No I2C Response

```
Symptoms: I2C scan doesn't find EZO device

Possible Causes:
1. Power not reaching EZO board
   - Check 3.3V_ISO with multimeter
   - Should be 3.25-3.35V under load
   - Solution: Check DC-DC converter, capacitors

2. I2C pullups missing or wrong value
   - Measure SDA/SCL voltage: Should be 3.3V when idle
   - Solution: Check R1-R4 values (should be 4.7kΩ)

3. Wrong I2C address
   - pH should be 0x63, EC 0x64, DO 0x61
   - Solution: Use i2cdetect to scan all addresses

4. I2C isolator not powered
   - Check VCC1 and VCC2 on isolator
   - Both should be 3.3V
   - Solution: Check isolator power connections
```

### Issue: Unstable Readings

```
Symptoms: Readings jump or fluctuate excessively

Possible Causes:
1. Ground loop (insufficient isolation)
   - Check GND and GND_ISO are truly isolated
   - Measure resistance: Should be >10MΩ
   - Solution: Verify PCB isolation barrier

2. Power supply noise
   - Check VCC_ISO ripple with oscilloscope
   - Should be <50mV pk-pk
   - Solution: Add larger decoupling cap (10µF tantalum)

3. EMI from other circuits
   - BNC probe cable picking up noise
   - Solution: Route BNC away from switching supplies

4. Probe not calibrated
   - Old calibration or drift
   - Solution: Recalibrate probe with fresh solutions
```

### Issue: Low Isolation Resistance

```
Symptoms: Continuity between GND and GND_ISO

Possible Causes:
1. PCB contamination
   - Flux residue creating conductive path
   - Solution: Clean PCB with IPA (isopropyl alcohol)

2. Insufficient clearance
   - Traces too close to isolation barrier
   - Solution: Review PCB layout, ensure 5mm spacing

3. Damaged isolator
   - DC-DC or I2C isolator shorted internally
   - Solution: Replace isolator component
```

---

## Calibration Procedures

### pH Probe Calibration (3-point)

```
Required solutions:
- pH 4.0 buffer (red)
- pH 7.0 buffer (yellow)
- pH 10.0 buffer (blue)
- Distilled water for rinsing

Procedure:
1. Rinse probe with distilled water
2. Place in pH 7.0 buffer (midpoint)
3. Send command: "Cal,mid,7.00"
4. Wait for response: "1" (success)

5. Rinse probe
6. Place in pH 4.0 buffer (lowpoint)
7. Send command: "Cal,low,4.00"
8. Wait for response: "1"

9. Rinse probe
10. Place in pH 10.0 buffer (highpoint)
11. Send command: "Cal,high,10.00"
12. Wait for response: "1"

13. Check calibration status:
    Send: "Cal,?"
    Response: "?CAL,3" (3-point calibrated)

Store calibration: Saved automatically in EZO EEPROM
```

### EC Probe Calibration (dry + 1-point)

```
Required:
- Dry air (for dry calibration)
- 1413µS calibration solution
- Distilled water

Procedure:
1. Dry calibration:
   - Remove probe from any solution
   - Shake dry
   - Send command: "Cal,dry"
   - Wait for response: "1"

2. Single-point calibration:
   - Rinse with distilled water
   - Place in 1413µS solution
   - Send command: "Cal,1413"
   - Wait 30 seconds for stabilization
   - Send command: "Cal,high,1413"
   - Response: "1"

3. Check calibration:
   Send: "Cal,?"
   Response: "?CAL,2" (dry + 1-point)

Note: For two-point EC calibration, also calibrate with 12,880µS solution
```

### DO Probe Calibration (1-point atmospheric)

```
Required:
- Air-saturated water (stir for 10 minutes)
- OR water-saturated air (in sealed container)
- Temperature measurement

Procedure:
1. Atmospheric calibration:
   - Place probe in air-saturated water at known temp
   - Let stabilize for 5 minutes
   - Send command: "Cal"
   - Wait for response: "1"

2. Check calibration:
   Send: "Cal,?"
   Response: "?CAL,1"

3. Set atmospheric pressure (if not at sea level):
   Send: "P,[pressure in kPa]"
   Example at Denver (84kPa): "P,84"

Note: DO probes don't need frequent calibration (monthly is typical)
```

---

## Maintenance and Best Practices

### Probe Care

```
pH Probe:
- Store in pH 4.0 storage solution (NOT distilled water!)
- Replace storage solution monthly
- Rinse with distilled water before each use
- Avoid touching the glass bulb
- Lifespan: 6-12 months with regular use

EC Probe:
- Store dry or in calibration solution
- Clean electrodes with soft brush if fouled
- Avoid oils, organics on electrode surface
- Lifespan: 2-3 years

DO Probe:
- Store dry (optical probes don't need wet storage)
- Clean optical window with soft cloth
- Replace cap/membrane yearly
- Lifespan: 5+ years for optical type
```

### Calibration Schedule

```
Recommended frequency:
- pH: Every 1-2 weeks (or when accuracy is critical)
- EC: Monthly
- DO: Monthly or quarterly

After calibration, store date in firmware:
```c
typedef struct {
    char sensor_type[8];    // "pH", "EC", "DO"
    time_t last_cal_date;   // Unix timestamp
    uint8_t cal_points;     // Number of calibration points
    float slope;            // pH slope (should be 58-60mV/pH)
} calibration_data_t;
```
```

### EZO Firmware Updates

```
Atlas Scientific occasionally releases firmware updates.

Check version:
- Send: "I"
- Response: "?I,pH,2.1" (example)

Update procedure:
1. Download .hex file from Atlas Scientific
2. Use Atlas Scientific UART-to-USB converter
3. Connect EZO circuit to PC
4. Use their GUI software to flash firmware
5. Recalibrate after firmware update

Note: Cannot update via I2C, requires UART mode
```

---

## Comparison with Atlas Scientific Pre-Made Isolation Solution

### Atlas Scientific Electrically Isolated EZO Carrier Board

Atlas Scientific offers a pre-made isolation solution for EZO circuits:

```
Product: Electrically Isolated EZO Carrier Board
- Model: Basic Carrier Board with Isolation
- Cost: ~$35-40 USD each
- Interface: I2C AND USB/UART (user selectable)
- Isolation: Galvanically isolated power and data
- Power: 5V input (requires external power or USB)
- Communication: I2C (native) or UART (via USB)
- Assembly: Plug-and-play, no soldering required
- Switching: Software command to switch between I2C/UART modes
```

### Side-by-Side Comparison

| Feature | **Atlas Isolated Carrier** | **Custom ISOW7841** ✅ |
|---------|---------------------------|----------------------|
| **Cost per Circuit** | ~$35-40 | ~$3-7 |
| **Cost for 3 Circuits** | ~$105-120 | ~$21-30 |
| **Assembly Required** | None (plug-and-play) | Custom PCB assembly |
| **Interface** | I2C or UART (switchable) | I2C (native) |
| **Connection to MCU** | 4 wires per board (I2C + power) | Single I2C bus (2 wires) |
| **Physical Size** | 3 separate boards (~3×3 inches each) | Integrated on main PCB |
| **Enclosure Requirements** | Large (3 boards + wiring) | Compact single board |
| **Power Input** | 5V (requires regulator or USB) | 3.3V (from ESP32) |
| **Power Consumption** | Higher (5V→3.3V conversion) | Lower (direct 3.3V) |
| **I2C Bus** | 3 separate I2C connections | Single shared I2C bus |
| **Firmware Complexity** | Same (I2C driver) | Same (I2C driver) |
| **Debugging** | Easy (can switch to USB mode) | I2C tools or logic analyzer |
| **Prototyping Speed** | Immediate | Requires PCB fabrication |
| **Professional Appearance** | 3 separate carrier boards | Professional (integrated) |
| **Maintenance** | 3 separate components | Single integrated system |
| **Flexibility** | Can switch I2C/UART in field | I2C only |

### Cost Analysis (Complete System)

```
Atlas Isolated Carrier Solution (3 sensors):
- 3× Isolated EZO Carrier @ $37 = $111
- Wire/connectors for I2C + power = $5
- 5V power supply (if not using USB) = $5-10
- Total: ~$121-126

Custom ISOW7841 Solution (3 sensors):
- 3× ISOW7841 @ $4 = $12
- 6× 100nF caps @ $0.10 = $0.60
- 3× BNC connector @ $3 = $9
- PCB fabrication (prototype) = $15-20
- Assembly time = $20-40 (if outsourced)
- Total: ~$57-82 (first run)
- Total: ~$22-30 (production, no assembly cost)

Savings with Custom Design:
- First prototype run: $39-69 savings
- Production units: $91-104 savings per unit
```

### System Architecture Comparison

```
Atlas Isolated Carrier Architecture:
┌──────────────────────────────────────┐
│  OPNhydro ESP32-C6 Controller        │
│                                      │
│  ┌──────────┐                        │
│  │  ESP32   │                        │
│  │  GPIO4───┼── SDA (shared) ────────┼─────────┐
│  │  GPIO5───┼── SCL (shared) ────────┼─────┐   │
│  │  3.3V────┼── 3.3V ────────────────┼───┐ │   │
│  │  GND─────┼── GND ─────────────────┼─┐ │ │   │
│  └──────────┘                        │ │ │ │   │
└──────────────────────────────────────┼─┼─┼─┼───┘
                                       │ │ │ │
      ┌────────────────────────────────┼─┼─┼─┼───────────┐
      │                                │ │ │ │           │
      ▼                                ▼ │ │ │           ▼
 ┌──────────────┐              ┌──────────────┐   ┌──────────────┐
 │Atlas Carrier │              │Atlas Carrier │   │Atlas Carrier │
 │   (pH)       │              │   (EC)       │   │   (DO)       │
 │   Isolated   │              │   Isolated   │   │   Isolated   │
 │  ┌────────┐  │              │  ┌────────┐  │   │  ┌────────┐  │
 │  │ EZO-pH │  │              │  │ EZO-EC │  │   │  │ EZO-DO │  │
 │  └───┬────┘  │              │  └───┬────┘  │   │  └───┬────┘  │
 └──────┼───────┘              └──────┼───────┘   └──────┼───────┘
        │                             │                  │
     pH Probe                     EC Probe           DO Probe

Challenges:
- 3 separate carrier boards (~3×3 inches each)
- Each board needs SDA, SCL, GND, 5V connections (12 wires total)
- Requires 5V power (ESP32 only has 3.3V, need level shift or separate 5V rail)
- Large physical footprint in enclosure
- Wire management and termination
- Difficult to achieve professional appearance


Custom ISOW7841 Architecture:
┌──────────────────────────────────────────────────────────┐
│           OPNhydro Main PCB                              │
│                                                          │
│  ┌──────────┐                                            │
│  │  ESP32   │──── I2C Bus (GPIO4/GPIO5) ──┬─┬─┬────────┐ │
│  └──────────┘                             │ │ │        │ │
│                                           │ │ │        │ │
│  ┌──────────────┐  ┌──────────────┐  ┌────┴─┴─┴──────┐ │ │
│  │   ISOW7841   │  │   ISOW7841   │  │   ISOW7841    │ │ │
│  │  (pH iso)    │  │  (EC iso)    │  │  (DO iso)     │ │ │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐   │ │ │
│  │  │ EZO-pH │  │  │  │ EZO-EC │  │  │  │ EZO-DO │   │ │ │
│  │  └───┬────┘  │  │  └───┬────┘  │  │  └───┬────┘   │ │ │
│  └──────┼───────┘  └──────┼───────┘  └──────┼────────┘ │ │
│         │                 │                 │          │ │
└─────────┼─────────────────┼─────────────────┼──────────┘ │
          │                 │                 │            │
       pH Probe         EC Probe          DO Probe         │
                                                           │
All BNC connectors on PCB edge ────────────────────────────┘

Advantages:
- Single I2C bus (2 GPIO pins)
- No cable management
- Compact integrated design
- Simple firmware (single I2C driver)
- Professional appearance
```

### When to Use Each Option

| Use Case | Best Choice | Reason |
|----------|------------|--------|
| **Immediate Testing** | Atlas Isolated Carrier | No PCB design/fabrication wait time |
| **Learning/Experimentation** | Atlas Isolated Carrier | Can switch to USB mode for debugging |
| **Single Sensor Only** | Atlas Isolated Carrier | Small cost difference for one sensor |
| **Temporary/Benchtop Setup** | Atlas Isolated Carrier | Quick setup, no soldering |
| **Cannot Design PCB** | Atlas Isolated Carrier | Plug-and-play solution |
| **Production System (3+ sensors)** | Custom ISOW7841 | $90+ savings, compact design |
| **Space-Constrained Enclosure** | Custom ISOW7841 | Single PCB vs 3 separate boards |
| **Clean Professional Look** | Custom ISOW7841 | Integrated design with edge BNCs |
| **Commercial Product** | Custom ISOW7841 | Lower BOM cost, manufacturability |
| **Multiple Units** | Custom ISOW7841 | Cost savings multiply per unit |
| **3.3V-Only System** | Custom ISOW7841 | No 5V rail needed (Atlas needs 5V) |

### Recommendation for OPNhydro Project

> **✅ DECISION (2026-02-20): OPNhydro will use the custom ISOW7841 design**
>
> The custom ISOW7841 integrated solution has been selected for this project.

**Rationale:** Use custom ISOW7841 design for the following reasons:

1. **Cost Savings:** ~$90-100 savings for 3 sensors
2. **Compact Design:** Single integrated PCB vs 3 separate carrier boards
3. **Simpler Power:** Uses ESP32's 3.3V directly (Atlas needs 5V rail)
4. **Professional Appearance:** Clean single-board design with BNC connectors on edge
5. **Future Expandability:** Easy to add more isolated sensors on same PCB
6. **Fewer Connections:** No external wiring between controller and sensors

**Atlas Carrier Advantages:**
- Immediate availability (no PCB fabrication wait)
- Easy debugging (can switch to USB mode for troubleshooting)
- No assembly/soldering required
- Good for one-off prototypes or testing

**Hybrid Prototyping Approach:**

```
Phase 1: Development (Atlas Carrier - Optional)
- Buy 1× Atlas Isolated Carrier for pH (~$37)
- Develop I2C firmware and test communication
- Test calibration and measurement procedures
- Validate sensor readings and algorithms
- NOTE: Can skip this phase and go directly to custom PCB

Phase 2: Custom PCB Design & Fabrication
- Design PCB with ISOW7841 isolation for all 3 sensors
- Submit PCB files to fab house (JLCPCB, PCBWay, etc.)
- Wait 1-2 weeks for fabrication
- Assemble components (or use PCBA service)

Phase 3: Testing & Integration
- Test custom PCB with EZO circuits
- Same I2C firmware works (no porting needed!)
- Calibrate all three probes (pH, EC, DO)
- Integrate into enclosure

Phase 4: Production
- Use custom ISOW7841 design
- Save ~$90 per unit
- Benefit from integrated, compact design
- Professional single-board appearance

Recommendation: Skip Phase 1 and go directly to custom PCB design
since both solutions use identical I2C firmware. The Atlas carrier
is mainly useful if you need immediate testing without waiting for
PCB fabrication.
```

### Firmware Comparison

```c
// Both solutions use I2C, so firmware is identical:

void read_ezo_i2c(void) {
    // Trigger all readings on shared I2C bus
    // Works with both Atlas carriers and custom ISOW7841
    ezo_send_command(0x63, "R");  // pH
    vTaskDelay(pdMS_TO_TICKS(5));

    ezo_send_command(0x64, "R");  // EC
    vTaskDelay(pdMS_TO_TICKS(5));

    ezo_send_command(0x61, "R");  // DO
    vTaskDelay(pdMS_TO_TICKS(600));

    // Read results from shared bus
    float ph = ezo_read_float(0x63);
    float ec = ezo_read_float(0x64);
    vTaskDelay(pdMS_TO_TICKS(600));
    float dissolved_oxygen = ezo_read_float(0x61);
}

// Key Difference: Hardware Integration
//
// Atlas Carrier Boards:
// - Requires physical wiring: 12 connections (SDA, SCL, 5V, GND × 3 boards)
// - Need to provide 5V power (ESP32 is 3.3V, so requires separate 5V rail)
// - 3 separate boards to mount and secure in enclosure
// - Professional appearance requires custom enclosure design
//
// Custom ISOW7841:
// - Everything integrated on single PCB
// - Powered directly from ESP32 3.3V rail
// - No external wiring needed
// - Clean, professional single-board design
```

---

## Advanced Topics

### Multiple Probes in Same Solution

```
When measuring pH, EC, and DO in the same reservoir:

Physical Placement:
          ┌─────────────────────────────┐
          │     Hydroponic Reservoir    │
          │                             │
          │   ┌─── DO Probe             │
          │   │    (optical, no current)│
          │   │                         │
          │   │        ┌─── pH Probe    │
          │   │        │   (high impedance)
          │   │        │                │
          │   ▼        ▼                │
          │   ●        ●                │
          │                      ●      │
          │                      │      │
          │                      └─── EC Probe
          │                    (generates field)
          └─────────────────────────────┘

Spacing Guidelines:
- pH and EC: Minimum 10cm apart
- DO and pH: Minimum 5cm apart
- DO and EC: Minimum 10cm apart
- Keep all probes away from pump outlets (turbulence)
- Avoid direct sunlight on optical DO probe
```

### Reading Multiple EZO Sensors Efficiently

```
I2C bus can only handle one transaction at a time.
Stagger readings to avoid bus congestion:

Optimal Reading Sequence:
1. Send "R" to pH (0x63)
2. Wait 5ms (bus clear time)
3. Send "R" to EC (0x64)
4. Wait 5ms
5. Send "R" to DO (0x61)
6. Wait 600ms (EZO response time for pH/EC)
7. Read pH result
8. Read EC result
9. Wait 600ms (total of 1200ms for DO)
10. Read DO result

Sample Code:
```c
void read_all_ezo_sensors(void) {
    // Trigger all readings
    ezo_send_command(I2C_EZO_PH, "R");
    vTaskDelay(pdMS_TO_TICKS(5));

    ezo_send_command(I2C_EZO_EC, "R");
    vTaskDelay(pdMS_TO_TICKS(5));

    ezo_send_command(I2C_EZO_DO, "R");

    // Wait for pH and EC (600ms)
    vTaskDelay(pdMS_TO_TICKS(600));

    float ph = ezo_read_float(I2C_EZO_PH);
    float ec = ezo_read_float(I2C_EZO_EC);

    // Wait additional 600ms for DO (total 1200ms)
    vTaskDelay(pdMS_TO_TICKS(600));

    float dissolved_oxygen = ezo_read_float(I2C_EZO_DO);

    // Process readings
    update_sensor_data(ph, ec, dissolved_oxygen);
}
```
```

### Temperature Compensation

```
All EZO circuits support automatic temperature compensation.

Connect DS18B20 reading to EZO circuits:
1. Read temperature from DS18B20 (GPIO2)
2. Send temp to each EZO circuit:
   Command: "T,[temp in °C]"
   Example: "T,25.3"

Code example:
```c
void update_ezo_temperature(float temp_celsius) {
    char cmd[16];
    snprintf(cmd, sizeof(cmd), "T,%.1f", temp_celsius);

    // Send to all EZO circuits
    ezo_send_command(I2C_EZO_PH, cmd);
    ezo_send_command(I2C_EZO_EC, cmd);
    ezo_send_command(I2C_EZO_DO, cmd);
}

// Call this whenever temperature changes (>0.5°C change)
```

Frequency:
- Update on every reading cycle
- Or only when temp changes >0.1°C
- Affects accuracy: pH ±0.003/°C, EC ±2%/°C
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Initial | Created isolated EZO circuit design document |

---

## References and Resources

### Datasheets
- [B0303S-1WR2 Isolated DC-DC Converter](https://www.mornsun-power.com/pdf/B_S-1WR2.pdf)
- [ISO1540 I2C Digital Isolator](https://www.ti.com/lit/ds/symlink/iso1540.pdf)
- [ISOW7841 Isolated I2C with Power](https://www.ti.com/lit/ds/symlink/isow7841.pdf)
- [Atlas Scientific EZO pH Circuit](https://files.atlas-scientific.com/pH_EZO_Datasheet.pdf)
- [Atlas Scientific EZO EC Circuit](https://files.atlas-scientific.com/EC_EZO_Datasheet.pdf)
- [Atlas Scientific EZO DO Circuit](https://files.atlas-scientific.com/DO_EZO_Datasheet.pdf)

### Atlas Scientific Resources
- [EZO Class Circuits - I2C Mode](https://files.atlas-scientific.com/pi_sample_code.pdf)
- [EZO Probe Selection Guide](https://atlas-scientific.com/probes/)
- [Calibration Solutions](https://atlas-scientific.com/calibration-solutions/)

### Design Guidelines
- [PCB Isolation Best Practices](https://www.ti.com/lit/an/slla284a/slla284a.pdf)
- [I2C Bus Specification](https://www.nxp.com/docs/en/user-guide/UM10204.pdf)
- [EMI/EMC Design for Isolated Systems](https://www.ti.com/lit/an/slla290a/slla290a.pdf)

---

**End of Document**
