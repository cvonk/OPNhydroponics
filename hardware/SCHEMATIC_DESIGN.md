# Schematic Design Guide

This document describes the circuit design for the OPNhydroponics controller PCB.

## Block Diagram

```
                                    ┌────────────────────────────────────────┐
                                    │              CONNECTORS                │
                                    │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │
                                    │  │ BNC │ │ BNC │ │     │ │Float│       │
                                    │  │ pH  │ │ EC  │ │ RTD │ │ SW  │       │
                                    │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘       │
                                    └─────┼──────┼──────┼──────┼─────────────┘
                                          │      │      │      │
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  PCB                                         │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────┐  │
│  │   POWER     │    │                    SENSORS                          │  │
│  │             │    │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │  │
│  │ 12V ──►5V   │    │  │ EZO-pH │  │ EZO-EC │  │ EZO-RTD│  │ BME280 │     │  │
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

**Additional Output Capacitance for Motor Loads:**

⚠️ **CRITICAL**: Add bulk capacitance beyond standard buck converter output caps

```
Recommended Additional Capacitors on 5V Rail:

5V ──┬──[2×22µF]──┬──[1000µF]──┬──[100nF]──► To ESP32 + Loads
     │  (standard │   (bulk    │  (HF
     │   Cout)    │   added)   │   filter)
    ─┴─          ─┴─          ─┴─
    GND          GND          GND

Components:
- C_bulk: 1000µF / 10V low-ESR electrolytic (Panasonic FR series)
  * Purpose: Buffer ESP32 WiFi TX bursts (500mA for 100-200ms)
  * Prevents brownout resets during WiFi transmission  * Place within 2cm of ESP32 VIN pin

- C_hf: 100nF / 16V ceramic (X7R)
  * Purpose: High-frequency noise filtering
  * Place within 5mm of ESP32 VIN pin

Why 1000µF?
- ESP32 WiFi TX peak: 500mA for 100-200ms
- Voltage sag: ΔV = I × Δt / C
- Target: <100mV sag → C = 0.5A × 0.2s / 0.1V = 1000µF ✅
```
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

### 1.5 12V Rail Bulk Capacitance (Motor Loads)

⚠️ **CRITICAL**: Brushless motor (AUBIG DC40-1250) requires substantial bulk capacitance for startup inrush

```
12V Power Supply Filtering:

12V_PSU ──┬──[2200µF]──┬──[100nF]──┬──► To MOSFET drivers
          │  (bulk)    │  (HF)     │
         ─┴─          ─┴─          ─┴─
         GND          GND          GND

Components:
- C_bulk: 2200µF / 25V low-ESR electrolytic (Panasonic FR series or equivalent)
  * Purpose: Buffer motor startup inrush current (AUBIG DC40-1250: ~2A for 50-100ms)
  * Prevents voltage sag that could reset ESP32 or cause pump stall
  * Place at 12V input near main pump MOSFET Q1

- C_hf: 100nF / 50V ceramic (X7R)
  * Purpose: High-frequency noise filtering from motor commutation
  * Place near 12V input connector

Why 2200µF?
- AUBIG brushless motor startup inrush: ~2A for 50-100ms (1.67× nominal 1.2A)
- Buck converter output caps: typically 47-220µF (insufficient for motor loads)
- Voltage sag calculation: ΔV = I × Δt / C
- Target: <200mV sag → C = 2A × 0.1s / 0.2V = 1000µF minimum
- Use 2200µF for safety margin and multiple pump operation

Additional Local Bypass Capacitors:
- Place 100nF ceramic (0805, X7R, 50V) near each MOSFET (Q1-Q6)
- Connects between 12V drain and GND
- Provides local energy storage for switching transients
- Reduces high-frequency noise on 12V rail

12V Distribution Layout:
┌──────────────────────────────────────────────────────────┐
│ 12V PSU                                                  │
│   │                                                      │
│   ├─[2200µF]─[100nF]─┬─[100nF]─┬─► Q1 (Main Pump)      │
│                       │         │                        │
│                       ├─[100nF]─┼─► Q2 (pH Up)          │
│                       │         │                        │
│                       ├─[100nF]─┼─► Q3 (pH Down)        │
│                       │         │                        │
│                       ├─[100nF]─┼─► Q4 (Nutrient A)     │
│                       │         │                        │
│                       ├─[100nF]─┼─► Q5 (Nutrient B)     │
│                       │         │                        │
│                       └─[100nF]─┴─► Q6 (ATO Valve)      │
│                                                          │
└──────────────────────────────────────────────────────────┘

IMPORTANT Power Supply Selection:
- Use PSU with built-in soft-start (Mean Well LRS-50-12 ✅)
- Generic PSUs may trip overcurrent during capacitor charging + motor startup
- Without soft-start: inrush can exceed 10A briefly (2.2mF × dV/dt)
```

### 1.6 PCB Layout Guidelines for Power Integrity

**Critical Layout Rules:**

1. **Star Ground Configuration:**
   ```
   ESP32 GND ──┐
   Sensors GND ─┼──► Single ground point at 12V PSU GND terminal
   Pumps GND ───┘

   - Prevents ground loops and noise coupling
   - Use solid ground plane on bottom layer (recommended)
   - If using ground traces, make pump ground traces thick (50 mil)
   ```

2. **Capacitor Placement:**
   ```
   Priority Order (closest to load first):
   1. 100nF ceramics: <5mm from IC pins
   2. 10-22µF ceramics: <1cm from IC
   3. 1000-2200µF electrolytics: <2cm from load

   Orientation: Place capacitors perpendicular to current flow for lowest ESL
   ```

3. **Trace Width Requirements:**
   ```
   5V Rail (500mA max):
   - Minimum: 20 mil (0.5mm)
   - Recommended: 30 mil (0.76mm)
   - Length: Keep <10cm from buck to ESP32

   12V Rail (3A peak):
   - Minimum: 40 mil (1.0mm)
   - Recommended: 50 mil (1.27mm)  - Main pump branch: 60 mil (1.5mm)
   - Dosing pump branches: 30 mil (0.76mm)

   For 1oz copper @ 25°C ambient:
   - 50 mil @ 3A = 10°C rise, 27mV drop per inch
   ```

4. **Ground Plane Strategy:**
   ```
   RECOMMENDED (for 2-layer board):
   - Top layer: Signal routing + power distribution
   - Bottom layer: Solid ground plane (remove only for vias/pads)

   ALTERNATIVE (for 4-layer board):
   - Layer 1 (Top): Signal + high-speed
   - Layer 2: Ground plane
   - Layer 3: Power planes (3.3V, 5V, 12V pours)
   - Layer 4 (Bottom): Ground plane
   ```

5. **Keep-Out Zones:**
   ```
   - ESP32 antenna area: No ground pour, no traces, no vias
   - I2C traces: Route away from 12V pump power traces (>10mm separation)
   - Sensor analog signals: Shield with ground guard traces if near pump power
   ```

### 1.7 Noise Mitigation (Optional - Only if Issues Observed)

**If you experience noise issues (ESP32 resets, erratic sensor readings, WiFi dropouts):**

```
Symptom-Based Solutions:

1. ESP32 resets during pump operation:
   ✅ Solution: Increase 5V bulk cap (1000µF → 2200µF)
   ✅ Solution: Add ferrite bead on 5V input to ESP32 (BLM18PG471SN1D)

2. Erratic I2C sensor readings when pumps run:
   ✅ Solution: Add ferrite beads on 12V pump power lines (BLM15HD182SN1)
   ✅ Solution: Use twisted-pair or shielded cable for pump connections
   ✅ Solution: Add RC snubber across pump terminals (10Ω + 100nF)

3. WiFi disconnects during dosing:
   ✅ Solution: Increase 5V bulk cap (1000µF → 2200µF)
   ✅ Solution: Enable ESP32 power save mode between WiFi transmissions

4. Brushed motors only - excessive noise:
   ✅ Solution: Add 100nF ceramic across motor terminals (suppresses brush arcing)
   ✅ Solution: Add common-mode choke on motor power wires

LAST RESORT - Optocoupler Isolation:
- Only if above solutions fail
- PC817 optocoupler between ESP32 GPIO and MOSFET gate
- Limitations: Adds complexity, 4µs propagation delay, affects PWM accuracy
- Cost: ~$0.40 per channel × 6 = $2.40 + 12 resistors
- NOT RECOMMENDED for this design (pumps share common ground with ESP32)
```

**Summary - Recommended Capacitor BOM:**

| Location | Capacitor | Qty | Part Example | Purpose |
|----------|-----------|-----|--------------|---------|
| 5V buck output | 1000µF 10V electrolytic | 1 | Panasonic EEU-FR1A102 | ESP32 WiFi buffering |
| 5V buck output | 100nF 16V ceramic | 1 | Generic X7R 0805 | HF filtering |
| 12V PSU input | 2200µF 25V electrolytic | 1 | Panasonic EEU-FR1E222 | Motor startup buffering |
| 12V PSU input | 100nF 50V ceramic | 1 | Generic X7R 0805 | HF filtering |
| Per MOSFET Q1-Q6 | 100nF 50V ceramic | 6 | Generic X7R 0805 | Local bypassing |
| **Total** | | **10** | | **~$3-4 total** |

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

### 3.2 Atlas Scientific Circuits — EZO vs OEM

Atlas Scientific offers two product lines for the same measurement circuits:

| | **EZO** (carrier board) | **OEM** (bare die) |
|---|---|---|
| Form factor | Breakout board with pin headers | Direct PCB solder-on |
| Dimensions | 13.97 × 20.16mm | 12 × 11mm |
| Interface | UART (default) + I2C (manual switch required) | I2C / SMBus only — no mode switching |
| Voltage | 3.3V–5V | 3.0V–5.5V |
| Isolation needed | Yes (B0303S-1WR2 per circuit) | Yes (same requirement) |
| Field-replaceable | Yes (unplugs from header) | No (soldered to PCB) |
| Best for | Prototyping / v1 | Production / volume |

**Decision: EZO carrier boards chosen for v1.** They are field-swappable when a circuit fails and require no custom PCB footprint. Switch to OEM for v2/production once the design is validated.

**EZO Circuits:**

| Circuit | Mfr Part | DigiKey | Price (DigiKey) | I2C Addr | Accuracy | Range |
|---------|----------|---------|-----------------|----------|----------|-------|
| **EZO-pH** | EZO-PH | [16003108](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-PH/16003108) | $51.27 | 0x63 | ±0.002 pH | 0.001–14.000 |
| **EZO-EC** | EZO-EC | [16003000](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-EC/16003000) | $82.25 | 0x64 | ±2% | 0.07–500,000+ µS/cm |
| **EZO-RTD** | EZO-RTD | [16003139](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-RTD/16003139) | $38.75 | 0x66 | ±(0.1 + 0.0017×°C) | -126–1254 °C |

All EZO circuits: 3.3V–5V, I2C or UART, 13.97 × 20.16mm

**OEM Circuits (for future reference):**

| Circuit | I2C Addr | Accuracy | Range |
|---------|----------|----------|-------|
| **pH-OEM** | 0x65 | ±0.002 pH | 0.001–14.000 |
| **EC-OEM** | 0x64 | ±2% | 0.07–500,000+ µS/cm |
| **RTD-OEM** | 0x68 | ±(0.1 + 0.0017×°C) | -126–1254 °C |

All OEM circuits: 3.0V–5.5V, I2C (SMBus) only, 12 × 11mm

> **I2C address differences:** pH OEM uses 0x65 (not 0x63) and RTD OEM uses 0x68 (not 0x66). Firmware must be updated if switching from EZO to OEM circuits.

**Recommended Probes:**

| Probe | Model | Price | Notes |
|-------|-------|-------|-------|
| **pH** | Gen 3 Lab Grade (ENV-40-pH) | $84.99 | Double-junction Ag/AgCl — double-junction required for nutrient solution (resists junction clogging) |
| **EC** | Conductivity K 1.0 (ENV-40-EC-K1.0) | $139.99 | K=1.0 covers hydroponics range 500–5000 µS/cm; no electrolyte depletion, calibrate at install only |
| **Temp** | PT-1000 RTD Probe (ENV-40-TMP) | — | Compatible with EZO-RTD; 1-point calibration |

**Kits (circuit + probe + calibration solutions + isolated carrier board):**

| Kit | Price |
|-----|-------|
| pH Kit | $159.99 |
| EC K 1.0 Kit | $229.99 |

> **EC probe K value:** K=1.0 is correct for hydroponics. The EZO-EC supports K=0.01–10.2 but the probe K value must suit your conductivity range. Do not substitute K=0.1 (ultra-pure water) or K=10 (seawater).

> **pH probe storage:** Gen 3 double-junction probe must be stored wet in storage solution (not plain water). Mount BNC connectors so probes are easily removed when the system is idle.

> **Isolation:** EZO-pH and EZO-EC must each be powered from an isolated 3.3V supply (B0303S-1WR2 DC-DC) to prevent cross-contamination when probes share the same solution. EZO-RTD does **not** require isolation — connect directly to the 3.3V rail.

### 3.2a Atlas Scientific Wi-Fi Hydroponics Kit — Considered, Not Selected

The [Wi-Fi Hydroponics Kit](https://atlas-scientific.com/kits/wi-fi-hydroponics-kit/) and its [Bare-Bones variant](https://atlas-scientific.com/kits/bb-wi-fi-hkit/) were evaluated as an alternative to the custom sensor integration.

**Full Kit ($569.99):** Enclosure + Adafruit HUZZAH32 + carrier board + EZO-pH + EZO-EC + EZO-RTD + probes + calibration solutions. Uploads to ThingSpeak over Wi-Fi.

**Bare-Bones Kit ($169.99):** Enclosure + Adafruit HUZZAH32 + carrier board (3 isolated EZO slots, I2C only). EZO circuits and probes supplied separately.

**Why not selected:**

| Requirement | Wi-Fi Kit | OPNhydro |
|-------------|-----------|----------|
| Dosing pump control (5 pumps) | No | Yes |
| ATO valve control | No | Yes |
| DO sensor support | No | Yes |
| Ultrasonic / float level sensing | No | Yes |
| ESP32-C6 (Thread/Zigbee capable) | No (HUZZAH32) | Yes |
| 12V power management | No | Yes |
| Open hardware | No | Yes |
| Custom firmware | Limited (ThingSpeak) | Full control |

The kit is a self-contained monitoring appliance, not a controller platform. It covers only pH, EC, and temperature — no DO, no actuation, and no 12V rail. The OPNhydro custom PCB is required to meet all system requirements.

**Total cost (circuits + probes):** ~$653 all three | ~$590 via kits | ~$394 pH + EC only (no DO)

---

### 3.3 EZO Circuit Connections

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

### 3.4 Switching EZO Circuits to I2C Mode (Manual, No UART Required)

EZO circuits ship in **UART mode** (green LED). They must be switched to **I2C mode** (blue LED)
before connecting to OPNhydro. This is done by briefly shorting two pins at power-on — no USB
adapter, no serial terminal, no programming required.

**LED color key:**
```
Green = UART mode
Blue  = I2C mode
```

**Pins to short (by circuit type):**

| EZO Circuit | Short these two pins | Default I2C address after switch |
|-------------|----------------------|----------------------------------|
| EZO-pH      | TX → PGND            | 0x63 (99)                        |
| EZO-EC      | TX → PGND            | 0x64 (100)                       |
| EZO-DO      | TX → PGND            | 0x61 (97)                        |

**Step-by-step procedure (from Atlas Scientific EZO pH datasheet, p.37):**

```
1. Disconnect GND (power off the EZO circuit)

2. Disconnect TX and RX from any microcontroller

3. Connect TX to PGND using a jumper wire
   (short these two pins directly on the EZO carrier board)

4. Confirm RX is disconnected — leaving RX connected will prevent switching

5. Connect GND (power on)

6. Wait for LED to change from Green → Blue
   (takes ~2 seconds; indicates I2C mode is now active)

7. Disconnect GND (power off)

8. Remove the TX-to-PGND jumper wire

9. Reconnect SDA, SCL, VCC, GND for normal I2C operation
```

> **Important:** RX must be floating (disconnected) during the switch.
> If RX is connected or pulled to any voltage, the mode switch will not occur.

> **Address reset:** The manual switch always resets the I2C address to the
> circuit's factory default (see table above). If you need a non-default address,
> set it via I2C command (`I2C,<addr>`) after switching.

**Wiring diagram for the switch:**

```
          EZO Circuit (during switching only)

    VCC ─────── [leave disconnected until step 5]
    GND ─────── [connect at step 5, disconnect at step 7]
    TX  ─┐
         │ jumper wire (short for steps 3–8)
    PGND─┘
    RX  ─────── [must be disconnected / floating]
    SDA ─────── [leave disconnected until step 9]
    SCL ─────── [leave disconnected until step 9]
```

**Reversing back to UART:** Same procedure — short TX to PGND again; LED changes Blue → Green.

---

### 3.5 I2C Connector

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
- Ultrasonic (HC-SR04+ / RCWL-1601): JST-XH 4-pin (2.5mm pitch) - smaller pitch!
- I2C sensors: Phoenix Contact 4-pin (3.5mm pitch) ✅

---

### 3.6 EZO Circuit Calibration

All calibration is performed over I2C by sending ASCII command strings to each circuit's address.
After sending a command, wait **300 ms** before reading the response.

Query current calibration status at any time with `Cal,?` → returns `?Cal,<n>` where `n` = number
of calibration points stored (0 = uncalibrated).

---

#### EZO-pH — 3-Point Calibration (address 0x63)

**Calibration solutions needed:** pH 4.00, 7.00, 10.00 buffers
**Order is mandatory:** mid → low → high. Starting over with `Cal,mid` clears all stored points.

```
Step 1 — Mid-point (pH 7.00)
  Place probe in pH 7.00 buffer.
  Wait for readings to stabilize (~1–2 min).
  Send:  Cal,mid,7
  Wait:  300 ms
  Read:  response (should be "*OK")

Step 2 — Low-point (pH 4.00)
  Rinse probe with DI water, dry gently.
  Place probe in pH 4.00 buffer.
  Wait for readings to stabilize (~1–2 min).
  Send:  Cal,low,4
  Wait:  300 ms
  Read:  response

Step 3 — High-point (pH 10.00)
  Rinse probe with DI water, dry gently.
  Place probe in pH 10.00 buffer.
  Wait for readings to stabilize (~1–2 min).
  Send:  Cal,high,10
  Wait:  300 ms
  Read:  response

Verify: Send Cal,?  →  expect ?Cal,3
```

| Command | Description |
|---------|-------------|
| `Cal,mid,7` | Midpoint calibration at pH 7 (must do first) |
| `Cal,low,4` | Low-point calibration at pH 4 |
| `Cal,high,10` | High-point calibration at pH 10 |
| `Cal,?` | Query — returns `?Cal,0/1/2/3` |
| `Cal,clear` | Erase all calibration data |

> **Recalibrate:** Every 6–12 months, or when probe response drifts >0.1 pH.
> **Storage:** Keep Gen 3 probe tip submerged in storage solution when not in use.

---

#### EZO-EC — 2-Point Calibration (address 0x64, K=1.0 probe)

**Calibration solutions needed:** 12,880 µS/cm and 80,000 µS/cm standards
(Atlas Scientific COND-12880 and COND-80000, or equivalent NIST-traceable solutions)

```
Step 1 — Dry calibration
  Remove probe from any liquid. Ensure probe is completely dry.
  Send:  Cal,dry
  Wait:  300 ms
  Read:  response (*OK)

Step 2 — Low-point (12,880 µS/cm)
  Place probe in 12,880 µS/cm standard.
  Wait for readings to stabilize (~1 min).
  Send:  Cal,low,12880
  Wait:  300 ms
  Read:  response

Step 3 — High-point (80,000 µS/cm)
  Rinse probe with DI water, dry gently.
  Place probe in 80,000 µS/cm standard.
  Wait for readings to stabilize (~1 min).
  Send:  Cal,high,80000
  Wait:  300 ms
  Read:  response

Verify: Send Cal,?  →  expect ?Cal,2
```

| Command | Description |
|---------|-------------|
| `Cal,dry` | Dry calibration (always first) |
| `Cal,low,12880` | Low-point at 12,880 µS/cm (K=1.0) |
| `Cal,high,80000` | High-point at 80,000 µS/cm (K=1.0) |
| `Cal,one,<value>` | Single-point calibration (alternative to 2-point) |
| `Cal,?` | Query — returns `?Cal,0/1/2` |
| `Cal,clear` | Erase all calibration data |

> **Recalibrate:** Annually or when probe is replaced.
> **K value:** Confirm probe is K=1.0 (`K,?` should return `?K,1.00`). If not, set with `K,1.0`.

---

#### EZO-DO — 1-Point Atmospheric Calibration (address 0x61)

**No calibration solution required** for standard atmospheric calibration.
Optional zero-point uses sodium sulfite solution (Na₂SO₃) to create 0 mg/L DO water.

```
Step 1 — Atmospheric (single-point, sufficient for hydroponics)
  Remove probe from water.
  Expose probe to open air for 30–60 seconds (readings must stabilize).
  Send:  Cal
  Wait:  300 ms
  Read:  response (*OK)

Verify: Send Cal,?  →  expect ?Cal,1

Optional Step 2 — Zero-point (improves accuracy, rarely needed)
  Prepare sodium sulfite solution (Na₂SO₃ in DI water).
  Submerge probe until DO reading reaches 0.00 mg/L.
  Send:  Cal,0
  Wait:  300 ms
  Read:  response

Verify: Send Cal,?  →  expect ?Cal,2
```

| Command | Description |
|---------|-------------|
| `Cal` | Atmospheric single-point calibration |
| `Cal,0` | Zero-point calibration (0 mg/L, optional) |
| `Cal,?` | Query — returns `?Cal,0/1/2` |
| `Cal,clear` | Erase all calibration data |

> **Recalibrate:** Every 8–12 months, or after membrane replacement.
> **Temperature compensation:** Send `T,<temp>` before calibrating if water temp ≠ 25°C.

---

#### General I2C Calibration Notes

```
I2C transaction for any calibration command:

1. Write command string to EZO address (e.g., 0x63)
   e.g.,  i2c_write(0x63, "Cal,mid,7")

2. Wait 300 ms minimum before reading response

3. Read 1+ bytes from EZO address
   Response byte 1 = status code:
     1 = success (*OK)
     2 = syntax error
     254 = still processing (wait longer)
     255 = no data

4. If status = 254, wait another 100 ms and retry read
```

**Calibration frequency summary:**

| Circuit | Method | Solutions | Frequency |
|---------|--------|-----------|-----------|
| EZO-pH  | 3-point | pH 4, 7, 10 buffers | Every 6–12 months |
| EZO-EC  | 2-point + dry | 12,880 + 80,000 µS/cm | Annually |
| EZO-DO  | 1-point atmospheric | None (air) | Every 8–12 months |

---

## 4. Temperature Sensor (1-Wire)

### 4.1 Basic Circuit

```
1-Wire Bus Connection:

    3.3V ───┬────────────────────────────► VDD to DS18B20 (Pin 3, Red)
            │
           [R1] 4.7kΩ pullup resistor
            │
            └──┬─────────────────────────► DQ to DS18B20 (Pin 2, White)
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
            ├─────┬────────────────► Pin 2: DQ (White wire)  [SEN-11050]
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
│ Pin 2: DQ (White)   │ ◄── To GPIO2 via 4.7kΩ pullup to 3.3V  [SEN-11050 uses White]
│ Pin 3: VDD (Red)    │ ◄── To 3.3V rail
└─────────────────────┘

Connector: JST-XH 3-pin S3B-XH-A (Right-angle, through-hole PCB mount)
Housing: JST XHP-3 (3-pin for cable assembly)
Contacts: JST SXH-001T-P0.6 (crimp terminals, 30-26 AWG)

Probe: SparkFun SEN-11050 bare wire ends → crimp SXH-001T-P0.6 contacts onto wires
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

**Selected part: SparkFun SEN-11050** (Waterproof DS18B20, ~$10)

```
SparkFun SEN-11050 specifications:
- Part number: SEN-11050
- Sensor IC: Maxim DS18B20
- Cable: ~1.8m (6 ft), PVC jacketed, bare wire ends (no connector)
- Wire colors: Red (VDD), White (DQ/SIG), Black (GND)
- Probe tip: Stainless steel, 6mm diameter
- Temperature range: -55°C to +125°C
- Accuracy: ±0.5°C (-10°C to +85°C)
- Operating voltage: 3.0V to 5.5V (use 3.3V rail)
- Interface: 1-Wire
- Waterproof: Yes (sealed epoxy probe tip)
```

**PCB connector wiring for SEN-11050:**
```
JST-XH 3-pin on PCB        SEN-11050 wire
─────────────────────────────────────────
Pin 1: GND (to GND rail) ◄── Black wire
Pin 2: DQ  (to GPIO2)    ◄── White wire  ← NOTE: White, not Yellow
Pin 3: VDD (to 3.3V)     ◄── Red wire
```

> **Note:** The bare wire ends of the SEN-11050 require termination.
> Crimp JST-XH contacts (SXH-001T-P0.6) onto each wire to plug directly
> into the PCB's JST-XH 3-pin header, or use a screw terminal adapter.

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

## 5. Ultrasonic Sensor (HC-SR04+ / RCWL-1601)

**Recommended part: RCWL-1601** — native 3.3V operation eliminates the level-shifting voltage divider required by the original 5V HC-SR04. Preferred over HC-SR04+ for better accuracy (1mm resolution vs ±3mm), lower current draw (2.2mA vs 15mA), specified operating temperature (-10°C to 90°C), and consistent quality from a known manufacturer (Cytron). HC-SR04+ is an acceptable alternative if sourcing is constrained — PCB footprint and firmware are identical.

### 5.1 Basic Circuit

```
HC-SR04+ / RCWL-1601 Ultrasonic Distance Sensor Connection:

    3.3V rail ──────────────────────────► VCC
                                           │
                                      ┌────┴────┐
    GND rail ───────────────────────► │ Sensor  │
                                      │         │
    GPIO9 ──────────────────────────► │ TRIG    │ (3.3V logic)
    (US_TRIG)                         │         │
    GPIO3 ◄─────────────────────────  │ ECHO    │ (3.3V logic output)
    (US_ECHO)                         └─────────┘


Signal Flow:
1. ESP32 GPIO9 sends 10µs pulse to TRIG (3.3V HIGH)
2. Sensor emits 8-cycle 40kHz ultrasonic burst
3. ECHO pin goes HIGH (3.3V) while waiting for reflection
4. ESP32 GPIO3 measures ECHO pulse width directly — no voltage divider needed
5. Distance calculated from pulse width
```

### 5.2 Component Selection

| Component | Value/Type | Purpose | Package |
|-----------|------------|---------|---------|
| **RCWL-1601** ✅ recommended | Ultrasonic sensor, 3.0V–5.5V | Distance measurement 2-450cm, 1mm res, 2.2mA | 4-pin module |
| ~~HC-SR04+~~ (alternative) | Ultrasonic sensor, 3.0V–5.5V | Distance measurement 2-400cm, ±3mm, 15mA | 4-pin module |
| **C1** (optional) | 100nF ceramic | VCC decoupling near connector | 0805 SMD |

> **Note:** No voltage divider resistors required. ECHO output is at 3.3V when sensor is powered from 3.3V rail — direct ESP32 GPIO connection is safe.

### 5.3 How the Sensor Works

**Ultrasonic Ranging Principle:**

```
Step 1: Trigger Pulse
   ESP32 sends 10µs HIGH pulse to TRIG pin
              ┌────┐
   TRIG  ─────┘    └─────
              10µs

Step 2: Ultrasonic Burst
   Sensor emits 8 cycles of 40kHz ultrasonic sound

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

**Why choose a native 3.3V part?**
- HC-SR04+ / RCWL-1601 operate from 3V–5.5V; ECHO output tracks VCC
- Powered at 3.3V → ECHO swings 0–3.3V → direct ESP32 GPIO connection
- Eliminates R1/R2 voltage divider, reducing BOM and PCB area
- Cleaner signal path with no resistive loading on ECHO

### 5.4 PCB Connector

**4-pin JST-XH connector (2.5mm pitch):**
```
┌──────────────────────┐
│ Pin 1: VCC (3.3V)    │ ◄── To 3.3V rail
│ Pin 2: TRIG          │ ◄── To GPIO9 (US_TRIG)
│ Pin 3: ECHO          │ ◄── Direct to GPIO3 (US_ECHO)
│ Pin 4: GND           │ ◄── To system GND
└──────────────────────┘

Connector: JST-XH 4-pin B4B-XH-A (Right-angle, PCB mount)
Housing: JST XHP-4 (4-pin for cable assembly)
Contacts: JST SXH-001T-P0.6 (crimp terminals)

Standard wire colors:
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
- Direct 3.3V connection — HC-SR04+ / RCWL-1601 ECHO output matches 3.3V supply

**Pin Safety:**
- Both pins are located near each other on ESP32-C6 DevKit
- Easy PCB routing from header to ultrasonic connector
- No conflicts with I2C (GPIO4/5) or 1-wire (GPIO2)

### 5.9 Specifications and Limitations

**HC-SR04+ / RCWL-1601 Specifications:**
```
Operating Voltage: 3.0V–5.5V (3.3V or 5V compatible)
Operating Current: 15mA (typical), 2mA (idle)
Frequency: 40kHz ultrasonic
Detection Range: 2cm - 400cm
Accuracy: ±1.5mm (typical)
Measuring Angle: 15° cone
Trigger Input: 10µs pulse (3.3V logic)
Echo Output: 3.3V pulse proportional to distance (when powered at 3.3V)
Dimension: 45mm × 20mm × 15mm (HC-SR04+ same form factor)

vs original HC-SR04:
- HC-SR04: 5V only, ECHO outputs 5V → voltage divider required
- HC-SR04+ / RCWL-1601: 3.3V–5V, ECHO tracks VCC → no divider needed
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

**JSN-SR04T (Waterproof Ultrasonic)**
```
Advantages:
- Waterproof probe (IP67)
- Better for humid environments
- Less sensitive to temperature

Disadvantages:
- 5V only interface → requires voltage divider on ECHO (same as original HC-SR04)
- Larger, bulkier probe assembly

Cost: ~$3-5
Recommended for: Outdoor or very humid grow rooms where waterproofing is required
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
| No readings at all | No power or bad TRIG | Check 3.3V supply, verify TRIG pulse with scope |
| ECHO always HIGH | GPIO3 floating or shorted | Check connector wiring and PCB trace |
| Intermittent readings | Weak 3.3V supply near connector | Add 100nF decoupling cap near VCC pin |
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
1. Optional decoupling capacitor:
   - C1 (100nF): Near connector VCC pin for high-frequency decoupling

2. Keep TRIG and ECHO traces separated
   - Prevent crosstalk between output and input signals
   - Route on opposite sides of board if possible

3. Connector placement:
   - Board edge for easy access
   - Away from BNC connectors (avoid physical interference)

Note: No voltage divider resistors needed — simplified layout vs 5V HC-SR04.
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

### 6.1 Part Selection — Horizontal vs Vertical

Two mounting styles are suitable. **Horizontal side-mount is recommended** for OPNhydro:

```
Horizontal (side-mount):               Vertical (top/bottom-mount):

   ══════════ ← HIGH hole ══════          ┌──stem──┐   ← lid/top mount
   │          ┌───┤>────┐            │    │        │
   │    water │   float │            │    │  float │ hangs down
   │          └─────────┘            │    └────────┘
   ══════════ ← LOW hole ═══          ══════════════
```

| | Horizontal (LH25) ✅ | Vertical (M8000) |
|---|---|---|
| **Level precision** | Set by hole position (±5mm) | Depends on float travel distance |
| **Mounting** | Side wall, 1/2" NPT | Lid/top or side, 1/8" NPT |
| **NO/NC selection** | Flip float orientation | Fixed NC (M8000) |
| **Tank holes** | 2 × 1/2" side holes | 2 × 1/8" holes (top or side) |
| **Chemical resistance** | PP or PVDF | PP |
| **IP rating** | IP68 | Not rated |
| **Typical cost** | ~$25 each | ~$15 each |
| **Best for** | Open-top or side-access reservoir | Sealed lid, top-mount only |

**Key advantage of horizontal:** The sensing level is fixed by where you drill the hole — no float travel calculation, no ambiguity. Reef keepers have used these in similar chemical environments for decades.

---

### 6.2 Recommended: Flowline LH25-1101 (Horizontal, PP)

```
Contact:      SPST dry reed, selectable NO/NC by float orientation
Rating:       30VA @ 120V AC/DC — far exceeds 3.3V GPIO pullup current
Material:     Polypropylene (PP) body and float
Mount:        1/2" NPT side-wall bulkhead
Accuracy:     ±5mm in water
Repeatability:±2mm
Temperature:  -40°C to 105°C
Pressure:     100 psi max
IP rating:    IP68 (NEMA 6)
Wire:         2' (61cm), 2-conductor, 22 AWG
Float orient: Hinge UP = normally open; Hinge DOWN = normally closed
```

**Wire as NC (hinge pointing down):**
```
Float arm UP   (water at/above switch) → magnet actuates reed → NC CLOSED → GPIO LOW  (0)
Float arm DOWN (water below switch)    → magnet away from reed → NC OPEN  → GPIO HIGH (1)
```

**Mounting positions:**
```
FLOAT_FLOW  (GPIO0): Hole at LOW water mark  — GPIO HIGH = low-water alarm, stop pumps
FLOAT_HIGH  (GPIO1): Hole at HIGH water mark — GPIO HIGH = water above cutoff?

 ⚠ Note for FLOAT_HIGH with NC and hinge-down:
   GPIO HIGH when float arm DOWN = water BELOW the switch (normal during filling)
   GPIO LOW  when float arm UP   = water HAS REACHED the cutoff level → stop ATO

 Firmware must treat GPIO1 LOW as the ATO stop condition (inverse of FLOAT_FLOW).
 Alternatively, mount FLOAT_HIGH with hinge UP (NO) and treat GPIO1 HIGH as stop.
```

> **Alternative:** Madison M8000 (1/8" NPT vertical NC, PP, 30VA) if side-wall mounting is not possible (e.g., opaque rigid reservoir with no accessible side). Same GPIO circuit applies.

---

### 6.3 Circuit

```
Float Switch - FLOW (low level alarm, GPIO0):
        3.3V
         │
        R1
       10k (pullup)
         │
GPIO0 ───┼──────────────► LH25 FLOW (NC, hinge down) ──► GND
         │
        C1
       100nF (debounce)
         │
        ─┴─
        GND

Float Switch - HIGH (high level cutoff, GPIO1):
        3.3V
         │
        R1
       10k (pullup)
         │
GPIO1 ───┼──────────────► LH25 HIGH (NC, hinge down) ──► GND
         │
        C1
       100nF (debounce)
         │
        ─┴─
        GND
```

---

## 7. Pump Driver Circuits

> **✅ PROJECT DECISION:** Main circulation pump selected: **AUBIG DC40-1250**
>
> **Selection Criteria:**
> 1. **Price:** $12-18 (most affordable true 12V DC option)
> 2. **PWM Control:** Native PWM support for variable flow rate control
> 3. **Reliability:** Brushless motor, 30,000-50,000 hour lifespan
> 4. **Compatibility:** True 12V DC input, works with existing MOSFET driver design
>
> **Key Specifications:**
> - Flow: 500-510 L/H (130-135 GPH)
> - Current: 1.2A @ 12V (14.4W)
> - PWM capable via GPIO10 (25 kHz recommended)
> - Suitable for NFT, drip, and small-medium DWC systems

All pumps and the ATO valve use the same 12V rail and identical driver circuits.

### 7.1 12V Main Pump Driver

```
                                    12V
                                     │
                        ┌────────────┼────┬──── 12V rail
                        │            │    │
                        │           C2  ─┴─
                        │          100nF GND (local bypass)
                        │            │
                       D1          PUMP+
                    (SS34)          │
                        │          PUMP
                        │         (1.2A)
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q1            ├───┴── PUMP-
        │      │  IRLR2905      │
        │      │  (DPAK)        │
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

C2: 100nF / 50V ceramic (X7R, 0805)
- Local bypass capacitor for switching transients
- Place within 5mm of Q1 DRAIN pin
- Reduces high-frequency noise on 12V rail

Q1: IRLR2905 (Logic-level N-MOSFET, DPAK/TO-252)
- VDS = 55V, ID = 42A
- RDS(on) = 40mΩ @ VGS=4.5V, 27mΩ @ VGS=10V
- VGS(th) = 1.5V (works with 3.3V logic)
- Power dissipation: 1.2A² × 0.04Ω = 58mW
- Current margin: 35× (42A / 1.2A)
- SMD package for automated assembly
- PWM capable: ESP32 GPIO10 can output PWM for variable pump speed control

D1: SS34 (3A Schottky flyback diode, SMC)
- Handles main pump inductive kickback

**Main Pump Specifications:**

Recommended 12V DC submersible pumps for hydroponic circulation:

| Parameter | Specification | Notes |
|-----------|---------------|-------|
| **Voltage** | 12V DC ±10% | Matches system power rail |
| **Current** | 1.0-1.5A typical | Within IRLR2905 capacity (42A) |
| **Power** | 12-18W maximum | Current × voltage |
| **Flow Rate** | 600-1000 L/H | 158-264 GPH |
| **Head Height** | 2-3 meters | 6.5-10 feet max lift |
| **Type** | Submersible | Water-cooled, silent operation |
| **Material** | Food-safe plastic or SS | Aquarium/hydroponics rated |
| **Duty Cycle** | Continuous | 24/7 operation capable |
| **Connection** | Wire leads or barrel jack | See connector specs below |

**Recommended Pump Models:**

**Option 1: AUBIG DC40-1250 Brushless Submersible Pump** ✅ **PRIMARY RECOMMENDATION**

**Electrical Specifications:**
- Model: DC40-1250 (also available as DC40E-1250 with NPT fittings)
- Voltage: 12V DC nominal (11-13V operating range)
- Current: 1.0-1.2A @ 12V
- Power: 14.4W maximum
- Motor: Brushless DC (BLDC) with magnetic drive coupling

**Hydraulic Performance:**
- Flow Rate: 500-510 L/H (130-135 GPH) at zero head
- Maximum Head: 5.0m (16.4 ft)
- Inlet: 13.8mm (0.54") diameter
- Outlet: 10.0mm (0.39") diameter or 1/4" / 1/2" NPT threads (DC40E model)

**Physical & Environmental:**
- Dimensions: Compact design, ~90×60×70mm
- Material: PA66 + Glass fiber (chemical resistant)
- Waterproof Rating: IP68 (fully submersible)
- Noise Level: <40 dB (ultra-quiet operation)
- Lifespan: 30,000-50,000 hours (brushless motor)
- Operating Temp: Fresh or salt water compatible

**Advanced Features:**
- ✅ **PWM Speed Control**: Supports PWM signal input for variable flow rate
- ✅ **0-5V Analog Control**: Alternative speed control via analog voltage
- ✅ **Solar Compatible**: Can run directly from 12V battery/solar systems
- ✅ **Magnetic Drive**: No shaft seal = leak-proof, maintenance-free
- ✅ **Low Voltage Safety**: 12V DC eliminates shock hazard
- ✅ **Soft Start**: Brushless controller reduces inrush current

**Cost & Availability:**
- Price: $12-18 USD
- Sources: Amazon, eBay, AliExpress
- Part Numbers: DC40-1250 (wire leads), DC40E-1250 (NPT threads)

**Hydroponic System Suitability:**

| System Type | Reservoir | Flow Rate Needed | AUBIG DC40-1250 | Rating |
|-------------|-----------|------------------|-----------------|--------|
| NFT (Nutrient Film) | 20-40 gal | 400-600 L/H | 500-510 L/H | ✅ **Excellent** |
| DWC (Deep Water) | 20-30 gal | 600-800 L/H | 500-510 L/H | ✅ **Good** |
| Ebb & Flow | 20-30 gal | 600-800 L/H | 500-510 L/H | ✅ **Good** |
| Drip System | Any | 400-600 L/H | 500-510 L/H | ✅ **Excellent** |
| Large DWC | 50+ gal | 1000+ L/H | 500-510 L/H | ⚠️ **Marginal** |

**PWM Speed Control Implementation:**

The AUBIG DC40-1250 supports PWM speed control via the 12V power input. The ESP32-S3 can generate PWM on GPIO10 to modulate the MOSFET gate, providing variable pump speed:

```
PWM Duty Cycle vs Flow Rate (typical):
- 100% duty cycle: 500-510 L/H (full flow)
- 75% duty cycle: ~375-380 L/H (75% flow)
- 50% duty cycle: ~250-255 L/H (50% flow)
- 25% duty cycle: ~125-130 L/H (25% flow, may stall)
- Minimum: ~30-40% duty recommended to prevent stall

ESP32-S3 PWM Configuration (suggested):
- Frequency: 25 kHz (above audible range, smooth motor control)
- Resolution: 10-bit (0-1023 values for fine control)
- Channel: LEDC PWM channel 0
- Pin: GPIO10 (same as pump control)

Benefits of PWM Control:
- Adjust circulation rate for different growth stages
- Reduce power consumption during low-demand periods
- Lower noise levels at reduced speeds
- Fine-tune nutrient flow for optimal plant uptake
- Extend pump lifespan with reduced wear
```

**Power Supply Requirements:**

⚠️ **CRITICAL**: User reviews emphasize stable, adequate power supply is essential for reliability.

```
12V Power Supply Specification:
- Voltage: 12V DC ±5% regulation (11.4V - 12.6V)
- Current capacity: 2A minimum per pump (1.2A × 1.5 safety factor)
- Ripple voltage: <100mV p-p (brushless motor sensitive to noise)
- Startup inrush: ~1.8-2.0A for 50-100ms (motor startup)
- Wire gauge: 18 AWG minimum for <1% voltage drop

Recommended Power Supplies:
- For main pump only: 12V 3A regulated DC
- For full system (pump + dosing + ATO): 12V 5-10A regulated DC
- Quality: Mean Well, TDK-Lambda, or equivalent (low ripple essential)
```

**Installation Notes:**
1. Pump must be fully submerged in water before power-on (prevents dry-run damage)
2. Mount pump vertically or horizontally, avoid inverted position
3. Use 1/2" ID vinyl tubing or NPT fittings (DC40E model)
4. Add inline strainer/filter to prevent debris clogging impeller
5. Test PWM control at low duty cycles to find minimum stable speed
6. Allow 10-15 second startup delay in software for motor initialization

**Pros:**
- ✅ True 12V DC input (works with MOSFET driver)
- ✅ PWM speed control capable (variable flow rate)
- ✅ Brushless motor (long life, low maintenance)
- ✅ Ultra-quiet operation (<40dB)
- ✅ Magnetic drive (leak-proof, no seal wear)
- ✅ Solar/battery compatible
- ✅ Very affordable ($12-18)
- ✅ Proven in hydroponics and aquariums

**Cons:**
- ⚠️ Sensitive to power quality (needs stable 12V, low ripple)
- ⚠️ Lower flow than AC pumps (130 GPH vs 400 GPH)
- ⚠️ Quality control varies (check reviews before purchase)
- ⚠️ Must run submerged (cannot self-prime)
- ⚠️ Not suitable for large systems (>40 gallon reservoirs)

---

**Alternative Options:**

**Option 2: Generic 800L/H 12V DC Submersible (Higher flow)**
- Flow: 800 L/H (211 GPH) @ 12V 1.0-1.2A
- Head: 2.5m maximum
- Cost: $15-25
- Note: Usually NOT PWM compatible (brush motor)
- Best for: Larger DWC systems needing higher circulation

**Option 3: Seaflo/Shurflo 12V Water Pump (Commercial grade)**
- Flow: 480-720 L/H @ 12V 1.0-1.5A
- Features: Self-priming, pressure switch, RV/marine rated
- Fittings: 3/8" or 1/2" NPT threaded
- Cost: $25-40
- Note: Not PWM compatible (diaphragm pump)
- Best for: Systems requiring self-priming or dry-run protection

**Flow Rate Sizing Guide:**

| System Type | Recommended Flow | AUBIG DC40-1250 | Reservoir Turnover |
|-------------|------------------|-----------------|-------------------|
| NFT (Nutrient Film) | 400-600 L/H | ✅ 500-510 L/H | 2-3× per hour |
| Drip System | 400-600 L/H | ✅ 500-510 L/H | 1-2× per hour |
| Ebb & Flow (Flood/Drain) | 600-800 L/H | ⚠️ 500-510 L/H | 2× per hour (marginal) |
| DWC Small (20-30 gal) | 600-800 L/H | ⚠️ 500-510 L/H | 2-2.5× per hour |
| DWC Large (50+ gal) | 1000+ L/H | ❌ 500-510 L/H | Too low, use Option 2 |

**Note:** AUBIG DC40-1250 is optimized for NFT and drip systems. For large DWC or ebb & flow systems requiring >600 L/H, consider Option 2 (800L/H generic pump) or run two AUBIG pumps in parallel.

**Pump Power Connector:**

```
Phoenix Contact MSTB 2.5/2-ST-5.08 (2-position screw terminal)
- Pitch: 5.08mm (0.2")
- Wire size: 24-12 AWG (for 1.5A @ 12V)
- PCB mount: Through-hole or SMD
- Mating plug: MSTB 2.5/2-STF-5.08 (optional, can use direct wire)
- Alternative: Phoenix Contact 1803280 (same as I2C) for consistency

Pin Assignment:
Pin 1: 12V_PUMP (switched via Q1)
Pin 2: GND

Pump Side Connection Options:
1. Wire leads (most common) - strip and insert into screw terminal
2. 5.5×2.1mm barrel jack - add PCB-mount jack in parallel
3. Anderson Powerpole 15A - industrial alternative
```

**PCB Layout Notes:**
- Place screw terminal at board edge for easy access
- 12V trace width: 50 mil (1.27mm) minimum for main pump
- Keep Q1 and screw terminal close to minimize trace resistance
- Add test points for 12V_SWITCHED and GND for diagnostics
- **C2 (100nF bypass)**: Place within 5mm of Q1 DRAIN pin for best performance
```

### 7.2 12V Dosing Pump Drivers (×4)

```
Same circuit topology as main pump, but using smaller AO3400A MOSFETs.
All on 12V rail. Use separate MOSFET for each dosing pump.

                                    12V
                                     │
                        ┌────────────┼────┬──── 12V rail
                        │            │    │
                        │           C2  ─┴─
                        │          100nF GND (local bypass)
                        │            │
                       D1          PUMP+
                   (1N5819)         │
                        │          PUMP
                        │           │
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q2-Q5         ├───┴── PUMP-
        │      │  AO3400A       │
        │      │  (SOT-23)      │
        │      └───────┬────────┘
        │           SOURCE
        │              │
       R2             ─┴─
      100Ω            GND
        │
        │
GPIO ───┼────────┬─────────────────► Gate Drive
                 │
                R1
               10k
                 │
                ─┴─
                GND

Q2-Q5: AO3400A (Logic-level N-MOSFET, SOT-23)
- VDS = 30V, ID = 5.8A
- RDS(on) = 33mΩ @ VGS=4.5V
- Compact SOT-23 package
- Perfect for 300mA dosing pump loads
- Alternative: BSS214N (50V, 5A, 100mΩ)

D1: 1N5819 (1A Schottky flyback diode, SOD-123)
- Lower current rating sufficient for dosing pumps

GPIO Assignments:
GPIO11 ──► Q2: Pump pH Up
GPIO15 ──► Q3: Pump pH Down
GPIO19 ──► Q4: Pump Nutrient A
GPIO20 ──► Q5: Pump Nutrient B

**Dosing Pump Specifications:**

Recommended 12V DC peristaltic pumps for precise nutrient dosing:

| Parameter | Specification | Notes |
|-----------|---------------|-------|
| **Voltage** | 12V DC | Matches system power rail |
| **Current** | 150-300mA typical | Well within AO3400A capacity (5.8A) |
| **Power** | 2-4W | Low power consumption |
| **Flow Rate** | 50-100 mL/min | Precision dosing |
| **Type** | Peristaltic | Self-priming, no contamination |
| **Tubing** | Food-grade silicone | 4×6mm or 6×9mm common |
| **Duty Cycle** | Intermittent (1-5 min/day) | Short bursts for dosing |
| **Connection** | Wire leads (2-wire) | Red = +12V, Black = GND |

**Recommended Dosing Pump Models:**

**Option 1: Kamoer NKP-DC-B08 Peristaltic Pump** ✅ **PRIMARY RECOMMENDATION**
- Flow: 47-90 mL/min (tubing dependent)
- Current: 250-300mA @ 12V
- Power: 3-4W
- Tubing: BPT tube (imported, long lifespan), 2.5mm ID × 4.5mm OD or 3mm ID × 5mm OD
- Features:
  - Premium build quality (Kamoer brand reputation)
  - Self-priming and dry-run capable
  - Reversible flow (change polarity for backflow)
  - Ultra-quiet operation, low pulse (3-rotor design)
  - Imported BPT tubing (longer service life than silicone)
  - Snap-fit pump head (easy tube replacement and cleaning)
- Cost: $15-25 per pump (×4 = $60-100 total)
- Sources: Amazon, eBay, Robotistan, Robu.in
- Part Number: NKP-DC-B08D (black), NKP-DC-B08G (green), NKP-DC-B08B (various)
- Best for: **Recommended for OPNhydro** - proven reliability, worth the premium over generic
- Reviews: Praised for build quality and user experience in aquarium hobby

**Option 2: Generic 12V Peristaltic Dosing Pump (Budget Alternative)**
- Flow: 50-100 mL/min
- Current: 200-300mA @ 12V
- Tubing: Food-grade silicone, 4×6mm or 6×9mm
- Features: Self-priming, bidirectional, chemically resistant
- Cost: $8-15 per pump (×4 = $32-60 total)
- Sources: Generic "12V Peristaltic Pump" (Amazon, AliExpress)
- Brands: INTLLAB, generic Chinese pumps
- Best for: Tight budgets - saves $40-60 vs Kamoer, but lower reliability
- Note: May require more frequent tubing replacement (1-2 years vs 3-5 years)

**Option 3: Kamoer KDS Series (High precision stepper)**
- Models: KDS-FE-2-S17B (50mL/min), KDS-FE-2-S17C (100mL/min)
- Current: 150-250mA @ 12V
- Features: Stepper motor, high accuracy, TTL/analog control
- Cost: $30-50 per pump (×4 = $120-200 total)
- Best for: Applications requiring ±1% dosing accuracy (commercial/research)

**Dosing Pump Connector (×4):**

```
Phoenix Contact MSTB 2.5/2-ST-5.08 (2-position screw terminal) ×4
- One terminal block per pump (Q2-Q5)
- Wire size: 24-18 AWG (for 300mA @ 12V)
- Label silkscreen: "pH UP", "pH DN", "NUT A", "NUT B"

Pin Assignment (each pump):
Pin 1: 12V_PUMP_n (switched via Q2-Q5)
Pin 2: GND

Alternative Connector:
- Phoenix Contact 1792887 (pluggable, 2-pos, 5.08mm pitch)
- Allows easy pump replacement without rewiring
```
```

### 7.3 ATO Solenoid Valve Driver

```
Same circuit topology as dosing pumps, using AO3400A MOSFET.
Connected to 12V rail.
Uses normally-closed (NC) solenoid valve for fail-safe operation.

                                    12V
                                     │
                        ┌────────────┤
                        │            │
                       D1         VALVE+
                   (1N5819)         │
                        │         VALVE
                        │        (NC, 500mA)
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q6            ├───┴── VALVE-
        │      │  AO3400A       │
        │      │  (SOT-23)      │
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

Q6: AO3400A (Logic-level N-MOSFET, SOT-23)
- VDS = 30V, ID = 5.8A
- RDS(on) = 33mΩ @ VGS=4.5V
- Handles 500mA solenoid load with margin
- Power dissipation: ~8mW (very low)
- Alternative: BSS214N (50V, 5A, 100mΩ)

D1: 1N5819 (1A Schottky flyback diode, SOD-123)
- Sufficient for solenoid valve inductive spike suppression

**ATO Solenoid Valve Specifications:**

| Parameter | Specification | Notes |
|-----------|---------------|-------|
| **Type** | Normally Closed (NC) | Fail-safe: valve closes on power loss |
| **Voltage** | 12V DC | Matches system power rail |
| **Current** | 300-500mA typical | Within AO3400A capacity (5.8A) |
| **Power** | 4-6W | Coil power consumption |
| **Pressure** | 0-0.8 MPa (0-116 PSI) | Typical municipal water pressure |
| **Port Size** | 1/4" to 1/2" | NPT thread or hose barb |
| **Material** | Brass body, EPDM/NBR seal | Food-safe, corrosion resistant |
| **Orifice** | 2-10mm | Determines flow rate |
| **Response** | 50-100ms typical | Fast open/close |

**Recommended Solenoid Valve Models:**

**✅ Recommended: DIGITEN DC 12V 1/4" NC Quick-Connect**
- Model: DIGITEN K170403
- Port: 1/4" quick-connect (fits standard 1/4" OD tubing directly — no NPT adapter needed)
- Type: Direct-acting, zero-pressure rated (works on gravity-fed top-off tanks)
- Current: ~400mA @ 12V DC (4.8W)
- Material: Food-grade plastic body, NBR seal
- Pressure: 0–0.5 MPa (0–72 PSI)
- Cost: ~$10
- Best for: RO/clean water ATO on gravity or mains supply

> **Why not the 2V025-08 (ANGGREK/AirTAC)?** The 2V025 is a pneumatic valve (designed for air/gas) with an anodized aluminum body. It functions for clean water short-term but is not rated for continuous liquid service. Brass or food-grade plastic bodies are more appropriate for water ATO.

**Alternative: U.S. Solid 1/4" NC Nylon 12V** (~$15–20)
- Direct-acting, NPT threads, water-specific design
- Lower power than U.S. Solid brass model (~350mA)
- Best for: Installations needing NPT fittings and known-brand sourcing

**High-end: U.S. Solid 1/4" NC Brass/Viton** (~$20–30)
- Model: USS2-00051
- Brass body, Viton seal, IP65, direct-acting, 0–101 PSI
- Current: ~1.17A (14W) — **update power budget if selected**
- Best for: Commercial/long-life installations; note high coil current

**ATO Valve Connector:**

```
Phoenix Contact MSTB 2.5/2-ST-5.08 (2-position screw terminal)
- Wire size: 24-18 AWG (for 500mA @ 12V)
- Label silkscreen: "ATO VALVE" or "WATER IN"

Pin Assignment:
Pin 1: 12V_VALVE (switched via Q6)
Pin 2: GND

Valve Side Connection:
- Most solenoid valves have 2-wire leads (polarity doesn't matter for DC)
- Some have wire connectors (DIN 43650A common)
- Strip and insert into screw terminal, or add mating connector
```

**Safety Notes:**
- ✅ NC valve ensures no water flow if controller loses power
- ✅ Float switch (GPIO1 - FLOAT_HIGH) provides hardware backup cutoff
- ✅ Float switch (GPIO0 - FLOAT_FLOW) provides low-level alarm
- ✅ Software timeout prevents flooding if level sensor fails
- ✅ Recommend inline manual shutoff valve for maintenance
- ✅ Consider water leak sensor near reservoir for additional protection

**Valve Installation:**
1. Install valve inline on water supply line (before reservoir)
2. Arrow on valve body indicates flow direction
3. Mount valve with coil vertical (prevents water ingress)
4. Use thread sealant (Teflon tape or pipe dope) on NPT threads
5. Test valve operation before connecting to reservoir
```

### 7.4 MOSFET Selection Summary

**Design Strategy:** All-SMD design with appropriately-sized MOSFETs for each load type.

| Load | Current | MOSFET | Package | RDS(on) @ 4.5V | Margin | Rationale |
|------|---------|--------|---------|----------------|--------|-----------|
| **Main Pump (AUBIG DC40-1250)** | 1.2A | **IRLR2905** | DPAK | 40mΩ | 35× | PWM capable, SMD |
| **Dosing Pumps (4×)** | 300mA | **AO3400A** | SOT-23 | 33mΩ | 19× | Low cost, efficient |
| **ATO Solenoid** | 500mA | **AO3400A** | SOT-23 | 33mΩ | 11× | Low cost, efficient |

**Power Dissipation Analysis:**
- IRLR2905 (Main pump): 1.2A² × 0.04Ω = **58mW** (DPAK handles easily)
- AO3400A (Dosing): 300mA² × 0.033Ω = **3mW** (negligible for SOT-23)
- AO3400A (ATO): 500mA² × 0.033Ω = **8mW** (very low for SOT-23)

**Benefits:**
- ✅ **100% SMD design** - entire board can use pick-and-place assembly
- ✅ **Compact footprint** - DPAK + 5× SOT-23 (vs 6× TO-220 through-hole)
- ✅ **Production-friendly** - no manual through-hole soldering required
- ✅ **Lower assembly cost** - automated SMD assembly throughout
- ✅ **Appropriate sizing** for each load (not overkill)
- ✅ **All logic-level compatible** (work with 3.3V GPIO)
- ✅ **Consistent design** - all MOSFETs are SMD packages
- ✅ **AO3400A optimization** - Lower RDS(on) (33mΩ vs 100mΩ), lower cost ($0.10 vs $0.20)

**Part Numbers:**
- Q1 (Main Pump): **IRLR2905** or IRLR2905ZPBF (Infineon, DPAK/TO-252)
- Q2-Q5 (Dosing Pumps): **AO3400A** (Alpha & Omega, SOT-23) - Primary choice
- Q6 (ATO Solenoid): **AO3400A** (Alpha & Omega, SOT-23) - Primary choice
- Alternative for Q2-Q6: BSS214N / BSS214NH6327XTSA1 (Infineon, 5A, SOT-23)

### 7.5 Pump and Valve BOM Summary

> **Main Pump Selection: AUBIG DC40-1250** ✅
> - **Chosen for:** Best price ($12-18) + PWM control capability
> - **Advantages:** Variable flow rate, long lifespan, low power consumption
> - **Suitable for:** NFT, drip systems, small-medium DWC (20-30 gal)

**Complete bill of materials for hydraulic components:**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Brushless | AUBIG DC40-1250, 510L/H, 12V 1.2A | $12-18 | $15 | ✅ Selected for price + PWM |
| **pH Up Dosing Pump** | 1 | Peristaltic | Kamoer NKP-DC-B08, 47-90mL/min | $15-25 | $20 | ✅ Selected for reliability |
| **pH Down Dosing Pump** | 1 | Peristaltic | Kamoer NKP-DC-B08, 47-90mL/min | $15-25 | $20 | ✅ BPT tubing, premium build |
| **Nutrient A Dosing Pump** | 1 | Peristaltic | Kamoer NKP-DC-B08, 47-90mL/min | $15-25 | $20 | ✅ BPT tubing, premium build |
| **Nutrient B Dosing Pump** | 1 | Peristaltic | Kamoer NKP-DC-B08, 47-90mL/min | $15-25 | $20 | ✅ BPT tubing, premium build |
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403, 1/4" QC, 12V 400mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Power Connectors** | 6 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $3 | 2-position, 5.08mm pitch |
| | | | | **Subtotal:** | **$110** | ✅ Recommended configuration |

**Why these components were selected:**

**AUBIG DC40-1250 (Main Pump):**
- ✅ **Lowest cost:** $12-18 vs $20-40 for alternatives
- ✅ **PWM control:** Variable flow rate via ESP32 GPIO10
- ✅ **Long lifespan:** Brushless motor, 30k-50k hours
- ✅ **True 12V DC:** Works with existing MOSFET driver (no AC required)
- ✅ **Suitable for:** NFT, drip, and small-medium DWC systems (20-30 gal)
- ⚠️ **Not for:** Large DWC (50+ gal) - use higher-flow alternative below

**Kamoer NKP-DC-B08 (Dosing Pumps):**
- ✅ **Better reliability:** Proven Kamoer brand reputation in aquarium/hydro industry
- ✅ **BPT tubing:** Imported, longer lifespan than silicone (3-5 years vs 1-2 years)
- ✅ **Self-priming + dry-run capable:** Prevents damage if reservoir runs low
- ✅ **Reversible flow:** Change polarity for backflow/cleaning cycles
- ✅ **Quieter operation:** 3-rotor design, ultra-low pulse
- ✅ **Easy maintenance:** Snap-fit pump head for quick tube replacement
- ✅ **Worth the premium:** Only $40-60 more total (×4) vs generic, significant reliability gain
- **Best for:** Reliable dosing without spending $120-200 on stepper pumps

**Budget Alternative Configuration (Generic Pumps):**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Brushless | AUBIG DC40-1250, 510L/H, 12V 1.2A | $12-18 | $15 | ✅ PWM capable, proven reliable |
| **Dosing Pumps (×4)** | 4 | Peristaltic | Generic 50-100mL/min, 12V 300mA | $8-15 | $40 | Budget option, silicone tubing |
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403, 1/4" QC, 12V 400mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Power Connectors** | 6 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $3 | 2-position, 5.08mm pitch |
| | | | | **Subtotal:** | **$70** | Minimum viable, lower reliability |

**Note:** Generic pumps save $40-60 but may require more frequent tubing replacement and have higher failure rates.

**Professional/Commercial Configuration (Kamoer KDS Stepper Pumps):**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Brushless | AUBIG DC40-1250, 510L/H, 12V 1.2A | $12-18 | $15 | ✅ PWM capable, proven reliable |
| **Dosing Pumps (×4)** | 4 | Peristaltic | Kamoer KDS-FE-2-S17B | $30-50 | $160 | Stepper motor, ±1% accuracy |
| **ATO Solenoid Valve** | 1 | NC Solenoid | U.S. Solid 1/4" NC Brass/Viton, 12V ~1.17A | $20-30 | $25 | IP65, direct-acting — note: 14W coil, update power budget |
| **Power Connectors** | 6 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $3 | 2-position, 5.08mm pitch |
| **12V Power Supply** | 1 | Regulated | Mean Well LRS-50-12 (50W, 4.2A) | $15-20 | $18 | Low ripple for brushless motor |
| | | | | **Subtotal:** | **$221** | Professional/commercial grade |

**For Large Systems (50+ gal DWC/Ebb & Flow):**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Submersible | Generic 800L/H, 12V 1.5A | $15-25 | $20 | Higher flow, no PWM |
| OR: **Dual AUBIG Pumps** | 2 | Brushless | AUBIG DC40-1250 (parallel) | $12-18 | $30 | 1000L/H total, redundant |
| **Dosing Pumps (×4)** | 4 | Peristaltic | Generic 50-100mL/min | $8-15 | $48 | Budget peristaltic |
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403, 1/4" QC, 12V 400mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Power Connectors** | 6 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $3 | 2-position, 5.08mm pitch |
| | | | | **Subtotal:** | **$83-113** | Budget, higher flow rate |

**Connector Summary:**

| Location | Connector | Part Number | Pins | Purpose |
|----------|-----------|-------------|------|---------|
| J? (Main Pump) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |
| J? (pH Up) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |
| J? (pH Down) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |
| J? (Nutrient A) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |
| J? (Nutrient B) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |
| J? (ATO Valve) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | 2 | 12V switched + GND |

**Wiring Specifications:**

- **Wire gauge:** 22-18 AWG for dosing pumps and valve (300-500mA)
- **Wire gauge:** 18 AWG for main pump AUBIG DC40-1250 (1.2A, <1% drop @ 3ft)
- **Wire type:** Stranded copper, 300V rated minimum
- **Insulation:** PVC or silicone (silicone preferred for flexibility)
- **Color code:** Red = +12V switched, Black = GND
- **Recommended:** Use ferrule crimps for screw terminal connections (prevents strand fraying)
- **Critical:** For AUBIG pump, keep wire runs short (<3ft) and use quality connectors to minimize voltage drop

**Total System Power Budget (12V rail):**

| Load | Current | Power | Duty Cycle | Avg Power | Notes |
|------|---------|-------|------------|-----------|-------|
| Main Pump (AUBIG DC40-1250) | 1.2A | 14.4W | 100% (continuous) | 14.4W | Brushless, PWM capable |
| pH Up Pump (Peristaltic) | 0.3A | 3.6W | <1% (1-2 min/day) | 0.04W | Intermittent |
| pH Down Pump (Peristaltic) | 0.3A | 3.6W | <1% (1-2 min/day) | 0.04W | Intermittent |
| Nutrient A Pump (Peristaltic) | 0.3A | 3.6W | <1% (1-2 min/day) | 0.04W | Intermittent |
| Nutrient B Pump (Peristaltic) | 0.3A | 3.6W | <1% (1-2 min/day) | 0.04W | Intermittent |
| ATO Valve (NC Solenoid) | 0.4A | 4.8W | <10% (periodic refill) | 0.48W | Normally closed |
| **Peak Total** | **2.8A** | **33.6W** | If all run simultaneously | - | Rare condition |
| **Typical Avg** | **~1.3A** | **~15W** | Normal operation | - | Main pump only |

**12V Power Supply Recommendation:**

⚠️ **CRITICAL for AUBIG DC40-1250**: Brushless motor requires stable, low-ripple DC power supply.

| Specification | Minimum | Recommended | Ideal (Commercial) |
|---------------|---------|-------------|-------------------|
| **Voltage** | 12V DC ±5% | 12V DC ±2% | 12V DC ±1% |
| **Current** | 3A (36W) | 5A (60W) | 10A (120W) |
| **Ripple** | <200mV p-p | <100mV p-p | <50mV p-p |
| **Regulation** | Line ±5% | Line/Load ±2% | Line/Load ±1% |
| **Inrush Handling** | 2× rated | 2× rated | 3× rated |
| **Use Case** | Budget (no PWM) | Standard (PWM OK) | Professional |

**Recommended Power Supply Models:**
- **Mean Well LRS-50-12** (50W, 4.2A) - $15-20, low ripple, reliable
- **Mean Well RS-75-12** (75W, 6A) - $20-30, DIN rail mount option
- **TDK-Lambda LS50-12** (50W, 4.2A) - $25-35, medical grade, ultra-low ripple
- **Generic 12V 5A "switching adapter"** - $10-15, acceptable if low ripple verified

**Power Supply Notes:**
1. ⚠️ **Avoid cheap "12V 5A" adapters** - high ripple can cause AUBIG pump motor jitter/noise
2. Verify ripple voltage with oscilloscope if using generic power supply
3. Add 470µF-1000µF bulk capacitor near pump connector if ripple >100mV
4. Use 18 AWG wire minimum from PSU to PCB (for <1% voltage drop)
5. Consider UPS/battery backup for main pump to prevent plant stress during power outages

---

## 8. Status LED

The ESP32-C6-DevKitC-1 includes a built-in RGB LED (WS2812B) on GPIO8.
No external status LED is needed on the OPNhydro PCB.

Use GPIO8 in firmware for status indication (do not route GPIO8 to any PCB pad).

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
