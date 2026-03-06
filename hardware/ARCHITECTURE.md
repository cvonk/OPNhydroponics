# OPNhydroponics - Hardware Architecture

## System Overview

ESP32-C6 based NFT hydroponics controller with full sensor suite, dosing pump control, and automatic top-off (ATO) capability. Designed for Home Assistant integration via ESPHome with standalone operation support.

```
┌─────────────────────────────────────────────────────────────┐
│                           24V DC INPUT                      │
│                               │                             │
│                    ┌──────────┴──────────┐                  │
│                    │                     │                  │
│                    ▼                     ▼                  │
│              ┌─────────┐           ┌─────────┐              │
│              │ 24V Bus │           │ 5V DC   │              │
│              │ (Pumps) │           │ (Logic) │              │
│              └────┬────┘           └────┬────┘              │
│                   │                     │                   │
│         ┌─────────┼─────────┐           ▼                   │
│         ▼         ▼         ▼        ┌──────────┐           │
│   ┌──────────┐ ┌──────────┐ ┌─────┐  │ 3.3V LDO │           │
│   │Main Pump │ │ Dosing   │ │ ATO │  └────┬─────┘           │
│   │ MOSFET   │ │ Stepper  │ │Valve│       │                 │
│   └──────────┘ └──────────┘ └─────┘       │                 │
│                                    ┌──────┴──────┐          │
│                                    │  ESP32-C6   │          │
│                                    │             │          │
│                                    └──────┬──────┘          │
│                                           │                 │
│         ┌─────────────┬────────────┬──────┴──────┐          │
│         │             │            │             │          │
│    ┌────┴────┐   ┌────┴────┐   ┌───┴───┐  ┌──────┴──────┐   │
│    │  I2C    │   │  GPIO   │   │ UART  │  │    SPI      │   │
│    │  Bus    │   │         │   │       │  │  (future)   │   │
│    └────┬────┘   └────┬────┘   └───────┘  └─────────────┘   │
│         │             │                                     │
│    ┌────┴───────┐  ┌──┴───────┐                             │
│    │ pH EZO     │  │Ultrasonic│                             │
│    │ EC EZO     │  │ HC-SR04  │                             │
│    │ RTD EZO    │  └──────────┘                             │
│    │ BH1750     │                                           │
│    │ BME280     │                                           │
│    │ OLED       │                                           │
│    └────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Design Decisions

Designing for a 50 leafy greens / herbs system.

### 1. Reservoir Selection

**✅Selected: Black 200 L reservoir (minimum).** Larger is better.

The hydroponic industry commonly uses plant count as the sizing basis:

| Crop type | Rule | 200 L capacity | 300 L capacity |
|-----------|------|----------------|----------------|
| Leafy greens / herbs | 1 US gal (~3.8 L) per plant | ~53 plants | ~80 plants |
| Fruiting crops (tomatoes, peppers) | 2+ US gal (~7.6 L) per plant | ~26 plants | ~40 plants |

The rationale is that fruiting crops have higher and more variable water and nutrient uptake, so a larger buffer per plant is needed to prevent rapid EC and pH swings between dosing events. The minimum is a lower bound — more volume per plant always improves stability.

200 L comfortably supports a medium-scale home NFT system at either crop type. For a mixed planting (e.g. herbs + one tomato row), use the fruiting-crop rule for the whole reservoir.

For pH and nutrient stability, reservoir volume is the single most effective passive stabiliser:

**pH stability**
- Carbon dioxide exchange and plant root exudates drive continuous pH creep. A larger volume creeps more slowly, giving the controller more time between corrections.
- At 200 L a 5 mL shot of 85% phosphoric acid moves pH by ~0.05–0.1 units; at 40 L the same dose moves it ~0.25–0.5 units. Larger volume → smaller overshoot risk → fewer correction cycles → less total acid consumed.

**Nutrient (EC) stability**
- Water evaporates; plants take up water and nutrients at different ratios. Both effects shift EC. In a larger reservoir these shifts accumulate more slowly, so the controller doses less frequently and EC stays within the target window for longer between events.
- A single top-off event (adding plain water) causes a smaller EC dilution in 200 L than in 40 L, reducing the magnitude of the corrective nutrient dose that follows.

**Thermal stability**
- Nutrient uptake rates and EC calibration are temperature-dependent. A larger thermal mass buffers day/night and seasonal temperature swings, reducing measurement noise and the need for temperature-compensation corrections.

**Practical trade-offs at 200 L**
- Weight: 200 kg when full — floor loading and structural support must be considered.
- Mixing: Position the return-pipe to create turbulence, to prevent stratification and ensure the sensors read a representative sample.
- Refill logistics: larger volume means less frequent top-offs, but each top-off event requires a larger water volume. An ATO (§5) handles this automatically.

**Light and contamination control**
- Light proofing: the reservoir must be fully opaque. Any light penetration drives algae growth, which consumes nutrients, clogs the system, and destabilises pH. Black HDPE tanks or IBC totes with an opaque cover are preferred.
- Lid: use a tight-fitting lid at all times. A lid reduces evaporation (slowing EC drift), blocks ambient light, and prevents dust, insects, and debris from entering the solution.
- Cut-outs for plumbing and sensor cables should be kept as small as practical and sealed with foam or rubber grommets.


---

### 2. Main Pump Selection

Requirements:
- 400-600 L/hr for NFT (Nutrient Film Technique)
- 24V brushless motor for longlivity
- 2.5m head

Models considered

Feature        | ✅SHYSKY/AUBIG DC40F-2470<sup>[1](https://www.amazon.com/SHYSKY-DC40F-2460-Brushless-Waterproof-Submersible/dp/B0C5721V85)</sup> |  Topsflo TL-B10<sup>[2](https://www.topsflo.com/brushless-dc-pump/tl-b10-brushless-dc-pump.html)</sup> |
---------------|----------------------------|-----------------|
Voltage        | 24V DC       | 24V                 |
Current        | 1.2A         | 1.3A                |
Max Head       | 6m           | 8m                  |
Max Flow       | 960 L/hr     | 720 L/hr            |
Lifespan       | 30,000 hr    | 20,000 hr           |
Materials      | Weak acid/alkaline | FDA approved  |
Noise          | <40dB @1m    | <40dB @1m           |
Self-Priming   | No           | No                  |
Variable speed | PWM          | PWM                 |
Cost           | \$26         | \$30 on AliExpress  |

**✅Selected: SHYSKY/AUBIG DC40F-2470** for free shipping with Amazon Prime.


---


### 3. Dosing Pump Selection

A 24V rail is used because it enables a broader selection of main circulation pumps and ATO solenoid valves, which are voltage-sensitive (unlike current-regulated stepper drivers).

Use a peristaltic pumps for their characteristics
- Self-priming capability
- Chemical resistance (no wetted metal parts)
- No contamination between fluids
- Self-sealing when stopped (rollers pinch tube; no drip-back)

#### Type of peristaltic pump

Feature    | ✅Stepper Pump                  | DC Pump
-----------|---------------------------------|--------------------------------
Accuracy   | High (Calibration stays stable) | ❌Low (Drifts as motor/tube ages)
Min dose   | ~0.05 ml                        | ~1.0 ml
Control    | Higher (needs Driver)           | Lower (needs MOSFET)
Motor life | ~5,000 hours                    | 1,000 hrs max with brushed motor
Cost       | \$90 - \$100                    | \$10 - \$30

**✅Selected: Stepper pump** for acurate dosing and reliability. Risk of a DC pump "sticking" or drifting and crashing your pH is considered too high. 

#### Per-Event Dose Estimates

Assumptions:
- 2-part nutrients at 5–7 mL/L (standard hydroponic concentrate);
- pH Down = 85% phosphoric acid at ~1–2 mL/10 L per pH unit correction;
- tap water pH 7.0–7.5, target pH 5.8–6.2;
- EC target 1.5–2.5 mS/cm. 
- Keepking pH Down steps ≤5 mL to avoid overshoot on a large volume. Step window (minimum 60 s) includes pump-on time plus mix-and-settle time before the next sensor reading.

The table below gives per-event dose estimates for a nominal **200 L reservoir**. Doses are applied incrementally: the controller pumps a small volume, waits for mixing, re-measures, and repeats as needed. Actual volumes scale with reservoir size and source-water chemistry.

| Channel | Event | Dose per step | Steps to target | Total volume | Step window | Required flow rate (100% DC) |
|---------|-------|--------------|-----------------|--------------|-------------|------------------------------|
| Nutrients A | Initial fill | 50–100 mL | 10–20 | 500–1,400 mL | 60–120 s | 25–100 mL/min |
| Nutrients B | Initial fill | 50–100 mL | 10–20 | 500–1,400 mL | 60–120 s | 25–100 mL/min |
| Nutrients A | Maintenance | 10–50 mL | 2–5 | 20–250 mL | 60–120 s | 5–50 mL/min |
| Nutrients B | Maintenance | 10–50 mL | 2–5 | 20–250 mL | 60–120 s | 5–50 mL/min |
| pH Down | Initial fill | 3–5 mL | 6–12 | 18–60 mL | 60 s | 3–5 mL/min |
| pH Down | Maintenance | 1–3 mL | 1–3 | 1–9 mL | 60 s | 1–3 mL/min |

#### Dosing Pump Model Selection

Peristaltic stepper dosers are typically rated for a 50% duty cycle. The pump runs for 50% of the step window, leaving the remaining 50% for mixing and settling before the next measurement. This doubles the required instantaneous flow rate relative to continuous pumping over the full window.

| Channel | Flow rate (continuous) | Flow rate (50% DC)  | 
|---------|------------------------|---------------------|
| Nutrients A/B | ~50 mL/min | ~100 mL/min |
| pH Down | ~5 mL/min | ~10 mL/min |

Two models were considered as shown in the table below.

Feature               | ✅ANKO A200SX | Kamoer KAS-SE |
----------------------|-------------|-----------------|
Current               | 1.7A                          | 1.2A
Motor                 | 1.8°/step                     | 1.8°/step
Motor life            | 5,000+ hours                  | ❌unknown
Duty cycle            | 50% max (300 s on-time limit) | ❌unknown
Acid resistant tubing | Norprene                      | Bioprene
Tubing life           | 200-1,000 hr of runtime       | ❌unknown
Tubing Ph-down        | 1/16" (max 54 mL/min)         | B08 (max 42 mL/min)
Tubing Nutriants      | 1/8" (max 219 mL/min)         | ❌B10 (84 mL/min)
Cost                  | \$90 at ANKO Products         | Cost: \$95 at AliExpress |

**✅Selected: ANKO A200SX** despite its higher current, because it has clear specifications. The specs for Kamoer KAS-SE <sup>[1](https://www.kamoer.com/us/product/doc.html?id=9005),[2](https://robu.in/wp-content/uploads/2021/12/kamoer-catalog-1.pdf)</sup> from manufacturer and vendors specify inconsistent flow rates with Bioprene tubing.


---


### 4. Dosing Pump Driver Selection

Requirements:
- 24V pump voltage
- 3.3V I/O voltage
- UART interface, ideally shared between drivers

The parts listed below were considered.

Feature         | ✅Trinamic TMC2209 | Trinamic TMC2225 |
----------------|---------------------|------------------|
Pump voltage    | 24V                 | 24V              |
I/O voltage     | 3.3V supported      | 3.3V supported   |
Current         | 2.0A RMS max        | ❌1.4A RMS max  |
UART            | Yes (shared)        | Yes              |
Near-silent op  | StealthChop2        | StealthChop2     |
Fault detection | StallGuard4         | unknown          |

**✅Selected: Trinamic TMC2209** because the TMC2225 can't drive the 1.7A current needed for the ANKO A200SX pump.

#### Current setting and operating margin

To reduce motor and driver temperature and extend service life, choose a target operating range of **70–90%** of the pumps rated **I<sub>RMS</sub>** . Very low thermal duty cycle (dosing pulses are seconds long) means thermal risk is minimal, but the margin also guards against stall on aged or swollen tubing.

This current should be limited in hardware and firmware:
1. Use the V<sub>REF</sub> input of the TMC2209 to set a hard limit to 90% of the 1.7 A<sub>RMS</sub> motor current.
2. Set `IHOLD_IRUN` register using firmware to further lower the current to a practical level Configure `IHOLD=0` (zero standstill current) via UART, so sense resistors and motor carry no current between dosing events.


---


### 5. Main Reservoir Level System

Uses existing ultrasonic sensor for level detection with a normally-closed solenoid valve:
- **Detection**: Ultrasonic sensor monitors water level continuously
- **Valve type**: 24V NC (normally closed) solenoid - fails safe (closed)
- **Safety**: Float switch provides hardware backup cutoff
- **User confirmation**: System requests approval via Home Assistant before filling
- **Timeout**: Maximum fill time prevents overflow if sensor fails


### 5.1 Automatic Top-Off (ATO) Selection

Requirements
- 24V to match system power rail
- Normally Closed (NC), so it is fail-safe: valve closes on power loss
- 0-0.8 MPa (0-116 PSI), the typical municipal water pressure
- Brass body, EPDM/NBR seal, so it is food-safe and corrosion resistant

The models listed below were considered

Feature | ✅DIGITEN DC 24V 1/4" NC<sup>[1](https://www.amazon.com/DIGITEN-Solenoid-Reverse-Osmosis-System/dp/B00X6RAHMU)</sup> | U.S. Solid JFSV00068<sup>[2](https://ussolid.com/products/u-s-solid-electric-solenoid-valve-1-4-24v-dc-solenoid-valve-stainless-steel-body-normally-closed-viton-seal-html?_pos=6&_fid=d5a36750a&_ss=c)</sup> | U.S. Solid JFSV00052<sup>[3](https://ussolid.com/products/u-s-solid-electric-solenoid-valve-1-4-24v-dc-solenoid-valve-brass-body-normally-closed-viton-seal-html?_pos=3&_fid=fa20ea39a&_ss=c)</sup> | U.S. Solid USS-MSV00027<sup>[4](https://ussolid.com/products/u-s-solid-motorized-ball-valve-1-4-stainless-steel-electrical-ball-valve-with-full-port-9-24-v-ac-dc-2-wire-auto-return-html)</sup>
----------------|-------------------------|-------------------|---------------------|---
Voltage         | 24V DC                  | 24V DC            | 24V DC              | 9-24V AC/DC
Body            | Plastic                 | Stainless steel   | Brass               | Stainless steel
Default state   | Normally Closed         | Normally Closed   | Normally Closed     | Normally Closed
Port            | 1/4" Quick Connect      | 1/4" NPT thread   | 1/4" NPT thread     | 1/4" NPT thread
Current         | 0.2A                    | 0.6A              | 0.6A                | 0.2A (when moving)
Max pressure    | 0.8 MPa (116 PSI)       | 0.7 MPa (101 PSI) | 0.7 MPa (101 PSI)   | 1.0 MPa (145 PSI)
Design          | Solonoid orifice        | Solonoid orifice  | Solonoid orifice    | Ball valve
Response time   | <1s                     | <1s               | <1s                 | 3-5s
Drinking safe   | Yes                     | Yes               | ❌No                | Yes
Cost            | \$10                    | \$30              | \$17                | $25

**✅Selected: DIGITEN DC 24V 1/4" NC** for its price.


### 5.2 Float Switch Selection

Goals:
- A low level float switch keeps keep main pump from running dry.
- A high level float switches provides a hardware guard against both overfilling the reservoir.

Requirements
- Normally closed switch.
- Horizontal side-mount, so the top of the reservoir can be opened for inspection. Also the sensing level is fixed by where you drill the hole — no float travel calculation, no ambiguity. 

Feature     | ✅Flowline LH25-1101
------------|----------------------
Contact     | SPST dry reed, selectable NO/NC by float orientation
Material    | Polypropylene (PP) body and float
Mount       | 1/2" NPT side-wall
Accuracy    | ±5mm in water
IP rating   | IP68
Wire        | 2' (61cm), 2-conductor, 22 AWG

**✅Selected: Flowline LH25-1101 (Horizontal, PP)**. No alternatives were considered.


---


### 6. Standalone Operation

The controller operates independently when Home Assistant is unavailable:
- Local pH control: Once daily at 10:00 AM (avoids temperature-induced pH fluctuations)
- Doses pH Down only — pH creep is always upward; no pH Up pump fitted (see §10)
- Local EC control: Doses nutrients when EC drops below threshold (every 10 min)
- Safety interlocks: Float switch protection always active
- ATO: Requires HA for user confirmation (manual override via physical button possible)
- Data logging: Buffers readings until HA reconnects

### 7. Dosing Reservoir Level Monitoring

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

### 8. Hardware Float Switch Safety Cutoffs

**Decision: FLOAT_LOW and FLOAT_HIGH provide hardware-enforced cutoffs, not software-only.**

To ensure fail-safe operation independent of MCU firmware, each float switch drives a small NPN transistor that directly pulls the respective MOSFET gate to GND when its cutoff condition is met. The MCU can still read the float state via GPIO for monitoring and alerting, but the hardware path acts regardless of software state.

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

### 0. Probes

Highly reliable and continuous monitoring is essential for maintaining optimal pH (5.5–6.5) and EC (0.8–2.5 mS/cm) levels.

Requirements:
- Provide high accuracy and resist electrical noise from pumps.
- Digital probes are highly recommended for the ESP32 to ensure stable readings without the need for custom analog filtering or voltage dividers.
- Designed for "7/24" monitoring to ensure the probes don't degrade under constant use.

**✅Selected: Atlas Scientific Probes**

1. **Lab Grade pH Probe (ENV-40-pH)**
   - Communicates via I2C or UART, making it plug-and-play with the ESP32.
   - According to Atlas Scientific, it provides lab-grade accuracy (+/- 0.002pH) and includes built-in temperature compensation and 1-3 point calibration.
   - Needs an extra EZO-pH circuit board. This board supports 3.3V logic.
   - Cost: \$85 plus \$46 for the circuit at Atlas Scientific.

2. **K 1.0 Conductivity Probe (EC-K1.0)**
   - According to Atlas Scientific, the probe is designed for the nutrient ranges typical in hydroponics (0.8–2.5 mS/cm) with a lifespan of roughly 2–2.5 years under continuous immersion.
   - Needs an extra EZO-EC circuit mezzanine board. This board supports 3.3V logic.
   - Cost \$140 for the probe, and \$68 for the circuit at Atlas Scientific.

3. **Temperature Probe (PT-1000)**
   - Also supports I2C/UART for direct digital data transfer to the ESP32.
   - Range: 200 ̊C to 850 ̊C +/- (0.15 + (0.002*t)) 
   - According to Atlas Scientific, the probe is designed for -200°C to 850°C with a lifespan of roughly 15 years under continuous immersion.
   - Needs an extra EZO-RTD circuit mezzanine board. This board supports 3.3V logic.
   - Cost \$24 for the probe, and \%36 for the circuit at Atlas Scientific.

**Alternative considered — DFRobot Gravity Sensors**

1. **PH Sensor Kit**
   - Needs a external ADC or a high-quality voltage regulator, as the ESP32’s native ADC is often non-linear.
   - Comes with a signal conversion board. This board supports 3.3V logic.
   - Cost \$65 at DFRobot plus price of an external ADC.

2. **Lab Grade Analog Conductivity Sensor Kit (K=1)**
   - Needs a external ADC or a high-quality voltage regulator.
   - Comes with a signal conversion board. This board supports 3.3V logic.
   - Cost \$70 at DFRobot plus price of an external ADC.

*Not selected because*: While DFRobot Gravity is significantly more affordable, they seem better suited for smaller hobbyist projects or prototypes where probes are not submerged 24/7. It is engineerd for a different level of "continuous" use according to user reports.

**Alternative considered — BlueLab Probes**

1. **pH Probe (PROBPH)**
   - ±0.1pH
   - Requires regular cleaning/calibration
   - Needs a external ADC or a high-quality voltage regulator.
   - Cost \$99

2. **Pro Controller Conductivity Probe (PROBPCEC)**
   - range approx. 0 - 10k µS/cm
   - Requires regular cleaning/calibration
   - Needs a external ADC or a high-quality voltage regulator.
   - Cost \$72

*Not selected because*: While Bluelab states an average lifespan of 18 months for their pH probes. Many users report having to replace them more frequently in 24/7 submerged environments. 


---


### 0. Probe Isolation Strategy

Requirement: 
- Prevent probe interference and ground loops (especially between pH and EC).

**Selected: EZO-Style I2C Circuits**
- Each probe has dedicated I2C interface circuit
- Galvanically isolated power per probe
- All probes can read simultaneously
- Cost: ~$60-150 depending on source (Atlas vs clones)

**Alternative considered — Time-Division Multiplexing**
- Single non-isolated ADC (ADS1115)
- MOSFET switches to power probes sequentially
- Only one probe powered at a time
- Cost: ~$15 for all probe interfaces

*Not selected because*: Lower accuracy, more complicated software, not worth the savings at medium scale.


### 4. Microcontroller Selection

To manage the hydroponic system with high-precision probes and dosing pumps, your microcontroller needs to handle multiple communication protocols simultaneously while maintaining timing for dosing.

Requirements:
1. Communication Protocols
   - I2C Bus: Required for Atlas Scientific EZO circuits (pH, EC, Temp).
   - UART: Required for TMC2209/TMC2225 drivers.
   - GPIO: You need 1 step pin per pump, 2 for water level sensors, 2 for float switches.

2. Processing and Memory
   - Dual-Core Architecture: The ESP32 is ideal because you can run the Dosing Logic/Stepper timing on Core 1 and the Wi-Fi/Data Logging/Web Server on Core 0. This prevents "jitter" in the stepper motors when the device sends data to the cloud.
   - Non-Volatile Memory: Essential for storing calibration data for your pH/EC probes and your "steps-per-ml" pump values so they aren't lost during power outages.
3. Power and Logic Levels
   - 3.3V Logic: The ESP32 operates at 3.3V.
   - ADC Resolution: If you bypass Atlas Scientific and use analog sensors, you need a 12-bit or 16-bit ADC. The ESP32's internal ADC is 12-bit but notoriously non-linear; an external ADS1115 (16-bit) is highly recommended for stable analog readings.
4. Connectivity Requirements
   - WiFi: Enables push alerts to a dashboard (like Home Assistant, Blynk, or Grafana) via MQTT or HTTP.
   - Matter/Thread: be ready for the future of home automation.

The ESP32 (WROOM or WROVER modules) is the industry standard for this scale.

**Selected: ESP32-C6-DevKitC-1-N8**
- Development board with USB-C, RGB-LED, buttons, and antenna.
- Mounts to carrier PCB via pin headers.
- 8MB flash memory.
- Cost: \$9

**Alternatives considered — ESP32-C6-WROOM-1**
- Bare module, requires antenna trace design and USB circuit
- Cost: \$6 plus the cost of USB-C port, RGB-LED and buttons.

*Not selected because:* The integrated USB-C port, PCB antenna and RGB LED simplify the PCB design. Not worth the marginal difference in cost.

### 9. Nutrient A and B on Separate TMC2209 Channels

**Decision: STEP_NUT_A and STEP_NUT_B each have a dedicated TMC2209 driver.**

Two-part nutrients (Part A: calcium/iron; Part B: phosphate/sulphate) are kept separate in concentrate to prevent precipitation, but are always dosed at a 1:1 ratio in normal operation — same STEP pulse count, at the same time.

Combining both pump motors on a single TMC2209 was considered and rejected:

| Factor | Combined | Separate (chosen) |
|--------|----------|-------------------|
| STEP GPIO cost | Saves 1 pin (GPIO19 free) | Uses GPIO15 + GPIO19 |
| DIR GPIO cost | n/a | n/a — DIR hardwired to 3.3V on all drivers |
| BOM cost | Save ~$3 (1× TMC2209) | Keep as-is |
| Ratio flexibility | Locked 1:1 | Any ratio in firmware |
| Tubing wear compensation | Not possible per-pump | Recalibrate each pump independently |
| Fault isolation | One failure disables both | Identify which pump failed |

**Rationale:** with stepper pumps the primary calibration concern shifts from flow-rate drift (eliminated by step counting) to tubing bore wear. Bore wear affects pump A and B at different rates depending on chemical exposure. Separate STEP channels allow independent step-count adjustment per pump without mechanical changes. The cost delta is one TMC2209 (~$3). DIR is hardwired to 3.3V on all drivers — peristaltic pumps are self-sealing and never need direction reversal.

**Future field change:** if combining is ever desired, tie the two coil outputs in parallel externally and leave one TMC2209 unpopulated (DNP). No PCB revision required.

### 10. pH Chemistry and Dosing Sequence

#### Why pH always drifts upward

In an active NFT or DWC system, pH creeps upward between doses due to two mechanisms:

1. **Plant nutrient uptake**: roots preferentially absorb nitrate (NO₃⁻) and release bicarbonate (HCO₃⁻) in exchange, alkalising the solution over hours.
2. **CO₂ offgassing**: carbonic acid (H₂CO₃) from dissolved CO₂ escapes the reservoir, removing a natural acid buffer and allowing pH to rise.

This upward drift is the dominant long-term trend in a healthy system.

#### Why there is no PUMP_PH_UP

Because pH reliably creeps upward, the system only ever needs to dose *down*.
A pH Up pump would fire only if pH somehow fell below target — an unusual condition that indicates a problem (wrong nutrient formula, excessive CO₂ injection, contamination) rather than normal operation. **PUMP_PH_UP has been omitted from the design.**  Only PUMP_PH_DN (GPIO11 STEP, TMC2209 U5) is fitted.

If pH falls unexpectedly low, the correct response is manual investigation, not
automated correction with an unmonitored acid reserve.

#### How nutrient dosing interacts with pH

Nutrient concentrates (especially Part B: phosphate and sulphate salts) are acidic.
Adding nutrients causes a transient pH *drop* of ~0.1–0.3 units per typical dose,
after which pH recovers and resumes its upward creep.

This has two implications for the control loop:

1. **Sequence matters**: EC correction must complete and the reservoir must mix before pH correction fires. Correcting pH immediately after an EC dose would be chasing a transient reading, not the steady-state pH.
2. **Nutrients reduce pH correction demand**: after a large EC dose, pH Down may not be required at all for that cycle.

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
| 20 | (available) | — | Free GPIO — EN tied to GND on all TMC2209 drivers (IHOLD=0 handles standstill) |
| 21 | TMC2209_UART_RX | Input | TMC2209 UART bus RX (ESP32-C6 UART1); direct connection to bus node |
| 22 | TMC2209_UART_TX | Output | TMC2209 UART bus TX (ESP32-C6 UART1); 1kΩ series to bus node (per TMC2209 datasheet §4.3) |
| 23 | (available) | — | Free GPIO |

## Power Architecture

### Recommended Supply

```
Recommended Power Supplies:
- Quality: Mean Well, TDK-Lambda, or equivalent (low ripple essential)
```


**Mean Well LRS-150-24** (24V / 6.5A / 150W, enclosed metal, convection cooled) —
recommended for comfortable headroom. **Minimum: LRS-100-24** (24V / 4.2A / 100W) if cost is a priority.

Peak 24V load estimate: TMC2209 supply current is chopper-averaged, not equal to motor coil current. Operating at 80% of rated (1.36A) with ~3Ω NEMA 17 coil resistance:
1.36² × 3Ω × 2 coils = 11.1W per motor; at ~82% driver efficiency → 11.1W / 0.82 / 24V ≈ 0.56A from 24V rail per motor. At 90% (1.53A) → 0.71A per motor.
Main pump (~0.75A) + 3× A200SX dosing (~0.56A each at 80%, worst-case all stepping) + ATO (~0.3A) + logic (~0.1A) ≈ 2.8A. Per §10 sequence, nutrients and pH Down never step simultaneously; normal worst-case is ~2.0A. LRS-100-24 (4.2A) is adequate; LRS-150-24 (6.5A) gives comfortable headroom and is recommended.

**IP67 alternative:** LPV-100-24 (24V / 4.2A / 100W) for humid environments.
Avoid HDR-60-24 — only 2.5A (insufficient).

```
24V DC Input (LRS-150-24, 6.5A)
    │
    ├──► 24V Rail ──┬──► Main Pump MOSFET Q1 (IRLR2905)
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

Note: TPS62933 input range is 3.8–30V — 24V is within spec.

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
| Main Pump (24V, TBD) | 24V | 300mA | 1.0A |
| Dosing pump — A200SX ×3 (each, chopper-avg @ 80%) | 24V | 0 (EN disabled) | ~560mA |
| ATO Solenoid Valve (24V NC) | 24V | 0 (idle) | 300mA |
| **24V Total** | | ~300mA | ~3.5A |

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
| 24V Power | 2-pin pluggable screw terminal (3.5mm) |
| Main Pump | 2-pin pluggable screw terminal (5.08mm — Phoenix MSTB 2.5/2-ST-5.08) |
| Dosing Pumps (stepper) | 3× A200SX connector — **verify on receipt**; likely JST PH 2.0mm 4-pin or bare pigtail (NEMA 17 standard); use screw terminal breakout or match to actual cable |
| ATO Solenoid | 2-pin pluggable screw terminal (3.5mm — Phoenix MC 1.5/2-ST-3.5) |
| pH/EC/RTD Probes | BNC female (panel mount) |
| I2C Sensors | 4-pin Phoenix Contact 1803280/1803581 |
| Float Switches | 2-pin JST-XH (×2) |
| Ultrasonic | 4-pin JST-XH |
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
