# Schematic Design Guide

This document describes the circuit design for the OPNhydroponics controller PCB.

## Block Diagram

```
                       ┌─────────────────────────────────────────────────────┐
                       │                    CONNECTORS                       │
                       │  ┌─────┐ ┌─────┐ ┌─────┐  ┌──────────┐ ┌─────────┐  │
                       │  │ BNC │ │ BNC │ │ BNC │  │ Float SW │ │Ultrasoni│  │
                       │  │ pH  │ │ EC  │ │ RTD │  │  2×JST2P │ │c  JST4P │  │
                       │  └──┬──┘ └──┬──┘ └──┬──┘  └────┬─────┘ └────┬────┘  │
                       └─────┼───────┼───────┼──────────┼────────────┼───────┘
                             │       │       │          │            │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    PCB                                          │
│  ┌─────────────┐   ┌───────────────────────────────────────────────────────┐    │
│  │   POWER     │   │                       SENSORS                         │    │
│  │             │   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │    │
│  │ 24V ──►5V   │   │  │ EZO-pH │  │ EZO-EC │  │EZO-RTD │  │ BME280 │       │    │
│  │     ──►3.3V │   │  │  I2C   │  │  I2C   │  │  I2C   │  │  I2C   │       │    │
│  │             │   │  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘       │    │
│  └──────┬──────┘   │      └───────────┴───────────┴───────────┘            │    │
│         │          │                        │ I2C Bus                      │    │
│         │          │  ┌──────────────────┐  ┌───────────────────────────┐  │    │
│         │          │  │    HC-SR04       │  │    Float SW (×2)          │  │    │
│         │          │  │  TRIG: GPIO7     │  │    LOW:  GPIO0            │  │    │
│         │          │  │  ECHO: GPIO3     │  │    HIGH: GPIO1            │  │    │
│         │          │  └──────────────────┘  └───────────────────────────┘  │    │
│         │          └───────────────────────────────────────────────────────┘    │
│         │                                   │                                   │
│         │          ┌────────────────────────┴─────────────────────────────┐     │
│         │          │               ESP32-C6-WROOM-1                       │     │
│         │          │  ┌──────────────────────────────────────────────┐    │     │
│         └─────────►│  │  GPIO4/5: I2C        GPIO2:  ATO_VALVE       │    │     │
│                    │  │  GPIO7:   HC_TRIG    GPIO3:  HC_ECHO         │    │     │
│                    │  │  GPIO0:   FLOAT_LOW  GPIO1:  FLOAT_HIGH      │    │     │
│                    │  │  GPIO6:   EZO_PDIS   GPIO10: PUMP_MAIN       │    │     │
│                    │  │  GPIO11:  STEP_PH_DN GPIO15: STEP_NUT_A      │    │     │
│                    │  │  GPIO19:  STEP_NUT_B GPIO21/22: TMC_UART     │    │     │
│                    │  └──────────────────────────────────────────────┘    │     │
│                    └──────────────────────────────────────────────────────┘     │
│                                            │                                    │
│         ┌──────────────────────────────────┼──────────────────────────────┐     │
│         │           PUMP/VALVE DRIVERS (all 24V)                          │     │
│         │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │     │
│         │  │ 24V    │  │ 24V    │  │ 24V    │  │ 24V    │  │ 24V    │     │     │
│         │  │ Main   │  │ pH Dn  │  │ Nut A  │  │ Nut B  │  │ ATO    │     │     │
│         │  │ Pump   │  │ Dose   │  │ Dose   │  │ Dose   │  │ Valve  │     │     │
│         │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘     │     │
│         └─────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Power Supply Section

### 1.1 Input Protection

```
24V DC IN ──┬──[PTC 5A]──┬──[TVS 28V]──┬──► 24V_PROTECTED
            │            │             │
           ─┴─          ─┴─           ─┴─
           GND          GND           GND

Component Selection:
- PTC: RXEF500 (5A hold, 10A trip)
- TVS: SMBJ28A (28V standoff, 45.4V clamp) — for 24V rail; SMBJ15A was for 12V only
```

### 1.2 Reverse Polarity Protection

P-channel MOSFET in series with the supply. Source is the unprotected input;
Drain is the protected output. R1 (10kΩ) connects Source to Gate; R2 (100kΩ)
connects Gate to GND.

```
                              Q1 (P-MOSFET, SOT-23)
                         ┌────────────────────────┐
                         │  S                  D  │
24V_PROTECTED ───────────┤  (in)          (out)   ├──────────── 24V_SAFE
                         │           G            │
                         └───────────┬────────────┘
                                     │
                          ┌──────────┘
                          │  (R1 10kΩ — Source to Gate)
                     Source (24V_PROTECTED)
                          │
                         [R1]
                         10kΩ
                          │
                         Gate ──────[R2 100kΩ]──── GND
```

**How it works:**

Normal polarity (+24V at Source):
- Vgate = 24V × R2/(R1+R2) = 24 × 100/(10+100) ≈ 21.8V
- Vgs = 21.8 − 24 = **−2.2V** → P-ch FET turns ON
- Current flows Source→Drain; voltage drop = I × Rds(on)

Reverse polarity (supply plugged backwards → Source at −24V):
- Vgate = −24V × 100/(10+100) ≈ −21.8V
- Vgs = −21.8 − (−24) = **+2.2V** → P-ch FET stays OFF; channel does not conduct

⚠ **Component rating note — SI2301 is not suitable for 24V:**
The SI2301 has Vds(max) = −20V. On reverse polarity the full supply voltage appears across D-S; at 24V this exceeds the rating. Replace with a 30V-rated SOT-23 device.

**Recommended replacement: AO3401A** (P-ch, −30V Vds, 4A, Rds(on) 45mΩ, SOT-23)
- Vgs(th) = −0.45 to −1V; Vgs = −2.2V with the 10kΩ/100kΩ divider → FET fully ON
- Vgs(max) = ±12V; Vgs = −2.2V at 24V → well within rating
- Drop-in SOT-23 replacement for SI2301

### 1.3 Buck Converter

**Design Rationale — why a switching buck converter for 24V→5V:**
A linear regulator dropping 24V to 5V would dissipate P = (24−5) × I = 19×I watts as heat. At 500mA load that's 9.5W — requiring a large heatsink and dominating PCB thermal budget. The TPS62933 synchronous buck operates at ~90% efficiency: at 500mA load it
dissipates only ~(1−0.9) × 24×0.5 = 1.2W.
Noise and ripple from the switcher are acceptable on the 5V rail, which only powers the HC-SR04 and WS2812B; sensitive analog/RF loads run on the 3.3V LDO downstream.

**24V to 5V (Logic/USB)**
```
                        Cbst
            ┌──────────┤├───────────────────────────────┐
            │         100nF                             │
            │                                      BST─┘
24V_SAFE ───┼──[Cin]──┬──────────────────────────┐
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
- Cin:  10µF / **50V** ceramic (X5R or X7R)
- Cout: 2×22µF / 10V ceramic (X5R or X7R)
- Cbst: 100nF / 10V ceramic (BST to SW)
- Css:  10nF (soft-start ≈ 1.5ms; minimum 6.8nF, do not float)
- Rrt:  47kΩ to GND → Fsw = 1MHz
- R_top: 200kΩ 1%
- R_bot:  38.3kΩ 1% (E96 series)
- No external compensation required (internal loop compensation)
- No external diode required (synchronous rectification)

Note: 24V rail powers pumps and ATO valve directly.

**Additional Output Capacitance for Motor Loads:**

⚠️ **CRITICAL**: Add bulk capacitance beyond standard buck converter output caps

```
Recommended Additional Capacitors on 5V Rail:

```
5V ──┬──[2×22µF]──┬──[1000µF]──┬──[100nF]──► To ESP32 + Loads
     │  (standard │   (bulk    │  (HF
     │   Cout)    │   added)   │   filter)
    ─┴─          ─┴─          ─┴─
    GND          GND          GND
```

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

### 1.4 LDO (3.3V)

**Design Rationale — why a linear LDO for 5V→3.3V:**
The ESP32-C6's RF (Wi-Fi 6, BLE 5) and 12-bit SAR ADC are sensitive to supply noise.
A switching regulator on the 3.3V rail would inject switching ripple at its operating frequency (hundreds of kHz) directly into the ADC reference and RF supply — degrading ADC accuracy and potentially increasing Wi-Fi packet error rate. An LDO has no switching element; its output noise floor is limited only by its PSRR and output capacitance, typically <50µVrms. The 1.7V dropout (5V→3.3V) means only P = 1.7 × 0.35 = 0.6W worst case — manageable on a small SOT-223 package without a heatsink.

```
5V ──┬──[10µF]──┬──► VIN ┌─────────┐ VOUT ──┬──[10µF]──┬──► 3.3V
     │          │        │ AMS1117 │        │          │
    ─┴─        ─┴─       │  -3.3   │       ─┴─        ─┴─
    GND        GND       └────┬────┘       GND        GND
                              │
                             ─┴─
                             GND
```

### 1.5 24V Rail Bulk Capacitance (Motor Loads)

⚠️ **CRITICAL**: Brushless motor (AUBIG DC40-1250) requires substantial bulk capacitance for startup inrush

```
24V Power Supply Filtering:

24V_PSU ──┬──[2200µF]──┬──[100nF]──┬──► To MOSFET drivers
          │  (bulk)    │  (HF)     │
         ─┴─          ─┴─          ─┴─
         GND          GND          GND
```

Components:
- C_bulk: 2200µF / **50V** low-ESR electrolytic (Panasonic FR series or equivalent)
  * Purpose: Buffer motor startup inrush current (AUBIG DC40-1250: ~2A for 50-100ms)
  * Prevents voltage sag that could reset ESP32 or cause pump stall
  * Place at 24V input near main pump MOSFET Q1

- C_hf: 100nF / 50V ceramic (X7R)
  * Purpose: High-frequency noise filtering from motor commutation
  * Place near 24V input connector

Why 2200µF?
- AUBIG brushless motor startup inrush: ~2A for 50-100ms (1.67× nominal 1.2A)
- Buck converter output caps: typically 47-220µF (insufficient for motor loads)
- Voltage sag calculation: ΔV = I × Δt / C
- Target: <200mV sag → C = 2A × 0.1s / 0.2V = 1000µF minimum
- Use 2200µF for safety margin and multiple pump operation

Additional Local Bypass Capacitors:
- Place 100nF ceramic (0805, X7R, 50V) near each MOSFET (Q1-Q6)
- Connects between 24V drain and GND
- Provides local energy storage for switching transients
- Reduces high-frequency noise on 24V rail

```
24V Distribution Layout:
┌──────────────────────────────────────────────────────────┐
│ 24V PSU                                                  │
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
```
IMPORTANT Power Supply Selection:
- Use PSU with built-in soft-start (Mean Well LRS-150-24 ✅)
- Generic PSUs may trip overcurrent during capacitor charging + motor startup
- Without soft-start: inrush can exceed 10A briefly (2.2mF × dV/dt)

### 1.6 PCB Layout Guidelines for Power Integrity

**Critical Layout Rules:**

1. **Star Ground Configuration:**
   ```
   ESP32 GND ───┐
   Sensors GND ─┼──► Single ground point at 24V PSU GND terminal
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

   24V Rail (3.5A peak):
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
   - Layer 3: Power planes (3.3V, 5V, 24V pours)
   - Layer 4 (Bottom): Ground plane
   ```

5. **Keep-Out Zones:**
   ```
   - ESP32 antenna area: No ground pour, no traces, no vias
   - I2C traces: Route away from 24V pump power traces (>10mm separation)
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
   ✅ Solution: Add ferrite beads on 24V pump power lines (BLM15HD182SN1)
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
| 24V PSU input | 2200µF **50V** electrolytic | 1 | Panasonic EEU-FR1E222 | Motor startup buffering |
| 24V PSU input | 100nF 50V ceramic | 1 | Generic X7R 0805 | HF filtering |
| Per MOSFET Q1-Q6 | 100nF 50V ceramic | 6 | Generic X7R 0805 | Local bypassing |
| **Total** | | **10** | | **~$3-4 total** |

---

## 2. ESP32-C6 Section

### 2.1 DevKit Pin Headers

The ESP32-C6-DevKitC-1-N8 mounts to the carrier PCB via 2×20 pin headers. USB-C, boot/reset buttons, antenna, and power regulation are on the DevKit.

```
                    ┌─────────────────────────────────────┐
                    │        ESP32-C6-DevKitC-1-N8        │
                    │     (includes USB-C, antenna,       │
                    │      boot/reset buttons, RGB LED)   │
                    │                                     │
           3.3V ────┤ 3V3                            GND  ├──── GND
            5V ─────┤ 5V (from USB or external)           │
                    │                                     │
    FLOAT_LOW ──────┤ GPIO0  (input)                      │
   FLOAT_HIGH ──────┤ GPIO1  (input)                      │
    ATO_VALVE ──────┤ GPIO2  (output)                     │
       US_ECHO ─────┤ GPIO3  (input)                      │
       I2C_SDA ─────┤ GPIO4  (bidirectional)              │
       I2C_SCL ─────┤ GPIO5  (output)                     │
      EZO_PDIS ─────┤ GPIO6  (output)                     │
                    │                                     │
      US_TRIG ──────┤ GPIO7  (output)                     │
                    │                                     │
     (reserved) ────┤ GPIO8  (RGB LED on DevKit)          │
    (available) ────┤ GPIO9  (strapping pin — 45kΩ pullup) │
     PUMP_MAIN ─────┤ GPIO10 (output)                     │
    STEP_PH_DN ─────┤ GPIO11 (output)                     │
                    │                                     │
    STEP_NUT_A ─────┤ GPIO15 (output, strapping pin)      │
     (reserved) ────┤ GPIO16 (CP2102N UART0 TX)           │
     (reserved) ────┤ GPIO17 (CP2102N UART0 RX from CP)   │
   (available) ─────┤ GPIO18 (available)                  │
    STEP_NUT_B ─────┤ GPIO19 (output)                     │
   (available) ─────┤ GPIO20 (available)                  │
                    │                                     │
 TMC2209_UART_RX ───┤ GPIO21 (input)                      │
 TMC2209_UART_TX ───┤ GPIO22 (output)                     │
    (available) ────┤ GPIO23 (available)                  │
                    │                                     │
                    └─────────────────────────────────────┘

Signal Type Key:
  (input)         = Input only
  (output)        = Output only
  (bidirectional) = Bidirectional (I2C)
```

### 2.2 Dual-Function Pin Considerations

#### GPIO8 — On-board RGB LED (reserved)
The DevKitC drives an on-board WS2812B RGB LED from GPIO8 through a series resistor.
Do not connect an external load to GPIO8 on the carrier PCB.
The LED is available for firmware status indication (boot state, error codes, etc.).

#### GPIO9 — Internal ~45kΩ pull-up (strapping pin, currently available)
GPIO9 is sampled at boot to select the boot mode:
- **HIGH** at boot (pull-up default) → normal application boot
- **LOW** at boot → enter ROM serial download mode

The internal pull-up holds GPIO9 HIGH in the absence of external drive, so normal boot
always succeeds when the pin is left unconnected. If GPIO9 is used in a future revision,
ensure any external load cannot pull it LOW during the boot window (~100ms after power-on
/ reset de-assertion).

#### GPIO12 / GPIO13 — USB D− / D+ (Serial logging, code upload, JTAG)
GPIO12 and GPIO13 are the USB D− and D+ lines on the ESP32-C6. The DevKitC connects
these directly to the USB-C connector for three simultaneous use cases:
- **Serial logging** via USB CDC (replaces UART0 for debug output)
- **Firmware upload** via esptool over USB CDC (no external programmer needed)
- **JTAG debugging** via USB (OpenOCD — no separate JTAG adapter needed)

Do not route GPIO12/GPIO13 to the carrier PCB. They are occupied by the DevKit USB
interface and must remain exclusive to the USB-C connector.

#### GPIO15 — TMC2209 STEP pull-down (strapping pin, STEP_NUT_A)
GPIO15 is a strapping pin. OPNhydro uses GPIO15 for STEP_NUT_A (TMC2209 STEP input for
the Nutrient A stepper driver). The TMC2209 STEP input has a 10kΩ pull-down on the PCB.
At boot, the ESP32-C6 samples GPIO15:
- The 10kΩ pull-down holds GPIO15 LOW → **ESP32 ROM boot messages are suppressed** on
  the UART0 TX pin. This is cosmetic only and has no effect on application operation.
- The pull-down also holds STEP_NUT_A LOW at power-on — no step pulses are generated
  before firmware runs. This is the correct fail-safe behaviour.

#### GPIO16 — CP2102N UART0 TX (reserved, do not connect externally)
GPIO16 is the ESP32-C6 UART0 TX output. On the DevKitC-1, this connects to the CP2102N
USB-UART bridge RX input. UART0 may transmit ROM boot messages and other serial data.
Do not route GPIO16 to the carrier PCB for any other purpose. Any external load would
corrupt serial output and could interfere with boot-time messages.

> Note: GPIO15's pull-down suppresses ROM messages on UART0 TX (GPIO16). Even so,
> GPIO16 remains occupied by the CP2102N connection and must not be used.


#### GPIO17 — CP2102N UART TX (reserved, do not connect)
GPIO17 is actively driven by the CP2102N USB-to-UART bridge TX output on the DevKitC.
Do not route GPIO17 to the carrier PCB. Any external connection would fight the CP2102N
output and could damage the bridge IC or the ESP32-C6 input buffer.

#### GPIO21 / GPIO22 — TMC2209 UART bus (RX / TX)
GPIO21 and GPIO22 are assigned to the TMC2209 single-wire UART bus (ESP32-C6 UART1):
- GPIO22: UART1 TX → drives the shared PDN_UART bus
- GPIO21: UART1 RX ← receives responses from the addressed TMC2209

See §7.2 for the UART wiring diagram, address table, and configuration registers.

#### GPIO23 — Available
No assignment. Leave unconnected on the carrier PCB.

#### ~RST — Reset input
- **Leave floating** — internally held HIGH by the chip; normal operation
- **Optional external reset button**: normally-open push-button from ~RST to GND on the
  carrier PCB; add 100nF bypass capacitor from ~RST to GND to suppress glitches
- **Do not drive HIGH externally** — the pin is already pulled HIGH internally
- A LOW pulse ≥1µs resets the device; the DevKitC on-board RST button does the same

---

### 2.3 Carrier PCB Headers

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
| Isolation needed | Yes (ADM3260 per circuit — integrated isoPower) | Yes (same requirement) |
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

> **Isolation:** EZO-pH (MEZZ3) and EZO-EC (MEZZ2) each have a dedicated ADM3260 (U3 and U4 respectively) which provides both I2C signal isolation and isolated DC power via integrated isoPower (up to 150mW, 3.15–5.25V output) — no separate DC-DC converter needed. EZO-RTD (MEZZ1) does **not** require isolation — connect directly to the 3.3V rail.

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
| 24V power management | No | Yes |
| Open hardware | No | Yes |
| Custom firmware | Limited (ThingSpeak) | Full control |

The kit is a self-contained monitoring appliance, not a controller platform. It covers only pH, EC, and temperature — no DO, no actuation, and no 24V rail. The OPNhydro custom PCB is required to meet all system requirements.

**Total cost (circuits + probes):** ~$653 all three | ~$590 via kits | ~$394 pH + EC only (no DO)

---

### 3.3 EZO Circuit Connections

```
Atlas Scientific EZO circuits use standard I2C.
Default addresses:
- EZO-pH:  0x63  (MEZZ3, isolated via U3 ADM3260)
- EZO-EC:  0x64  (MEZZ2, isolated via U4 ADM3260)
- EZO-RTD: 0x66  (MEZZ1, no isolation required)
- BME280:  0x76

EZO-pH and EZO-EC (isolated via ADM3260):

                                         GPIO6 (EZO_PDIS)
                                              │
┌──────────────────────────────────────┐   ┌──┴───────────────────────┐
│  EZO-pH (MEZZ3) or EZO-EC (MEZZ2)    │   │  ADM3260 (U3 or U4)      │
│                                      │   │                          │
│   VCC ◄──── 3.3V_ISO ────────────────┼───┤ isoPower out   VCC1◄─3.3V│
│   GND ◄──── GND_ISO  ────────────────┼───┤ GND_ISO        PDIS◄─────┘
│   SDA ◄───► I2C SDA  ────────────────┼───┤ SDA2 ◄──► SDA1           │
│   SCL ◄──── I2C SCL  ────────────────┼───┤ SCL2 ◄─── SCL1           │
│   PRB ◄──── BNC panel-mount          │   └──────────────────────────┘
│                                      │
└──────────────────────────────────────┘

GPIO6 (EZO_PDIS) — active-HIGH power disable, shared by U3 (pH) and U4 (EC):
  GPIO6 LOW  → isoPower enabled  → EZO-pH and EZO-EC powered normally
  GPIO6 HIGH → isoPower disabled → EZO-pH and EZO-EC de-energised

Use cases:
  - Fault recovery: pulse HIGH 100ms then LOW; wait ≥1.2s before sending I2C commands
  - Power saving: de-energise both circuits when readings are not needed (~30mA saved)

EZO-RTD (MEZZ1) has no ADM3260 and is not controlled by EZO_PDIS.

EZO-RTD (MEZZ1, no isolation):
┌──────────────────────────────────────┐
│  EZO-RTD (MEZZ1)                     │
│                                      │
│   VCC ◄──── 3.3V                     │
│   GND ◄──── GND                      │
│   SDA ◄───► I2C SDA                  │
│   SCL ◄──── I2C SCL                  │
│   PRB ◄──── BNC panel-mount          │
│                                      │
└──────────────────────────────────────┘

The ADM3260 provides both I2C signal isolation (2.5kV) and isolated DC power
via integrated isoPower — up to 150mW output. No external DC-DC converter needed.

3.3V ──► ADM3260 (U3 or U4) VCC1 ──► isoPower ──► 3.3V_ISO ──► EZO VCC/SDA/SCL
GPIO6 ──► ADM3260 PDIS (U3 and U4 tied together) — HIGH disables isoPower
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
- Float switches: JST-XH 2-pin (2.5mm pitch)
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

## 4. Temperature Sensor (1-Wire) — ⛔ NOT POPULATED

> **Design decision:** The 1-Wire DS18B20 has been removed from the build.
> Water temperature is measured by the EZO-RTD circuit (MEZZ1, I2C address 0x66).
> Ambient temperature is measured by the BME280 (I2C).
> GPIO2 is now used for ATO_VALVE (output). R30 (4.7kΩ 1-Wire pullup) is DNP.
>
> The technical documentation below is retained for reference only.

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
    GPIO7 ──────────────────────────► │ TRIG    │ (3.3V logic)
    (US_TRIG)                         │         │
    GPIO3 ◄─────────────────────────  │ ECHO    │ (3.3V logic output)
    (US_ECHO)                         └─────────┘


Signal Flow:
1. ESP32 GPIO7 sends 10µs pulse to TRIG (3.3V HIGH)
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
│ Pin 2: TRIG          │ ◄── To GPIO7 (US_TRIG)
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
#define US_TRIG_GPIO    7
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

### 5.8 Why GPIO7 and GPIO3 Were Selected

**GPIO7 (US_TRIG) - Output:*
- Can be used as output
- GPIO7 is a standard GPIO — no strapping pin concerns
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

**Both switches are mounted NC (hinge pointing DOWN).** Wiring to the PCB differs
between the two so that both GPIO signals are active-HIGH on their cutoff condition
(see section 6.3 for circuit details and section 6.5 for full mounting guide):

```
FLOAT_LOW  (GPIO0) — hole at LOW water mark:
  Float arm UP   (water ≥ LOW mark):  NC CLOSED → switch pulls to GND → GPIO0 LOW  (water OK)
  Float arm DOWN (water < LOW mark):  NC OPEN   → pull-up → GPIO0 HIGH (alarm — stop pump)
  PCB wiring: switch wire → GND terminal

FLOAT_HIGH  (GPIO1) — hole at HIGH water mark:
  Float arm UP   (water ≥ HIGH mark): NC CLOSED → switch pulls to 3.3V → GPIO1 HIGH (stop ATO)
  Float arm DOWN (water < HIGH mark): NC OPEN   → pull-down → GPIO1 LOW  (ATO OK)
  PCB wiring: switch wire → 3.3V terminal
```

> **Alternative:** Madison M8000 (1/8" NPT vertical NC, PP, 30VA) if side-wall mounting
> is not possible (e.g., opaque rigid reservoir with no accessible side). Same circuit applies.

---

### 6.3 Circuit

The two float switches use opposite pull directions so that both GPIO signals are
**active-HIGH when their cutoff condition is triggered** — consistent logic for both
software and the hardware NPN cutoff transistors (see section 6.4).

```
Float Switch - FLOW (low level alarm, GPIO0):
Pull-UP to 3.3V, switch-to-GND, NC (hinge down)

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

Float arm UP   (water at/above LOW mark): NC CLOSED → GPIO0 = LOW  (0) — water OK
Float arm DOWN (water below LOW mark):    NC OPEN   → GPIO0 = HIGH (1) — ALARM, stop pump

Float Switch - HIGH (high level cutoff, GPIO1):
Pull-DOWN to GND, switch-to-3.3V, NC (hinge down)
⚠ Reversed from FLOAT_LOW so GPIO1 is also active-HIGH on cutoff.

        3.3V
         │
        LH25 HIGH (NC, hinge down)
         │
GPIO1 ───┼──────────────────────────────────────────────────
         │
        R1
       10k (pulldown)
         │
        C1
       100nF (debounce)
         │
        ─┴─
        GND

Float arm UP   (water at/above HIGH mark): NC CLOSES to 3.3V → GPIO1 = HIGH (1) — STOP ATO
Float arm DOWN (water below HIGH mark):    NC OPEN → pull-down → GPIO1 = LOW  (0) — ATO OK
```

---

### 6.4 Hardware Cutoff via NPN Transistors

Each float switch drives a small NPN transistor that directly clamps the respective
MOSFET gate to GND when the cutoff condition fires. This is independent of firmware —
the pump and ATO valve shut down in hardware even if the MCU is hung or misbehaving.

```
FLOAT_LOW hardware cutoff (water-low → main pump off):

GPIO0 (HIGH = water low) ────── R_base ──── Base  ┐
                                4.7kΩ              │ MMBT3904 NPN
                                         Emitter ──┴── GND
                                         Collector ──────────────────────────► Q1 Gate
                                                              (also driven by GPIO10 through 100Ω)

FLOAT_HIGH hardware cutoff (water-high → ATO valve closes):

GPIO1 (HIGH = water high) ───── R_base ──── Base  ┐
                                4.7kΩ              │ MMBT3904 NPN
                                         Emitter ──┴── GND
                                         Collector ──────────────────────────► Q8 Gate
                                                              (also driven by GPIO2 through 100Ω)
```

**Operation:**
| Condition | GPIO state | NPN | MOSFET gate | Load |
|-----------|-----------|-----|-------------|------|
| Water OK / ATO OK | LOW (0) | OFF | Controlled by GPIO10/GPIO2 | Normal operation |
| Water LOW / Water HIGH | HIGH (1) | ON (saturated) | Pulled to ≈GND | OFF (hardware) |

**Component selection:**
- MMBT3904 (SOT-23): β ≥ 100, I_C(max) = 200mA, V_CE(sat) ≈ 0.2V
- Base resistor: 4.7kΩ → I_B = (3.3V − 0.7V) / 4.7kΩ = 0.55mA
- Worst-case I_C when GPIO10/GPIO7 HIGH and NPN ON: (3.3V − 0.2V) / 100Ω = 31mA
- Saturation overdrive: 0.55mA / 0.31mA = 1.8× → fully saturated ✓
- Gate clamped to ≤ 0.2V, well below VGS(th) = 1.5V of both Q1 and Q8

**Schematic note:** Two additional MMBT3904 transistors (Q9, Q10) and two 4.7kΩ
resistors are required on the PCB. The 4.7kΩ value is already present in the BOM (R30).

---

### 6.5 Normally Open vs Normally Closed — Full Explanation

A float switch contains a **reed switch** — a sealed glass capsule with two metal contacts
that close when a magnet is brought near. The float arm holds a permanent magnet that moves
closer to or farther from the reed switch as the water level changes.

**Normally Closed (NC)** — contacts CLOSED in the resting state:

```
                ╔════════════╗
                ║  Reed      ║
                ║  Switch    ║  ← magnet near = contacts CLOSED
    ┌───┤≈────╗ ║            ║
    │  float  ╚═╗  ───────── ║
    │   arm     ║  contacts  ║
    └───────────╚════════════╝

  Float UP (in water):  Magnet near reed → contacts CLOSED  → circuit CONDUCTING
  Float DOWN (in air):  Magnet away      → contacts OPEN    → circuit BROKEN
```

**Normally Open (NO)** — contacts OPEN in the resting state:

```
  Same hardware as NC — just flip the float arm orientation on the LH25.
  Float UP (in water):  Magnet near reed → contacts OPEN     → circuit BROKEN
  Float DOWN (in air):  Magnet away      → contacts CLOSED   → circuit CONDUCTING
```

For the **Flowline LH25**, NO/NC is selected by the float hinge orientation:

```
  Hinge DOWN (arm hangs down by gravity in air):
    → In air: arm DOWN, magnet away  = NC resting state = CLOSED
    → In water: arm UP, magnet near  = NC actuated    = OPEN? ← confusing!
```

Wait — the LH25 spec states it the other way. Here is the correct behaviour:

```
  LH25, Hinge DOWN = NC wiring:
    Float arm UP  (water present at switch level) → reed CLOSES → contacts CONDUCTING
    Float arm DOWN (water below switch level)     → reed OPENS  → contacts BROKEN

  LH25, Hinge UP = NO wiring:
    Float arm UP  (water present at switch level) → reed OPENS  → contacts BROKEN
    Float arm DOWN (water below switch level)     → reed CLOSES → contacts CONDUCTING
```

**OPNhydro uses NC (hinge DOWN) for both switches.**
When water rises to the switch, the float arm lifts → reed closes → circuit makes.
When water drops below the switch, the float arm falls → reed opens → circuit breaks.

---

### 6.6 Mounting the Float Switches

**Tools required:**
- Step drill bit or hole saw: 18mm (23/32") for 1/2" NPT tap drill
- 1/2" NPT tap + tap handle
- Adjustable wrench or pipe wrench
- PTFE thread tape

**Step 1 — Determine water levels:**
```
       ┌──────────────────────────┐
       │                          │   ← tank top / lid
       │       FLOAT_HIGH         │ ← HIGH mark: ATO stops here
       │          ●               │   (e.g., 25mm below brim)
       │                          │
       │  [operating range]       │
       │                          │
       │       FLOAT_LOW          │ ← LOW mark: pump stops here
       │          ●               │   (e.g., 50mm above bottom)
       │                          │
       └──────────────────────────┘
```

- **FLOAT_LOW (low mark):** Set high enough that the pump is never run dry.
  Typically 50–75mm above the reservoir bottom.
- **FLOAT_HIGH (high mark):** Set low enough to prevent overflow.
  Typically 25–50mm below the top of the reservoir.
- The vertical distance between them defines the ATO working range.

**Step 2 — Drill the side-wall holes:**
1. Mark the two hole positions on the reservoir side wall.
2. Use an 18mm (23/32") step bit or hole saw to drill each hole.
3. Tap each hole to 1/2" NPT using the NPT tap.
   - Apply cutting oil if drilling into HDPE or polypropylene.
   - Use a slow, steady hand — plastic cracks if rushed.
4. Deburr the inside edge with a countersink or knife.

**Step 3 — Install the switches:**
1. Wrap 3–4 turns of PTFE tape on the LH25 NPT threads (clockwise wrap).
2. Thread into the hole by hand until snug.
3. Orient the float hinge **pointing DOWN** (NC mode) — the hinge end is marked on the body.
4. Use a wrench to tighten 1–2 additional turns past hand-tight. Do not overtighten.
5. The float arm should point **toward the inside of the reservoir** and swing freely.

```
   Outside of reservoir wall:     Inside of reservoir:

     ┌────────────────┐             ┌─────────────────┐
     │   NPT threads  │             │                 │
     │ LLLLL LH25 body│═════════════│  ←arm swings    │
     │  (hinge DOWN)  │             │   freely here   │
     └────────────────┘             └─────────────────┘
           ↑
      Wire exits here
      (2', 22 AWG,
       2-conductor)
```

**Step 4 — Route and connect the wires:**

Both switches come with 2' (61cm) bare wire leads. Terminate each wire with a
JST-XH 2-pin crimp or strip and clamp into a 2-pin screw terminal on the PCB.

| Switch | Wire to PCB pin 1 | Wire to PCB pin 2 | Notes |
|--------|-------------------|-------------------|-------|
| FLOAT_LOW (GPIO0) | GND | GND | Both wires to GND — polarity doesn't matter for dry reed |
| FLOAT_HIGH (GPIO1) | 3.3V | 3.3V | Both wires to 3.3V |

Wait — a reed switch is a 2-terminal device with no polarity. The PCB has a pull-up or
pull-down resistor and the switch creates the signal. The actual connection is:

```
FLOAT_LOW (GPIO0):
  PCB header Pin 1: → GPIO0 signal node (already has pull-up to 3.3V on PCB)
  PCB header Pin 2: → GND
  Wire one switch lead to each pin. No polarity.

FLOAT_HIGH (GPIO1):
  PCB header Pin 1: → GPIO1 signal node (already has pull-down to GND on PCB)
  PCB header Pin 2: → 3.3V
  Wire one switch lead to each pin. No polarity.
```

**Step 5 — Test before filling:**
1. With the reservoir empty, both float arms should hang DOWN.
   - GPIO0 should read HIGH (water low alarm, expected)
   - GPIO1 should read LOW (ATO OK, expected)
2. Lift FLOAT_LOW arm by hand — GPIO0 should go LOW (arm up = water OK).
3. Lift FLOAT_HIGH arm by hand — GPIO1 should go HIGH (arm up = water at HIGH mark → ATO stops).

---

## 7. Pump Driver Circuits

> ⚠️ **PENDING SELECTION:** Main circulation pump — **24V DC required** (system rail is 24V).
> The AUBIG DC40-1250 (12V) is no longer suitable.
>
> **Requirements for replacement:**
> - Voltage: **24V DC**
> - Flow: ≥500 L/H at operating head
> - Head: ≥4m
> - Brushless preferred (reliability)
> - PWM-capable preferred for variable flow via Q1 MOSFET gate
> - Barbed fittings preferred

All pumps and the ATO valve use the same 24V rail and identical driver circuits.

### 7.1 24V Main Pump Driver

```
                                    24V
                                     │
                        ┌────────────┼────┬──── 24V rail
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
        ├────────────────────────────────── Gate (Q1)
        │                                       │
GPIO10 ─┘                                      R1
                                              10kΩ (pull-down)
                                               │
                                              ─┴─
                                              GND

Hardware cutoff — FLOAT_LOW (water-low) overrides GPIO10:

GPIO0 ──── R_base (4.7kΩ) ──── Base ┐
                                     │ Q9: MMBT3904 NPN
                          Emitter ───┴─── GND
                          Collector ─────────────────────────► Gate (Q1)

When GPIO0 HIGH (water low): Q9 saturates → Gate clamped to ≤0.2V → Q1 OFF (hardware)
When GPIO0 LOW  (water OK):  Q9 off      → Gate driven by GPIO10 normally

C2: 100nF / 50V ceramic (X7R, 0805)
- Local bypass capacitor for switching transients
- Place within 5mm of Q1 DRAIN pin
- Reduces high-frequency noise on 24V rail

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
```

**Main Pump Specifications:**

Recommended 24V DC submersible pumps for hydroponic circulation: (**Selection TBD — 24V equivalents required**)

| Parameter | Specification | Notes |
|-----------|---------------|-------|
| **Voltage** | **24V DC** | Matches system power rail |
| **Current** | 0.5-0.75A typical at 24V | Within IRLR2905 capacity (42A) |
| **Power** | 12-18W maximum | Current × voltage |
| **Flow Rate** | 600-1000 L/H | 158-264 GPH |
| **Head Height** | 2-3 meters | 6.5-10 feet max lift |
| **Type** | Submersible | Water-cooled, silent operation |
| **Material** | Food-safe plastic or SS | Aquarium/hydroponics rated |
| **Duty Cycle** | Continuous | 24/7 operation capable |
| **Connection** | Wire leads or barrel jack | See connector specs below |

**Recommended Pump Models:**

**Option 1: 24V Brushless Submersible Pump** ⚠️ **TBD — 24V equivalent required**

**Electrical Specifications:**
- Voltage: **24V DC** (AUBIG DC40-1250 was 12V and is no longer suitable)
- Current: ~0.6-0.75A @ 24V (equivalent power ~14-18W)
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
- ⚠️ **Voltage Safety**: 24V DC — low-voltage shock risk is minimal but use appropriate wire ratings
- ✅ **Soft Start**: Brushless controller reduces inrush current

**Cost & Availability:**
- Price: $12-18 USD
- Sources: Amazon, eBay, AliExpress
- Part Numbers: DC40-1250 (wire leads), DC40-1250 (NPT threads)

**Hydroponic System Suitability:**

| System Type | Reservoir | Flow Rate Needed | AUBIG DC40-1250 | Rating |
|-------------|-----------|------------------|-----------------|--------|
| NFT (Nutrient Film) | 20-40 gal | 400-600 L/H | 500-510 L/H | ✅ **Excellent** |
| DWC (Deep Water) | 20-30 gal | 600-800 L/H | 500-510 L/H | ✅ **Good** |
| Ebb & Flow | 20-30 gal | 600-800 L/H | 500-510 L/H | ✅ **Good** |
| Drip System | Any | 400-600 L/H | 500-510 L/H | ✅ **Excellent** |
| Large DWC | 50+ gal | 1000+ L/H | 500-510 L/H | ⚠️ **Marginal** |

**PWM Speed Control Implementation:**

The main pump supports PWM speed control via the 24V power input. The ESP32-S3 can generate PWM on GPIO10 to modulate the MOSFET gate, providing variable pump speed:

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
24V Power Supply Specification:
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
3. Use 1/2" ID vinyl or silicone tubing on barbed fittings; secure with hose clamps
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
- ⚠️ Sensitive to power quality (needs stable 24V, low ripple)
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
- 24V trace width: 50 mil (1.27mm) minimum for main pump
- Keep Q1 and screw terminal close to minimize trace resistance
- Add test points for 24V_SWITCHED and GND for diagnostics
- **C2 (100nF bypass)**: Place within 5mm of Q1 DRAIN pin for best performance

### 7.2 24V Dosing Pump Drivers — TMC2209 Stepper (×3)

> **Design decision — Stepper over DC motor, and Nutrient A/B on separate channels:**
> DC peristaltic pumps require periodic flow-rate calibration; stepper-driven pumps dose by step count × pump displacement, which is stable between calibrations. TMC2209 StealthChop2 provides near-silent operation.
Nutrient A and B use separate STEP lines (GPIO15, GPIO19) but share DIR (GPIO18) — they always dose in the same direction. 
Cost delta vs combined channel: ~$3 (one TMC2209). See ARCHITECTURE.md §2 and §8.

Three TMC2209 stepper drivers (QFN-28) each drive one Kamoer KAS SF-12V bipolar stepper peristaltic pump. All drivers operate in **UART mode** via GPIO21/22 (ESP32-C6 UART1).
StealthChop2 is active by default at the low step rates used for dosing.

**TMC2209 UART Configuration:**
- PDN_UART: 100Ω series resistor to shared UART bus. GPIO22 TX → bus via 1kΩ; GPIO21 RX → bus direct
- MS1/MS2: set UART address per driver (see address table below)
- EN: tied to GND — drivers permanently enabled; standstill current eliminated via `IHOLD=0`
- DIR: hardwired to 3.3V — peristaltic pumps never need reversal
- SPREAD: GND → StealthChop2 mode (silent)
- RSENSE: 220mΩ — sets full-scale current reference with VREF
- VREF: resistor divider from 3.3V → ~0.58V → full-scale ~1.32A; IRUN register scales to 0.75A
- STDBY (pin 20): HIGH = standby (internal regulator off, all UART registers reset to defaults);
  LOW = normal operation. **Tied to GND** — OPNhydro runs continuously; IHOLD=0 handles
  standstill power saving without the register-reset complication of STDBY.
  ⚠ If STDBY is ever asserted, all UART registers (IRUN, IHOLD, IHOLDDELAY, TPWMTHRS…)
  must be re-written by firmware after wake-up. EN must be HIGH and VREF driven to 0V
  before asserting STDBY.
- DIAG: active-HIGH output; asserts when StallGuard4 detects a stall or a driver error; see below
- INDEX: pulse output; see below

**UART address wiring (MS1/MS2 per driver):**

| Driver | MS1 | MS2 | Address |
|--------|-----|-----|---------|
| U5 pH Down | GND | GND | 0 |
| U6 Nut A | 3.3V | GND | 1 |
| U7 Nut B | GND | 3.3V | 2 |

**UART bus wiring:**

```
ESP32 GPIO22 (TX) ──── 1kΩ ──┐
                              ├── shared bus node
ESP32 GPIO21 (RX) ────────────┘        │
                                  100Ω ├──── U5 PDN_UART
                                  100Ω ├──── U6 PDN_UART
                                  100Ω └──── U7 PDN_UART
```

> **⚠ Critical Wiring Detail — The UART Resistor (per TMC2209 datasheet §4.3)**
> Connect ESP32 TX to the TMC2209 PDN_UART bus through a **1kΩ series resistor**.
> Connect ESP32 RX **directly** to the same PDN_UART bus node — no resistor on RX.
> The 1kΩ goes on the **TX line**, not the RX line.
> Source: [TMC2209 Datasheet Rev 1.09, §4.3 UART Signals](https://www.analog.com/media/en/technical-documentation/data-sheets/tmc2209_datasheet_rev1.09.pdf)

**1kΩ on GPIO22 TX:**
PDN_UART is an open-drain bidirectional pin. When the ESP32 TX drives HIGH to send a command, and the TMC2209's open-drain output momentarily pulls the bus LOW to begin its response (a brief overlap before software tri-states TX), a low-impedance conflict occurs between TX driving HIGH and the open-drain pulling LOW. The 1kΩ on TX limits the fault current during this window to (3.3V / 1kΩ) = 3.3 mA — safe for both the ESP32 output driver and the TMC2209 PDN_UART. RX is connected directly because it is a high-impedance input that only monitors the bus voltage; no protection is needed.

Configure ESP32-C6 UART1 in **half-duplex / single-wire mode** so TX is tri-stated (high-impedance) during the receive window. The TMC2209 then pulls the bus LOW open-drain to transmit its response, with no conflict from TX.

**100Ω on each PDN_UART pin:**
All three drivers share the same bus node. When one driver responds, its open-drain output pulls that driver's PDN_UART pin LOW. Without isolation, this LOW would also be seen at the PDN_UART pin of the other two non-responding drivers, which could
corrupt their internal UART state (treating the bus activity as addressed to them). 
The 100Ω series resistor on each PDN_UART pin creates a small voltage drop that decouples each driver's input from the bus during contention, and limits the current path between drivers if two open-drain outputs are momentarily both active.

**Circuit (same topology for U5/U6/U7 — MS1/MS2 differ per address table):**

```
                24V (VM)
                  │
           ┌───┬──┴──────┐
           │   │         │
        100µF 100nF      │  ← 100µF bulk + 100nF local bypass per driver
          ─┴─ ─┴─     VM │
              ┌──────────┴───────────┐
 3.3V ───────►│ VIO                  │
 GND ────────►│ GND                  │
              │                      │
 STEP_xxx ───►│ STEP          OA1 ───┼──► coil A+   ← U5: GPIO11, U6: GPIO15, U7: GPIO19
 3.3V ───────►│ DIR           OA2 ───┼──► coil A-
  GND ───────►│ EN            OB1 ───┼──► coil B+
              │               OB2 ───┼──► coil B-
UART bus─100Ω►│ PDN_UART             │   ← bus: GPIO22─1kΩ─┤; GPIO21 direct; 100Ω isolates each driver
  MS1* ──────►│ MS1           BRA ───┼──── 220mΩ ──── GND   ← RSENSE: 1%, 1/4W 0805
  MS2* ──────►│ MS2           BRB ───┼──── 220mΩ ──── GND   ← 1/8W insufficient at full scale
  GND ───────►│ SPREAD               │
  GND ───────►│ STDBY                │   ← tied LOW; STDBY resets all UART regs if pulsed
              │                      │
see below  ──►│ VREF                 │   ← ~0.58V, full-scale ~1.32A
              │      TMC2209         │
              └──────────────────────┘
  * MS1/MS2 per address table: U5=GND/GND, U6=3.3V/GND, U7=GND/3.3V
```

**GPIO Assignments:**
```
GPIO11 ──► STEP_PH_DN  (U5 pH Down driver STEP)
GPIO15 ──► STEP_NUT_A  (U6 Nutrient A driver STEP)
GPIO19 ──► STEP_NUT_B  (U7 Nutrient B driver STEP)
GPIO21 ──► TMC2209_UART_RX  (UART1 RX — shared bus listen, direct connection)
GPIO22 ──► TMC2209_UART_TX  (UART1 TX — shared bus drive, 1kΩ series to bus)
GPIO20 ──  (available — STEPPER_EN not needed; EN tied to GND)
```

**DIR hardwired to 3.3V** on all three drivers. Peristaltic pumps are self-sealing — the rollers pinch the tube closed when stopped, so backflow cannot occur and direction reversal is never needed. If a pump runs backwards on first install, swap the coil A wires (OA1 ↔ OA2) on the connector.

**SENSE resistors (R<sub>sa</sub> and R<sub>sb</sub>):**
BRA and BRB are the low-side current sense points of the H-bridge for coil A and coil B respectively. A shunt resistor connects each pin to GND. The TMC2209 measures the voltage drop across this resistor to determine actual coil current, then adjusts its PWM chopper duty cycle to regulate current to the IRUN/IHOLD target.

> All currents in this section are RMS currents. 

Following the TMC2209 datasheet Ch. 8 recommendation for the A200SX 1.7A motor.
> **R<sub>s</sub> = 120mΩ**

Based on the formula from chapter 9 of the datasheet:
> **I<sub>max</sub> = V<sub>fs</sub> / (R<sub>s</sub>+20mΩ) * 1 / √2**, where V<sub>fs</sub> is the full-scale voltage as determined by the `vsense control bit`. Default is 325mV.

So with a R<sub>s</sub> = 120mΩ and V<sub>fs</sub> = 325mV
> **I<sub>max</sub>** = 325mV / (120mΩ+20mΩ) * 1 / √2 = **1.77A**,

Set a hard limit using the V<sub>REF</sub> input of the TMC2209. This linearly scales the maximum current. To cap the operating range in hardware at 90%, apply a 
> **V<sub>REF</sub>** = (0.9 * 1.7A) / 1.77A * 2.5V = **2.161V**

Too create this voltage, use the 3.3V rail with a R<sub>H</sub> and R<sub>L</sub> voltage divider. Taking into account a R<sub>VREF</sub>=240MΩ, the required resistors follow as:
> **R<sub>H</sub> = 3.92kΩ**
> **R<sub>L</sub> = 7.68kΩ** (both E96 Series, 1%)

At 90% of I<sub>max</sub>, the sense resistor R<sub>s</sub> will dissipate:
>  **P<sub>d</sub> = I<sub>rms</sub><sup>2</sup> × R<sub>s</sub>** = (0.9 * 1.7A)<sup>2</sup> * 0.12Ω = 0.28W ⇒ choose **1/2W**

With the current capped at 90% of 1.7A, we lower the current futher with the current scale specified by the `IHOLD_IRUN` register:
> I<sub>rms</sub> = V<sub>REF</sub>/2.5V * (CS + 1)/32 * V<sub>fs</sub> / (R<sub>s</sub>+20mΩ) * 1 / sqrt(2), where V<sub>fs</sub> is the full-scale voltage as determined by the `vsense control bit`. Default is 325mV.

Try an initial **70% or 80%** operating range by setting the **CS to 24 or 27**. Increase to 85–90% only if stalling occurs on aged tubing.

CS value | Current limit| Target range
---------|---------|-------------
24       | 1.19A   | 70%
25       | 1.24A   | 73%
26       | 1.29A   | 76%
27       | 1.34A   | 79%
28       | 1.43A   | 81%
29       | 1.39A   | 84%
30       | 1.48A   | 87%
31       | 1.53A   | 90%

The sense voltage is also used by StealthChop2 (current-mode PWM feedback) and StallGuard4 (coil current deviation from expected pattern signals a stall).

**Key UART registers to configure at startup:**

| Register | Value | Purpose |
|----------|-------|---------|
| `IHOLD` | 0 | Zero standstill current (EN tied to GND — this is essential) |
| `IRUN` | 18 | Run current ≈ 0.75A (18/31 × full-scale with RSENSE=220mΩ, VREF=0.58V) |
| `IHOLDDELAY` | 6 | Steps between IRUN→IHOLD transition after last STEP pulse |
| `TPWMTHRS` | 0 | StealthChop2 active at all speeds |
| `SENDDELAY` | ≥2 | **Required for multi-driver bus.** Reply delay before TMC2209 begins its UART response. Default (0) can cause a non-addressed chip to detect a transmission error when a different chip responds. Set to 2 or higher on all drivers. See note below. |

> **⚠ Multi-driver SENDDELAY note**
> When multiple TMC2209 chips share the same serial line with different addresses, the
> `SENDDELAY` register must be increased from its default value, otherwise a non-addressed
> chip may detect a transmission error when it sees the response from the addressed chip.
> Set `SENDDELAY` ≥ 2 on every driver at firmware init.
> Source: [janelia-arduino/TMC2209 library README](https://github.com/janelia-arduino/TMC2209)

**DIAG pin:**
Active-HIGH open-drain output. Asserts (goes HIGH) when StallGuard4 detects a motor
stall or when a driver error occurs (overtemperature, short circuit). In UART mode,
stall detection is preferred via the `DRV_STATUS` register (read `SG_RESULT` field)
rather than the DIAG pin — this avoids spending a GPIO and is more informative
(gives a numeric stall load value, not just a binary flag).

PCB connection options:
- **v1 (recommended):** leave DIAG floating — no GPIO required; poll `DRV_STATUS` via
  UART instead. Place a DNP 10kΩ pullup footprint to 3.3V for future use.
- **v2 (optional):** connect each DIAG to a free GPIO (GPIO18, GPIO20, GPIO23) via
  10kΩ pullup; allows interrupt-driven stall detection without polling.

**INDEX pin:**
Pulse output — by default emits one pulse per electrical period (every 4 full steps at
1× microstepping). Can be reconfigured via UART `IOIN` register to signal other events
(e.g. first microstep position, stepper index).

For dosing pumps, step count is controlled directly by the ESP32 (counted steps = known
volume), so INDEX adds no value in normal operation. **Leave INDEX floating** (high-Z
output, no harm). Place a DNP 1kΩ series + test point footprint for debugging if needed.

**Standalone fallback (no firmware UART):** replace each 100Ω PDN_UART series resistor
with 100kΩ to 3.3V; set MS1/MS2 both to 3.3V (1/16 microstep, addr unused); connect
EN to GPIO20. Current then set by VREF divider only. StealthChop2 remains active.

**VM Bulk Capacitance:**
Place at least one **100µF electrolytic capacitor** (≥35V, low-ESR) close to each
driver's VM pin. The TMC2209 chopper switches coil current rapidly — each switching
event draws a brief spike from the VM supply. Without local bulk capacitance these
spikes appear as voltage transients on the VM rail, which can corrupt UART communication
(if the supply dips below the VIO logic threshold briefly) and degrade StallGuard4
accuracy (coil current measurement depends on a stable VM). A 100nF ceramic (already
in the circuit) handles high-frequency transients; the 100µF electrolytic handles the
lower-frequency, higher-energy spikes from step-rate switching. Place the 100µF within
5mm of the VM pin, with a short direct trace to GND.

**Firmware — TMCStepper Library:**

Use **[TMCStepper](https://github.com/teemuatlut/TMCStepper)** for all TMC2209 driver
configuration and status monitoring. It provides full UART register access: write
IRUN=18, IHOLD=0, IHOLDDELAY=6, TPWMTHRS=0 at startup; read DRV_STATUS.SG_RESULT and
temperature flags during operation. No alternative library provides this capability.

**Firmware — STEP Pulse Generation (RMT / LEDC / ISR Timer):**

STEP pulses must be generated by hardware peripherals, not software loops.

If the ESP32 is busy with a Wi-Fi request, SSL/TLS handshake, or MQTT reconnect, a
software-timed pulse loop can stall for tens of milliseconds. A single missed or late
pulse causes the stepper to lose a step — and since dosing accuracy is derived from
step count × tube displacement constant, one lost step per dose accumulates into
measurable calibration error over time.

The ESP32-C6 provides three suitable hardware options:

**Option 1 — RMT (Remote Control Transceiver) — recommended:**
The RMT peripheral generates arbitrary pulse sequences from a preloaded buffer with
nanosecond resolution, independent of the CPU. Configure it to output N pulses at the
target step frequency, then trigger it once per dose. When the burst completes it fires
a done interrupt; the CPU core is free throughout.

```
// Pseudocode — ESP-IDF RMT approach
rmt_config_t cfg = { .gpio_num = STEP_PH_DN, .clk_src = RMT_CLK_SRC_DEFAULT };
rmt_channel_handle_t ch;
rmt_new_tx_channel(&cfg, &ch);
// preload N symbols: 50% duty, period = 1/step_freq
rmt_transmit(ch, encoder, symbols, n_steps, NULL);
// CPU is free; RMT fires done callback when burst finishes
```

Supports up to 4 independent TX channels on ESP32-C6 → one per STEP pin (GPIO11,
GPIO15, GPIO19) with one spare.

**Option 2 — LEDC (LED PWM Controller):**
LEDC generates continuous PWM at hardware level. For dosing, drive LEDC at the target
step frequency and disable it after counting the required pulses via a GPIO interrupt
on the STEP line, or use a one-shot approach: enable LEDC, start a hardware timer for
N/freq seconds, disable LEDC in the timer callback. Less precise step count than RMT
(off-by-one at stop edge possible) but simpler to configure.

**Option 3 — ESP32_ISR_Stepper / ESP32TimerInterrupt:**
The [ESP32TimerInterrupt](https://github.com/khoih-prog/ESP32TimerInterrupt) library
configures hardware timer ISRs that run independently of the main loop and Wi-Fi
stack. Use with `ESP32_ISR_Timer` in non-blocking mode: the ISR toggles the STEP GPIO
at the target rate and decrements a step counter; when it reaches zero the ISR
disables itself. All three pump channels require separate hardware timer instances
(ESP32-C6 has 2 hardware timer groups × 2 timers each = 4 timers available).

**Recommendation for OPNhydro:**
Use **RMT** as the primary approach. It is the most deterministic, requires no ISR
management, and the burst-complete callback integrates cleanly with an ESPHome custom
component or FreeRTOS task. Use `ESP32TimerInterrupt` as a fallback if the RMT
peripheral is needed for other functions (e.g. WS2812B LED strip).

**Dosing Pump — Kamoer KAS SF-12V:**

| Parameter | Specification |
|-----------|---------------|
| Voltage | 24V VM (TMC2209 regulated) |
| Current | 0.75A |
| Flow rate | ~11.5–71.5 mL/min (3-rotor, speed-dependent) |
| Tubing | 3mm ID × 5mm OD, silicone or BPT |
| Motor | Bipolar stepper (4-wire) |
| Motor cable connector | JST PHR-6 (6-pin PH female, 2.0mm pitch) |
| Drive board control connector | JST B4B-XH-A (4-pin XH male, 2.5mm) — on bundled drive board only |
| Source | [Kamoer KAS SF-12V datasheet](https://www.kamoer.com/us/previewPdf/index.html?type=1&docId=8583&xxsToken=55a775c80a10a02b4f4b7ec1185bf381&id=9005) |

Order without the bundled drive board — TMC2209 replaces it.

**Connector overview:**
The pump motor cable terminates in a **JST PHR-6** (6-pin PH 2.0mm female housing). The
bundled drive board (not used) has a **JST B4B-XH-A** (4-pin XH 2.5mm, for STEP/DIR/EN/GND).
([Kamoer KAS SF-12V datasheet](https://www.kamoer.com/us/previewPdf/index.html?type=1&docId=8583&xxsToken=55a775c80a10a02b4f4b7ec1185bf381&id=9005))

The 6-pin PHR-6 carries motor power and coil wires together (pinout from Kamoer datasheet):

```
PHR-6 Pin Assignment (verify against datasheet before assembly):
┌─────┬──────────────────────────────────────────────────────┐
│ Pin │ Signal         │ PCB connection                      │
├─────┼────────────────┼─────────────────────────────────────┤
│  1  │ VCC (24V VM)   │ 24V rail (motor power)              │
│  2  │ GND            │ GND                                 │
│  3  │ Coil A+  (OA1) │ TMC2209 OA1                         │
│  4  │ Coil A−  (OA2) │ TMC2209 OA2                         │
│  5  │ Coil B+  (OB1) │ TMC2209 OB1                         │
│  6  │ Coil B−  (OB2) │ TMC2209 OB2                         │
└─────┴────────────────┴─────────────────────────────────────┘
⚠ Pin order and VCC/GND position must be verified from the Kamoer KAS SF-12V datasheet
  before PCB layout. Coil swap (A↔B or polarity) only affects rotation direction; the
  TMC2209 handles both. VCC/GND mis-wiring to OA/OB would damage the driver.
```

**Dosing Pump Connector (×3, PCB side):**

```
JST S6B-PH-K-S (6-position PH male header, 2.0mm pitch, right-angle TH, PCB mount) ×3
- Mates with: JST PHR-6 housing on pump motor cable
- Pitch: 2.0mm
- 6 pins: VCC, GND, coil A+, coil A−, coil B+, coil B−
- Silkscreen label: "pH DN", "NUT A", "NUT B"
- Right-angle orientation: cable exits horizontally toward board edge — preferred for
  enclosure builds where cables route sideways through cable glands
- Alternative: B6B-PH-K-S (vertical TH) if cables must exit upward
```

### 7.3 ATO Solenoid Valve Driver

```
Same circuit topology as dosing pumps, using AO3400A MOSFET.
Connected to 24V rail.
Uses normally-closed (NC) solenoid valve for fail-safe operation.

                                    24V
                                     │
                        ┌────────────┤
                        │            │
                       D1         VALVE+
                   (1N5819)         │
                        │         VALVE
                        │        (NC, 500mA)
               ┌────────┴───────┐   │
               │     DRAIN      │   │
        ┌──────┤  Q8            ├───┴── VALVE-
        │      │  AO3400A       │
        │      │  (SOT-23)      │
        │      └───────┬────────┘
        │           SOURCE
        │              │
       R2             ─┴─
      100Ω            GND
        │
        ├────────────────────────────────── Gate (Q8)
        │                                       │
GPIO2 ──┘                                      R1
                                              10kΩ (pull-down)
                                               │
                                              ─┴─
                                              GND

Hardware cutoff — FLOAT_HIGH (water-high) overrides GPIO7:

GPIO1 ──── R_base (4.7kΩ) ──── Base ┐
                                     │ Q10: MMBT3904 NPN
                          Emitter ───┴─── GND
                          Collector ─────────────────────────► Gate (Q8)

When GPIO1 HIGH (water high): Q10 saturates → Gate clamped to ≤0.2V → Q8 OFF → valve closes (hardware)
When GPIO1 LOW  (water OK):   Q10 off      → Gate driven by GPIO2 normally
```

Q8: AO3400A (Logic-level N-MOSFET, SOT-23)
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
| **Voltage** | 24V DC | Matches system power rail |
| **Current** | 300-500mA typical | Within AO3400A capacity (5.8A) |
| **Power** | 4-6W | Coil power consumption |
| **Pressure** | 0-0.8 MPa (0-116 PSI) | Typical municipal water pressure |
| **Port Size** | 1/4" to 1/2" | NPT thread or hose barb |
| **Material** | Brass body, EPDM/NBR seal | Food-safe, corrosion resistant |
| **Orifice** | 2-10mm | Determines flow rate |
| **Response** | 50-100ms typical | Fast open/close |

**Recommended Solenoid Valve Models:**

**✅ Recommended: DIGITEN DC 24V 1/4" NC Quick-Connect** *(or equivalent 24V NC valve)*
- Model: DIGITEN K170403
- Port: 1/4" quick-connect (fits standard 1/4" OD tubing directly — no NPT adapter needed)
- Type: Direct-acting, zero-pressure rated (works on gravity-fed top-off tanks)
- Current: ~200mA @ 24V DC (4.8W)
- Material: Food-grade plastic body, NBR seal
- Pressure: 0–0.5 MPa (0–72 PSI)
- Cost: ~$10
- Best for: RO/clean water ATO on gravity or mains supply

> **Why not the 2V025-08 (ANGGREK/AirTAC)?** The 2V025 is a pneumatic valve (designed for air/gas) with an anodized aluminum body. It functions for clean water short-term but is not rated for continuous liquid service. Brass or food-grade plastic bodies are more appropriate for water ATO.

**Alternative: U.S. Solid 1/4" NC Nylon 24V** (~$15–20)
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
Phoenix Contact MC 1.5/2-ST-3.5 (2-position pluggable screw terminal)
- Pitch: 3.5mm — same family as dosing pump connectors
- PCB header: MC 1.5/2-G-3.5
- Wire size: 24-18 AWG (for 250mA @ 24V)
- Label silkscreen: "ATO VALVE" or "WATER IN"

Pin Assignment:
Pin 1: 24V_VALVE (switched via Q8)
Pin 2: GND

Valve Side Connection:
- Most solenoid valves have 2-wire leads (polarity doesn't matter for DC)
- Some have wire connectors (DIN 43650A common)
- Strip and insert into screw terminal, or add mating connector
```

**Safety Notes:**
- ✅ NC valve ensures no water flow if controller loses power
- ✅ Float switch (GPIO1 - FLOAT_HIGH) provides hardware backup cutoff
- ✅ Float switch (GPIO0 - FLOAT_LOW) provides low-level alarm
- ✅ Software timeout prevents flooding if level sensor fails
- ✅ Recommend inline manual shutoff valve for maintenance
- ✅ Consider water leak sensor near reservoir for additional protection

**Valve Installation:**
1. Install valve inline on water supply line (before reservoir)
2. Arrow on valve body indicates flow direction
3. Mount valve with coil vertical (prevents water ingress)
4. Use thread sealant (Teflon tape or pipe dope) on NPT threads
5. Test valve operation before connecting to reservoir

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
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403-24V, 1/4" QC, 24V ~200mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Main Pump Connector** | 1 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $0.50 | 5.08mm pitch — incompatible with dosing |
| **Dosing + ATO Connectors** | 5 | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | $0.40 | $2 | 3.5mm pitch — incompatible with main pump |
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
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403-24V, 1/4" QC, 24V ~200mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Main Pump Connector** | 1 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $0.50 | 5.08mm pitch — incompatible with dosing |
| **Dosing + ATO Connectors** | 5 | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | $0.40 | $2 | 3.5mm pitch — incompatible with main pump |
| | | | | **Subtotal:** | **$70** | Minimum viable, lower reliability |

**Note:** Generic pumps save $40-60 but may require more frequent tubing replacement and have higher failure rates.

**Professional/Commercial Configuration (Kamoer KDS Stepper Pumps):**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Brushless | AUBIG DC40-1250, 510L/H, 12V 1.2A | $12-18 | $15 | ✅ PWM capable, proven reliable |
| **Dosing Pumps (×4)** | 4 | Peristaltic | Kamoer KDS-FE-2-S17B | $30-50 | $160 | Stepper motor, ±1% accuracy |
| **ATO Solenoid Valve** | 1 | NC Solenoid | U.S. Solid 1/4" NC Brass/Viton, 24V ~0.6A | $20-30 | $25 | IP65, direct-acting — note: 14W coil, update power budget |
| **Main Pump Connector** | 1 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $0.50 | 5.08mm pitch — incompatible with dosing |
| **Dosing + ATO Connectors** | 5 | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | $0.40 | $2 | 3.5mm pitch — incompatible with main pump |
| **24V Power Supply** | 1 | Regulated | Mean Well LRS-150-24 (50W, 4.2A) | $15-20 | $18 | Low ripple for brushless motor |
| | | | | **Subtotal:** | **$221** | Professional/commercial grade |

**For Large Systems (50+ gal DWC/Ebb & Flow):**

| Component | Qty | Type | Specifications | Cost (ea) | Total | Notes |
|-----------|-----|------|----------------|-----------|-------|-------|
| **Main Circulation Pump** | 1 | Submersible | Generic 800L/H, 12V 1.5A | $15-25 | $20 | Higher flow, no PWM |
| OR: **Dual AUBIG Pumps** | 2 | Brushless | AUBIG DC40-1250 (parallel) | $12-18 | $30 | 1000L/H total, redundant |
| **Dosing Pumps (×4)** | 4 | Peristaltic | Generic 50-100mL/min | $8-15 | $48 | Budget peristaltic |
| **ATO Solenoid Valve** | 1 | NC Solenoid | DIGITEN K170403-24V, 1/4" QC, 24V ~200mA, direct-acting | $8-12 | $10 | ✅ Food-grade, zero-pressure rated |
| **Main Pump Connector** | 1 | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | $0.50 | $0.50 | 5.08mm pitch — incompatible with dosing |
| **Dosing + ATO Connectors** | 5 | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | $0.40 | $2 | 3.5mm pitch — incompatible with main pump |
| | | | | **Subtotal:** | **$83-113** | Budget, higher flow rate |

**Connector Summary:**

| Location | Connector | Part Number | Pitch | Pins | Purpose |
|----------|-----------|-------------|-------|------|---------|
| J? (Main Pump) | Screw Terminal | Phoenix MSTB 2.5/2-ST-5.08 | **5.08mm** | 2 | 24V switched + GND |
| J? (pH Up) | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | 3.5mm | 2 | 24V switched + GND |
| J? (pH Down) | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | 3.5mm | 2 | 24V switched + GND |
| J? (Nutrient A) | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | 3.5mm | 2 | 24V switched + GND |
| J? (Nutrient B) | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | 3.5mm | 2 | 24V switched + GND |
| J? (ATO Valve) | Screw Terminal | Phoenix MC 1.5/2-ST-3.5 | 3.5mm | 2 | 24V switched + GND |

> **Misconnection prevention:** The 5.08mm main pump plug physically cannot be inserted
> into a 3.5mm dosing pump header, and vice versa. No silkscreen label required for safety,
> though labels are still recommended for ease of installation.

**Wiring Specifications:**

- **Wire gauge:** 22-18 AWG for dosing pumps and valve (300-500mA)
- **Wire gauge:** 18 AWG for main pump AUBIG DC40-1250 (1.2A, <1% drop @ 3ft)
- **Wire type:** Stranded copper, 300V rated minimum
- **Insulation:** PVC or silicone (silicone preferred for flexibility)
- **Color code:** Red = +24V switched, Black = GND
- **Recommended:** Use ferrule crimps for screw terminal connections (prevents strand fraying)
- **Critical:** For AUBIG pump, keep wire runs short (<3ft) and use quality connectors to minimize voltage drop

**Total System Power Budget (24V rail):**

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

**24V Power Supply Recommendation:**

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
- **Mean Well LRS-150-24** (50W, 4.2A) - $15-20, low ripple, reliable
- **Mean Well RS-75-12** (75W, 6A) - $20-30, DIN rail mount option
- **TDK-Lambda LS50-12** (50W, 4.2A) - $25-35, medical grade, ultra-low ripple
- **Generic 12V 5A "switching adapter"** - $10-15, acceptable if low ripple verified

**Power Supply Notes:**
1. ⚠️ **Avoid cheap "24V" adapters** - high ripple can cause AUBIG pump motor jitter/noise
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

## 10. PCB Layout Guidelines

### 10.1 Layer Stack (2-layer)
- Top: Signal + Power
- Bottom: Ground plane (solid)

### 10.2 Critical Routing
1. Keep power traces wide (1mm min for logic, 2mm+ for pump circuits)
2. Star ground from single point near power input
3. Keep analog (I2C sensors) away from switching circuits
4. Keep 40mm clearance around ESP32-C6 antenna (no copper on top layer)

### 10.3 Trace Width — IPC-2221 Standard

Trace width is calculated using the IPC-2221 empirical formula for external conductors:

```
I = k × ΔT^0.44 × A^0.725

Where:
  I   = current (A)
  k   = 0.048 (external/outer layer)  |  0.024 (internal layer)
  ΔT  = allowable temperature rise above ambient (°C)
  A   = cross-sectional area (mil²)  =  width_mil × thickness_mil
  thickness: 1oz copper = 1.37 mil  |  2oz copper = 2.74 mil
```

All values below use **ΔT = 10°C** (conservative; IPC-2221 permits 20°C for most PCB classes).

#### External Layer (k = 0.048)

| Net | Current | 1oz Cu (min width) | 2oz Cu (min width) | Notes |
|-----|---------|--------------------|--------------------|-------|
| 24V input (PSU→TVS→RPP) | 6.5 A | **158 mil (4.0 mm)** | **79 mil (2.0 mm)** | Use 2oz or copper pour |
| 24V main pump | ~1.0 A | 12 mil (0.30 mm) | 6 mil (0.15 mm) | Brushless pump |
| 24V dosing bus | 2.25 A total (3×0.75 A) | 37 mil (0.94 mm) | 19 mil (0.48 mm) | 3 steppers |
| 24V ATO valve | 0.3 A | 4 mil (0.10 mm) | 2 mil (0.05 mm) | Use 8 mil min for fab |
| 5V rail (post-buck) | 3.0 A | 55 mil (1.40 mm) | 28 mil (0.71 mm) | TPS62933 output |
| 3.3V rail (post-LDO) | 1.0 A | 12 mil (0.30 mm) | 6 mil (0.15 mm) | AMS1117 output |
| Stepper coil (per phase) | 0.75 A | 8 mil (0.20 mm) | 6 mil (0.15 mm) | TMC2209 OA1/OA2/OB1/OB2 |

#### Practical Minimums

| Rule | Value |
|------|-------|
| Minimum trace width (most fabs) | 6 mil (0.15 mm) |
| Recommended minimum (signal) | 8 mil (0.20 mm) |
| 24V input trace — recommended | **2oz copper pour or 4.0 mm trace** |
| 5V rail — recommended | 1.5 mm trace or copper pour on both layers |

#### Summary Recommendations

- **24V input net**: Use 2oz copper or a filled pour; 1oz at 4 mm trace is acceptable but borderline.
- **5V rail**: 1.5 mm at 2oz or 3 mm at 1oz. Route short and direct from buck output cap.
- **Dosing bus (24V, 2.25 A shared)**: 1 mm at 1oz is adequate per branch (each branch 0.75 A = 8 mil); the shared trunk before branching should be 37 mil (0.94 mm) at 1oz.
- **Signal traces (UART, I2C, STEP, DIR, EN)**: 8 mil minimum; no special width requirement.
- **BNC/probe connections**: match to probe input impedance (50Ω trace for RF, not applicable here — use 8 mil minimum).

### 10.4 Connector Placement
- Power input on one edge
- Pump outputs grouped together
- BNC connectors on opposite edge from power
- USB-C accessible for programming

### 10.5 Thermal Considerations
- Add thermal vias under MOSFET source pads
- Use large copper pours for heatsinking
- Consider heatsinks on MOSFETs if continuous pump operation

---

## 11. Test Points

Add test points for debugging:
- TP1: 3.3V
- TP2: 5V
- TP3: 24V
- TP4: GND
- TP5: I2C SDA
- TP6: I2C SCL
- TP7: 1-Wire
