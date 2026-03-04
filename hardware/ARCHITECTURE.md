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

**Selected: Kamoer KAS SF-12V stepper peristaltic pump + TMC2209 stepper driver**

Peristaltic pumps are used for:
- Self-priming capability
- Chemical resistance (no wetted metal parts)
- No contamination between fluids
- Self-sealing when stopped (rollers pinch tube; no drip-back without motor reversal)

DC peristaltic pumps were evaluated and rejected. Their flow rate (mL/s) depends on
supply voltage and tubing wear, requiring periodic re-calibration to maintain dosing
accuracy. Stepper-driven pumps dose by step count × pump displacement constant —
calibration is a one-time measurement and accuracy is maintained until tubing replacement.

**Pump — Kamoer KAS SF-12V:**
- Voltage: 12V
- Current: 0.75A
- Flow rate: ~11.5–71.5 mL/min (3-rotor head, speed-dependent)
- Tubing: 3mm ID × 5mm OD, silicone or BPT
- Motor: bipolar stepper (4-wire)
- Order without bundled drive board; TMC2209 used instead

**Driver — Trinamic TMC2209 (QFN-28, standalone mode):**
- VM: 4.75–29V (12V rail used)
- Logic: 3.3V
- Current: 2A RMS rated, set to 0.75A via VREF resistor
- StealthChop2: near-silent operation at low step rates (default in standalone mode)
- 1/16 microstepping hardwired via MS1/MS2; interpolated to 1/256 internally
- Standalone mode: PDN_UART pulled HIGH, MS1/MS2 set microstepping, STEPPER_EN (GPIO20) gates power
- UART mode (GPIO21 RX / GPIO22 TX): all 3 drivers on one shared bus; IHOLD=0 eliminates standstill
  current, making STEPPER_EN redundant; StallGuard4 stall detection available; see SCHEMATIC_DESIGN.md §7.2
- DIAG pin available for fault detection (optional in v1)

**Why 12V and not 24V:**
The 24V variant of the KAS pump was considered to reduce supply current. It does not help
for stepper motors driven by a current-regulating chopper driver.

The TMC2209 regulates coil current to the VREF/RSENSE setpoint (0.75A) regardless of
supply voltage. At low step rates — where dosing pumps operate — back-EMF is negligible,
so supply power is approximately I²×R_coil, independent of VM. Switching from 12V to 24V
supply with the same 0.75A coil current does not meaningfully reduce supply current draw.

The only real benefit of higher supply voltage for stepper motors is a higher achievable
step rate (faster di/dt = V/L allows the coil to reach rated current at higher RPM). For
a dosing pump turning a few rotations per dose at <50 RPM, this is irrelevant.

Using 24V for dosing pumps while keeping 12V for the main pump and ATO valve would require
a second supply rail. 12V is used throughout.

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
  - Doses pH Down only — pH creep is always upward; no pH Up pump fitted (see §9)
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
- GPIO2 drives NPN transistor base; NPN collector tied to Q8 gate
- When GPIO1 HIGH: NPN saturates → Q8 gate pulled to ≈GND → ATO valve closes (hardware)
- When GPIO1 LOW: NPN off → Q8 gate controlled by GPIO7 normally

**Additional components required (per channel):**
- 1× MMBT3904 NPN transistor, SOT-23 (~$0.05)
- 1× 4.7kΩ base resistor, 0805 (already in BOM)

### 8. Nutrient A and B on Separate TMC2209 Channels

**Decision: STEP_NUT_A and STEP_NUT_B each have a dedicated TMC2209 driver.**

Two-part nutrients (Part A: calcium/iron; Part B: phosphate/sulphate) are kept separate in
concentrate to prevent precipitation, but are always dosed at a 1:1 ratio in normal
operation — same STEP pulse count, at the same time.

Combining both pump motors on a single TMC2209 was considered and rejected:

| Factor | Combined | Separate (chosen) |
|--------|----------|-------------------|
| STEP GPIO cost | Saves 1 pin (GPIO19 free) | Uses GPIO15 + GPIO19 |
| DIR GPIO cost | n/a | n/a — DIR hardwired to 3.3V on all drivers |
| BOM cost | Save ~$3 (1× TMC2209) | Keep as-is |
| Ratio flexibility | Locked 1:1 | Any ratio in firmware |
| Tubing wear compensation | Not possible per-pump | Recalibrate each pump independently |
| Fault isolation | One failure disables both | Identify which pump failed |

**Rationale:** with stepper pumps the primary calibration concern shifts from flow-rate
drift (eliminated by step counting) to tubing bore wear. Bore wear affects pump A and B
at different rates depending on chemical exposure. Separate STEP channels allow independent
step-count adjustment per pump without mechanical changes. The cost delta is one TMC2209
(~$3). DIR is hardwired to 3.3V on all drivers — peristaltic pumps are self-sealing and
never need direction reversal.

**Future field change:** if combining is ever desired, tie the two coil outputs in parallel
externally and leave one TMC2209 unpopulated (DNP). No PCB revision required.

### 9. pH Chemistry and Dosing Sequence

#### Why pH always drifts upward

In an active NFT or DWC system, pH creeps upward between doses due to two mechanisms:

1. **Plant nutrient uptake**: roots preferentially absorb nitrate (NO₃⁻) and release
   bicarbonate (HCO₃⁻) in exchange, alkalising the solution over hours.
2. **CO₂ offgassing**: carbonic acid (H₂CO₃) from dissolved CO₂ escapes the reservoir,
   removing a natural acid buffer and allowing pH to rise.

This upward drift is the dominant long-term trend in a healthy system.

#### Why there is no PUMP_PH_UP

Because pH reliably creeps upward, the system only ever needs to dose *down*.
A pH Up pump would fire only if pH somehow fell below target — an unusual condition
that indicates a problem (wrong nutrient formula, excessive CO₂ injection, contamination)
rather than normal operation. **PUMP_PH_UP has been omitted from the design.**
Only PUMP_PH_DN (GPIO11 STEP, TMC2209 U5) is fitted.

If pH falls unexpectedly low, the correct response is manual investigation, not
automated correction with an unmonitored acid reserve.

#### How nutrient dosing interacts with pH

Nutrient concentrates (especially Part B: phosphate and sulphate salts) are acidic.
Adding nutrients causes a transient pH *drop* of ~0.1–0.3 units per typical dose,
after which pH recovers and resumes its upward creep.

This has two implications for the control loop:

1. **Sequence matters**: EC correction must complete and the reservoir must mix before
   pH correction fires. Correcting pH immediately after an EC dose would be chasing a
   transient reading, not the steady-state pH.
2. **Nutrients reduce pH correction demand**: after a large EC dose, pH Down may not
   be required at all for that cycle.

#### Required firmware dosing sequence

```
1. Measure EC
2. If EC < target → dose PUMP_NUT_A + PUMP_NUT_B simultaneously
3. Wait for mixing (circulation pump running, e.g. 5–10 min)
4. Re-measure pH
5. If pH > target → dose PUMP_PH_DN
6. Wait for mixing (e.g. 2–5 min)
7. Re-measure pH — repeat step 5 if still high (avoid overdosing)
8. Log readings
```

Never run EC and pH corrections in the same step. Always re-measure after mixing.

## Pin Assignment

| GPIO | Signal | Direction | Notes |
|------|--------|-----------|-------|
| 0 | FLOAT_LOW | Input | Flow float switch |
| 1 | FLOAT_HIGH | Input | High-level float switch |
| 2 | ATO_VALVE | Output | ATO solenoid valve via MOSFET Q8; R30 (4.7kΩ) DNP |
| 3 | US_ECHO | Input | Ultrasonic sensor echo |
| 4 | I2C_SDA | Bidirectional | I2C bus (4.7kΩ pullup) |
| 5 | I2C_SCL | Output | I2C bus (4.7kΩ pullup) |
| 6 | EZO_PDIS | Output | ADM3260 isoPower disable — active HIGH; shared by U3 (pH) & U4 (EC) |
| 7 | US_TRIG | Output | Ultrasonic sensor trigger |
| 8 | (RGB LED) | — | DevKit on-board RGB LED — do not use |
| 9 | (available) | — | Strapping pin — internal 45kΩ pullup; leave undriven at boot |
| 10 | PUMP_MAIN | Output | Main circulation pump via MOSFET Q1 (IRLR2905) |
| 11 | STEP_PH_DN | Output | TMC2209 STEP for pH Down driver |
| 15 | STEP_NUT_A | Output | TMC2209 STEP for Nutrient A driver; strapping pin — 10kΩ pulldown holds STEP LOW at boot |
| 17 | (CP2102 TX) | — | Reserved — CP2102N UART TX on DevKit |
| 18 | (available) | — | Free GPIO |
| 19 | STEP_NUT_B | Output | TMC2209 STEP for Nutrient B driver |
| 20 | STEPPER_EN | Output | TMC2209 shared active-LOW enable for all 3 stepper drivers (not needed in UART mode) |
| 21 | TMC2209_UART_RX | Input | TMC2209 UART bus RX (ESP32-C6 UART1) |
| 22 | TMC2209_UART_TX | Output | TMC2209 UART bus TX (ESP32-C6 UART1) |
| 23 | (available) | — | Free GPIO |

## Power Architecture

### Recommended Supply

**Mean Well LRS-75-12** (12V / 6A / 75W, enclosed metal, convection cooled).

Peak 12V load estimate: main pump (1.2A) + 3× dosing (0.75A each, only when stepping) +
ATO valve (0.5A) + logic buck input (0.5A) ≈ 4.5A worst-case simultaneous. 6A provides
1.5A headroom.

**IP67 alternative:** LPV-60-12 (12V / 5A / 60W) for humid environments; adequate if
loads are not fully simultaneous. Avoid HDR-60-12 — only 4.5A (marginal after derating).

```
12V DC Input (LRS-75-12, 6A)
    │
    ├──► 12V Rail ──┬──► Main Pump MOSFET Q1 (IRLR2905)
    │               ├──► 3× TMC2209 dosing stepper drivers (VM pin)
    │               └──► ATO Solenoid Valve MOSFET Q8 (AO3400A)
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
| Dosing pump — KAS SF-12V (each) | 12V | 0 (EN disabled) | 750mA |
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
| Dosing Pumps (stepper) | 3× JST S6B-PH-K-S (6-pin PH 2.0mm right-angle TH — mates with PHR-6 on KAS SF-12V cable; VCC/GND/A+/A−/B+/B−) |
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
