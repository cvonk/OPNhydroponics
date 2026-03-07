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

A 24V rail is used because it enables a broader selection of main circulation pumps and ATO solenoid valves, which are voltage-sensitive (unlike current-regulated stepper drivers).

The controller operates independently when Home Assistant is unavailable:
- Local pH control: Once daily at 10:00 AM (avoids temperature-induced pH fluctuations)
- Doses pH Down only — pH creep is always upward; no pH Up pump fitted (see §10)
- Local EC control: Doses nutrients when EC drops below threshold (every 10 min)
- Safety interlocks: Float switch protection always active
- ATO: Requires HA for user confirmation (manual override via physical button possible)
- Data logging: Buffers readings until HA reconnects


---


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

#### Parts Considered

Feature        | ✅[SHYSKY/AUBIG DC40F-2470](https://www.amazon.com/SHYSKY-DC40F-2460-Brushless-Waterproof-Submersible/dp/B0C5721V85) | [Topsflo TL-B10](https://www.topsflo.com/brushless-dc-pump/tl-b10-brushless-dc-pump.html) |
---------------|--------------|---------------------|
Voltage        | 24V DC       | 24V                 |
Current        | 1.2A         | 1.3A                |
Max Head       | 6m           | 8m                  |
Max Flow       | 960 L/hr     | 720 L/hr            |
Lifespan       | 30,000 hr    | 20,000 hr           |
Materials      | Weak acid/alkaline | FDA approved  |
Noise          | <40dB        | <40dB               |
Self-Priming   | No           | No                  |
Variable speed | PWM          | PWM                 |
Cost           | \$26         | \$30 on AliExpress  |

**✅Selected: SHYSKY/AUBIG DC40F-2470** for free shipping with Amazon Prime.


---


### 3. Dosing Pump Selection

Use a peristaltic pumps for their characteristics
- Self-priming capability
- Chemical resistance (no wetted metal parts)
- No contamination between fluids
- Self-sealing when stopped (rollers pinch tube; no drip-back)

#### 3.1. Technologies Considered

Feature    | Stepper Pump                    | DC Pump
-----------|---------------------------------|--------------------------------
Accuracy   | High (Calibration stays stable) | ❌Low (Drifts as motor/tube ages)
Min dose   | ~0.05 ml                        | ~1.0 ml
Control    | High (with Driver)              | Low (with MOSFET)
Motor life | ~5,000 hours                    | 1,000 hrs max with brushed motor
EMI noise  | ❌High                          | Moderate
Cost       | \$90 - \$100                    | \$10 - \$120

A stepper motor is nice for its acurate dosing and reliability, but may create a PCB layout headache due to its EMI. On the other hand with a DC pump, we risk the pump "sticking" or drifting and crashing your pH is too high.   As there is no clear winner, we'll consider both types of motors.

Before we can explore specific dosing pumps, we need to know the required dosing.

#### 3.2. Per-Event Dose Estimates

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

#### 3.3. Parts Considered

Peristaltic stepper dosers are often rated for a 50% duty cycle. This doubles the required instantaneous flow rate relative to continuous pumping over the full window.

Requirements
- 24V DC motor
- I2C or UART control
- Continuous flow rate of ~5ml/min for pH down.
- Continuous flow rate of ~50 mL/min for Nutrients.

Note that the **EZO-PMP is not a stepper-based**. The dependence on flow-rate calibration and the "Dose over Time" logic confirm it is a regulated DC motor using tachometer/time-based feedback rather than discrete steps. It achieves ±1% accuracy the same way a Kamoer NKP-DC-B08 would — via calibrated timed runs — not via step counting. 

Feature       | [ANKO A200SX](https://ankoproducts.com/products/a200sx) | [Kamoer KAS-SE](https://www.kamoer.cn/us/product/detail.html?id=9005) | [Atlas EZO-PMP](https://atlas-scientific.com/peristaltic/ezo-pmp/)
--------------|------------------------|-----------------------|--------------
Voltage       | 24V DC                 | 24V DC                | 12 – 24V DC
Technology    | Stepper motor          | Stepper motor         | DC Motor
Rated Current | 1.7A (RMS)             | 0.4 – 0.8A            | 0.1 – 0.25A
Duty Cycle    | 50% (Industrial)       | Intermittent          | 100% (Continuous)
Acid Tubing   | Norprene               | Bioprene              | Bioprene / Tygon
Max Flow Rate | 450 mL/min             | ❌maybe 71.5 mL/min   | 105 mL/min
Motor Life    | 5,000+ hr              | 1,000 – 2,000 hr      | ❌~1,000 hr
Tubing Life   | ~1,000 hr              | ~1,000 hr             | 500 – 1,000 hr
Driver        | Needs ext. driver      | Needs ext. driver     | Build-in
Control       | I2C to ext. driver     | I2C to ext. driver    | Native I2C
EMI noise     | ❌High: 1.7A switching | Moderate 0.8A switching | Low
Price         | \$90 on ANKO Products  | \$95 on AliExpress    | \$120 on Atlas

Again, no clear winner.  But if we're willing to accept some limitations on how we use the ANKO stepper pump, we can have the best of both worlds.  Acceptable EMI noise and current, and the accurateness and longlivity.

**✅Selected: ANKO A200SX** but with the promise to implement Sequential Logic (turning off motors to read sensors) and limit the motor current as far as feasible (1A ?).  
- *Overbuilt for Precision:* The NEMA 17 stepper (ANKO) has massive "holding torque." In dosing, this prevents the rollers from "back-creeping" when the pump is off, ensuring the pH Down doesn't slowly leak into the tank.
- *Thermal Headroom:* By running at 60% of its rated current, active cooling isn't neede for the stepper driver.
- *The "Silent Read" Advantage:* Since we'll not read pH/EC while pumping, we eliminate the biggest risk of the ANKO (chopper noise). The code simply disables the motor drivers (ENN = HIGH) before requesting data from the ADM3260 islands.

Running the motor at 1A RMS (~60% of its 1.7A rating) will significantly reduce the electromagnetic field strength and current ripples that contribute to EMI. However, because torque in stepper motors is directly proportional to current, you should expect roughly **40-45% less torque** than the motor’s peak capability.

Recommendations:
- **Test under Load:** Verify that 1A provides enough torque to move the fluid through your specific tubing at your required pressure.
- **Adjust Microstepping:** If the motor vibrates or stalls at 1A, increasing microstepping (e.g., to 1/8 or 1/16) can sometimes help smooth out the motion and prevent resonance-related stalls at lower current levels. 

### 4. Dosing Pump Driver Selection

Requirements:
- 24V pump voltage
- 3.3V I/O voltage
- UART interface, ideally shared between drivers

#### 4.1. Parts Considered

Feature         | ✅[Trinamic TMC2209](https://www.analog.com/en/products/tmc2209.html) | [Trinamic TMC2225](https://www.analog.com/media/en/technical-documentation/data-sheets/TMC2225_datasheet_rev1.14.pdf)
----------------|---------------------|------------------|
Pump voltage    | 24V supported       | 24V supported    |
I/O voltage     | 3.3V supported      | 3.3V supported   |
Current         | 2.0A RMS max        | ❌1.4A RMS max   |
UART            | Yes (shared)        | Yes (shared)     |
Near-silent op  | StealthChop2        | StealthChop2     |
Fault detection | StallGuard4         | unknown          |

**✅Selected: Trinamic TMC2209** because the TMC2225 can't drive the 1.7A current needed for the ANKO A200SX pump.

#### 4.2. Limit EMI Noise and Current

To reduce EMI noise and current, choose a **target operating range of 60–70%** of the pumps rated **I<sub>RMS</sub>** .

This current should be limited in hardware and firmware:
1. Use the V<sub>REF</sub> input of the TMC2209 to set a hard limit to 90% of the 1.7 A<sub>RMS</sub> motor current. This is likely still overkill, but will limit the current further in firmware. 
2. Set `IHOLD_IRUN` register using firmware to further lower the current to a practical level Configure `IHOLD=0` (zero standstill current) via UART, so sense resistors and motor carry no current between dosing events.

---


### 5. Main Reservoir Level System

Tight water level control is less about volume and more about chemical stability.
- When **water evaporates**, it leaves behind minerals, salts, and nutrients. This can lead to osmotic shock, nutrient burn in plants. An Auto Top-Off (ATO) keeps the ratio of water-to-solids constant.
- Smaller volumes of water are more susceptible to rapid **pH swings**. Maintaining a consistent reservoir volume provides a larger "thermal and chemical mass," which acts as a buffer against rapid fluctuations caused by plant uptake or waste breakdown.
- Most pumps are not designed to **run dry**.

Requirements:
- **User confirmation**: System requests approval from user before filling
- **Timeout**: Maximum fill time prevents overflow if sensor fails
- **Safety**: Float switches provides hardware backup cutoff
- **Valve type**: 24V NC (normally closed) solenoid - fails safe (closed)
- **Hysteresis** in driving the OTA valve. If you triggered a refill the second the water dropped 1mm, your pump would "chatter" (rapidly flip on/off).

Purpose:
- A **continuous depth sensor** measure the liquid height to track consumption and guide the automatic top-off (ATO) feature
- Independent sensors for **high and low alarms** provide a safety feature in case the ATO system fails. The high alarm disables the auto top-off feature.  The low alarm disables the main pump so it can't run dry.


#### 5.1 Continuous Depth Sensor Selection


This sensors provide a real-time measurement of the liquid height, which is ideal for tracking consumption and guiding the auto top-off feature.

##### 5.1.1. Technologies Considered

Feature  | LiDAR | Capacitive | Ultrasonic | Hydrostatic
---------|-------|------------|------------|------------
Contact | Non-contact | ❌Contact | Non-contact | ❌Contact
Precision | Very High (mm) | High (±0.2%) | Moderate (±0.25") | High (±0.1%)
Foam/Vapor | Unaffected | Unaffected | Poor | Unaffected
Blind Spot | 10 cm | 0 cm | ❌20 cm | 0 cm
Best For | Clean liquids | Viscous/Sticky fluids | General water/Chemicals | Deep tanks/Turbulence
Example Product | Benewake TF-Luna | uFire Capacitive | JSN-SR04T | DFRobot Gravity
Interface | I2C/UART | I2C | GPIO | ❌Analog
Approx. Price | \$25 – \$40 | \$35 – \$50 | \$10 – \$15 | ❌\$60 – \$80

**✅Selected: LiDAR** since it stays dry, so no maintenance-free. The 10 cm head room is acceptable since it only needs to measure the level up to the high alarm float sensor. Capacitance and hydro static were rejected since mineral buildup eventually affects these sensors.  Ultrasonic is rejected, since it needs excessive head room.

##### 5.1.2. Parts Considered

Feature         | ST VL53L1X<sup>[1](https://www.adafruit.com/product/3967)</sup> | Benewake TF-Luna<sup>[2](https://www.robotshop.com/products/benewake-tf-luna-8m-lidar-distance-sensor)</sup> | Benewake TFmini-S<sup>[3](https://www.robotshop.com/products/benewake-tfmini-s-micro-lidar-module-i2c-12m)</sup>
----------------|------------------|------------------|------------------
Range           | 0.04-4 m         | 0.1-8 m          | 0.1-12 m
Interface       | I2C              | I2C/UART         | I2C/UART
Supply Voltage  | 2.6V – 5.5V      | 3.7V – 5.2V      | 4.5V – 6.0V
I/O Logic Level | 3.3V / 5V        | 3.3V             | 3.3V
Form Factor     | ❌Breakout board | Compact module   | Ruggedized module
Price           | $14.95           | $22.26           | ❌$48.10

**✅Selected: Benewake TF-Luna** because if its housing and price.  Rejected the ST VL53L1X since it is an unhoused breakout board.  Rejected the Benewake TFmini-S because if its price.


#### 5.2 High/Low Alarm Sensor Selection


Goals:
- A low level float switch keeps keep main pump from running dry.
- A high level float switches provides a hardware guard against both overfilling the reservoir.

Requirements
- The switches should disable the driving of the MOSFETs that control the ATO feature and main pump.
- A normally closed switch is less likely to fail.
- Horizontal side-mount, so the top of the reservoir can be opened for inspection. Also the sensing level is fixed by where you drill the hole — no float travel calculation, no ambiguity. 

##### 5.2.1. Parts Considered

Feature     | ✅Flowline LH25-1101
------------|----------------------
Contact     | SPST dry reed, selectable NO/NC by float orientation
Material    | Polypropylene (PP) body and float
Mount       | 1/2" NPT side-wall
Accuracy    | ±5mm in water
IP rating   | IP68
Wire        | 2' (61cm), 2-conductor, 22 AWG

**✅Selected: Flowline LH25-1101 (Horizontal, PP)**. No alternatives were considered.


### 5.3 Automatic Top-Off (ATO) Selection


Requirements
- 24V to match system power rail
- Normally Closed (NC), so it is fail-safe: valve closes on power loss
- 0-0.8 MPa (0-116 PSI), the typical municipal water pressure
- Brass body, EPDM/NBR seal, so it is food-safe and corrosion resistant

#### 5.1.1 Parts Considered

Feature | ✅[DIGITEN DC 24V 1/4" NC](https://www.amazon.com/DIGITEN-Solenoid-Reverse-Osmosis-System/dp/B00X6RAHMU) | [US Solid JFSV00068](https://ussolid.com/products/u-s-solid-electric-solenoid-valve-1-4-24v-dc-solenoid-valve-stainless-steel-body-normally-closed-viton-seal-html?_pos=6&_fid=d5a36750a&_ss=c) | [US Solid MSV00027](https://ussolid.com/products/u-s-solid-motorized-ball-valve-1-4-stainless-steel-electrical-ball-valve-with-full-port-9-24-v-ac-dc-2-wire-auto-return-html)
----------------|-------------------------|-------------------|--------------------
Voltage         | 24V DC                  | 24V DC            | 9-24V AC/DC
Body            | Plastic                 | Stainless steel   | Stainless steel
Default state   | Normally Closed         | Normally Closed   | Normally Closed
Port            | 1/4" Quick Connect      | 1/4" NPT thread   | 1/4" NPT thread
Current         | 0.2A                    | 0.6A              | 0.2A (when moving)
Max pressure    | 0.8 MPa (116 PSI)       | 0.7 MPa (101 PSI) | 1.0 MPa (145 PSI)
Design          | Solonoid orifice        | Solonoid orifice  | Ball valve
Response time   | <1s                     | <1s               | 3-5s
Drinking safe   | Yes                     | Yes               | Yes
Cost            | \$10                    | \$30              | $25

**✅Selected: DIGITEN DC 24V 1/4" NC** for its price.


---


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








---


### 7. Probes

Highly reliable and continuous monitoring is essential for maintaining optimal pH (5.5–6.5) and EC (0.8–2.5 mS/cm) levels. pH and EC readings drift significantly as water temperature changes.

Why this is critical:
- pH Drift: pH readings change by about 0.03 pH per 1°C deviation from the 25°C calibration point.
- EC Drift: Conductivity is even more sensitive, changing by roughly 2% per 1°C. Without this link, a reservoir warming up by 5°C would report a 10% error in nutrient concentration.

To link your EZO-RTD to your pH and EC circuits, you must use a "read-then-write" loop. Atlas EZO circuits do not "talk" to each other directly on the I2C bus; your microcontroller must act as the bridge by reading the temperature and then sending it to the other sensors using `T,n` commands or `RT,n` on newer circuits.

Requirements:
- Suited continuous immersion in a mineral-heavy nutrient solution (high salts/calcium).
- Provide high accuracy and resist electrical noise from pumps.
- No need for custom analog filtering or voltage dividers.

#### 7.1. Parts Considered

##### 7.1.1. pH Probes

Feature     | Atlas Scientific ENV-40-pH (gen3) | DFRobot pH Sensor Kit (v2) | ✅BlueLab PROBPH
------------|-------------------------------|--------------------|------------------------
Class       | Laboratory grade                | Budget-friendly    | Industry grade
Interface   | I2C/UART                        | ❌Analog           | I2C/UART
I/O voltage | 3.3 - 5V                        | 3.3 - 5.5V         | 3.3 - 5V
Range       | 0 – 14 pH                       | 0 – 14 pH          | 0 – 14 pH
Accuracy    | ±0.002 pH (ultra-high)          | ±0.1 pH (standard) | ±0.1 pH (standard)
Lifespan    | ~1-1.5 yr (double junction)     | ❌>0.5 years       | ~1.5 yr (double junction)
Maintenance | ❌Frequent cleaning/calibration | unknown            | set-and-forget
Immersion   | Indefinite                      | ❌Limited          | Indefinite
Price       | \$85 + \$46 for EZO-pH          | \$30 + ADC         | \$99 + \$46 for EZO-pH

A double junction, adds an extra physical barrier that prevents nutrient salts and heavy minerals from "poisoning" the internal reference silver wire. This makes it far superior for 24/7 immersion in "dirty" or high-EC water.

**✅Selected: BlueLab PROBPH** because no glass bulb like the Atlas, and doesn't require frequent cleaning and re-calibration. The DFRobot is engineerd for a different level of "continuous" use according to user report and needs a external ADC, as the ESP32’s native ADC is often non-linear. Note that while Bluelab states an average lifespan of 18 months for their pH probes. Many users report having to replace them more frequently in 24/7 submerged environments. 

##### 7.1.2. EC Probes

The nutrient range typical in hydroponics is 0.8 – 2.5 mS/cm.

Feature     | Atlas Scientific EC-K1.0  | DFRobot Gravity (K=1) | ✅BlueLab PROBPCEC
------------|---------------------------|---------------------|------------------------------
Class       | Laboratory grade          | Budget-friendly     | Industry grade
Interface   | I2C/UART                  | ❌Analog            | I2C/UART
I/O voltage | 3.3 - 5V                  | 3.3 - 5.5V          | 3.3 - 5V
Range       | 0.07 – 500,000+ µS/cm     | 1 – 15,000 µS/cm    | 0 – 10,000 µS/cm
Accuracy    | ±2% of reading            | ±5% F.S.            | ±100 µS/cm at 2,770 µS/cm
Lifespan    | ~10 yr                    | >0.5 yr             | High (commercial)
Maintenance | Monthly soak              | Weekly              | Monthly scrub
Immersion   | Indefinite                | ❌Limited           | Indefinite
Price       | ❌\$140 + \$68 for EZO-EC | \$70 + external ADC | $72 + \$68 for EZO-EC

**✅Selected: BlueLab PROBPCEC** because is cheaper and easier to clean compared to the Atlas that uses a "sensing cavity design" that is hard to scrub.

##### 7.2.3. Temperature Probes

The Bluelab Temperature Probe was included because it is the industry standard for durability in commercial hydroponic reservoirs. While the Atlas Scientific PT-1000 is more accurate for laboratory use, the Bluelab probe is favored by professional growers because its housing is specifically engineered to withstand "24/7" immersion in harsh, mineral-heavy nutrient solutions without drifting or corroding.

Feature     | ✅Atlas Scientific PT-1000 | DFRobot Gravity PT1000 | BlueLab PROBTEMP
------------|--------------------------|----------------------|-------------------------
Class       | Laboratory grade         | Industry grade       | Industry grade
Sensor type | Class A platinum RTD     | Class A platinum RTD | Thermistor / RTD Hybrid
Interface   | I2C/UART                 | ❌Analog             | ❌Analog
I/O voltage | 3.3 - 5V                 | 3.3 - 5.0V           | 3.3 - 5V
Range       | -200 - 850°C             | -30 - 350°C          | 0 - 50°C (optimized)
Accuracy    | ±(0.15 + 0.002*T)°C      | ±0.3 - 0.6°C         | ±1.0°C
Lifespan    | ~10 yr                   | >0.5 yr              | Industrial grade
Maintenance | Monthy wipe              | Periodic soak        | Set-and-forget
Immersion   | Indefinite               | ❌Limited            | Indefinite
Price       | \$24 + \$36 for EZO-RTD  | \$59 + external ADC  | \$60 + external ADC

**✅Selected: Atlas Scientific PT-1000** because it has a long lifespan and supports a I2C interface when combined with the Atlas EZO-RTD.

### 7.3. Probe Isolation Strategy

In a mineral-heavy reservoir, the "hidden" enemy is **ground loops** causing probe interference. Since water is conductive, multiple probes (pH, EC) in the same tank act like batteries, leaking small currents that distort each other's readings.

Note that the EZO-RTD does not require isolation; temperature measurements are resistance-based and immune to the electrical noise that affects electrochemical probes.

To prevent this, one can use the professional Isolated I2C approach or a Time Division Multiplexing (TDM) hack.

#### Technologies considered

Feature      | ✅Isolated I2C (EZO Style)     | TDM / MOSFET Switching
-------------|--------------------------------|-----------------------
Philosophy   | Continuous, simultaneous data  | One sensor at a time (sequential)
Hardware     | I2C and DC/DC isolator         | MOSFETs + ADS1115 (16-bit ADC)
Ground Loops | Eliminated by physical air gap | Reduced, but still risky
Complexity   | Low (Plug and Play).           | High (complex wiring & timing)
Accuracy     | Highest (no interference)      | Moderate (switching noise/latency)
Cost         | ~$40–$60 for all channels      | ~$15 for all channels

**✅Selected: Isolated I2C**, because chemical probes (especially pH) require a constant charge to remain stable. Turning them off/on frequently causes "reading drift" and significantly slows down your data refresh rate.

#### Parts considered

The Atlas Scientific ISO-I2C Brand Isolator primarily uses the ADM3260 chip from Analog Devices. Older or USB versions of their isolated carrier boards previously utilized a Silicon Labs SI8600 bidirectional I2C isolator and an RFM-0505 or Mornsun B0505S isolated DC-DC converter. 

Feature    | ADM3260          | Atlas ISO-I2C Board | uFire / DFRobot Isolators
-----------|------------------|---------------------|--------------------------
Footprint  | IC and glue      | Mezzanine board     | Mezzanine board
Difficulty | Layout sensitive | Plug & play         | Plug & play
Price      | \$5              | \$32                | \$20

Prices are per channel



---


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
