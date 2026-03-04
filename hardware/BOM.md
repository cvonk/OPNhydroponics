# Bill of Materials (BOM)

## Summary

| Category | Cost |
|----------|------|
| Microcontroller | $8 |
| Power Management | $15 |
| Water Quality Sensors (Atlas Scientific) | ~$397 |
| Environmental Sensors | $20 |
| Actuators (pumps + ATO valve) | ~$150 |
| Connectors & PCB | $40 |
| Enclosure | $25 |
| **Total** | **~$468** |

---

## Microcontroller Module

| Qty | Part | Description | Budget Source | Price |
|-----|------|-------------|---------------|-------|
| 1 | ESP32-C6-DevKitC-1-N8 | WiFi 6 + BLE 5 devkit, 8MB flash, USB-C | Digikey, Mouser | $10-15 |

Note: Using DevKit instead of bare module - includes USB-C, antenna, and boot/reset buttons. Mounts via 2×20 pin headers.

---

## Power Management

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 1 | TPS62933DRLR | 12V→5V synchronous buck, 3A, SOT583 | Logic power | — |
| 1 | AMS1117-3.3 | 5V→3.3V LDO, 1A | ESP32 power | $0.50 |
| 1 | B5819W | Schottky diode, reverse protection | Or SS54 | $0.20 |
| 1 | SI2301 | P-MOSFET, reverse polarity | SOT-23 | $0.30 |
| 2 | 100µF/25V | Electrolytic capacitor | Input/output | $0.50 |
| 4 | 10µF/25V | Ceramic capacitor | Decoupling | $0.40 |
| 1 | PTC fuse 5A | Resettable fuse | Protection | $0.50 |

**Subtotal: ~$5-10**

---

## Sensors

### Water Quality (Atlas Scientific - Selected)

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | Atlas Scientific EZO-pH (EZO-PH) | pH circuit, I2C 0x63 | DigiKey [16003108](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-PH/16003108) | $51.27 |
| 1 | Atlas Scientific EZO-EC (EZO-EC) | Conductivity circuit, I2C 0x64 | DigiKey [16003000](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-EC/16003000) | $82.25 |
| 1 | Atlas Scientific EZO-RTD (EZO-RTD) | Temperature circuit, I2C 0x66 | DigiKey [16003139](https://www.digikey.com/en/products/detail/atlas-scientific/EZO-RTD/16003139) | $38.75 |
| 1 | Atlas pH Probe Gen 3 (ENV-40-pH) | Lab grade, double-junction, BNC | Atlas Scientific | $84.99 |
| 1 | Atlas EC Probe K=1.0 (ENV-40-EC-K1.0) | Conductivity probe, ±2%, BNC | Atlas Scientific | $139.99 |
| 1 | Atlas PT-1000 RTD Probe (ENV-40-TMP) | Temperature probe, BNC | Atlas Scientific | — |

**Water Quality Subtotal: ~$397**

Note: Atlas Scientific probes include calibration data and have better longevity than budget alternatives.

### Environmental

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | BME280 module | Temp/humidity/pressure | Amazon/AliExpress | $4 |
| 1 | BH1750 module | Light intensity (lux) | Amazon/AliExpress | $2 |
| 1 | HC-SR04 | Ultrasonic distance | Amazon/AliExpress | $2 |
| 2 | Float switch | Water level, vertical | Amazon | $3 ea |

**Sensors Subtotal: $80-180**

---

## Actuators

### Main Circulation Pump

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | AUBIG DC40-1250 | Brushless DC 12V, 500 L/H, 5m head, ~1.0A, barbed fittings | [Amazon (B076QB7P2V)](https://www.amazon.com/dp/B076QB7P2V) / [eBay](https://www.ebay.com/p/1411964986) | ~$20–25 |

**Selected model: AUBIG DC40-1250** — barbed fittings, 12V, 500 L/H, 5m head, ~1.0–1.2A

- Amazon ASIN B076QB7P2V (also B008F29MYA); also available on eBay if out of stock
- DC40E-1250 (NPT threads variant) is currently in short supply — use barbed DC40-1250 instead
- Avoid generic unbranded brushless pumps — flow rate and current draw are often misrepresented

### Dosing Pumps

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 3 | Kamoer KAS SF-12V | Stepper peristaltic, 12V, 0.75A, 3mm ID silicone, 3-rotor | [Amazon](https://www.amazon.com/peristaltic-Stepper-Kamoer-Variable-OD%EF%BC%8C5-84ml/dp/B094QHDSQL) | ~$25–35 ea |

Required: pH Down (U5), Nutrient A (U6), Nutrient B (U7) — 3 pumps total.
Order **without** bundled drive board; TMC2209 replaces it.
BPT tube recommended over silicone for longer chemical resistance life.

### ATO Solenoid Valve

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | 12V NC Solenoid Valve | 1/2" normally closed, food safe | Amazon/AliExpress | $8 |

Recommended:
- US Solid 12V NC solenoid (food grade)
- Must be NC (normally closed) for fail-safe operation

**Actuators Subtotal: ~$150** (3× KAS SF-12V stepper pumps dominate cost)

---

## Pump/Valve Driver Components

### Main Pump + ATO Valve (MOSFET)

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 1 | IRLR2905 | N-MOSFET 55V/42A, DPAK | Main pump driver (Q1) | — |
| 1 | AO3400A | N-MOSFET 30V/5.7A, SOT-23 | ATO solenoid valve (Q8) | — |
| 2 | MMBT3904 | NPN transistor, SOT-23 | Float switch hardware cutoffs (Q9, Q10) | $0.05 ea |
| 2 | 10kΩ resistor | Gate pull-down (Q1, Q8) | 0805 | $0.05 ea |
| 2 | 100Ω resistor | Gate series (Q1, Q8) | 0805 | $0.05 ea |
| 2 | 4.7kΩ resistor | NPN base resistor (Q9, Q10) | 0805 | $0.05 ea |

### Dosing Pump Stepper Drivers (TMC2209)

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 3 | TMC2209 | Stepper driver, QFN-28, 2A RMS | U5 pH Down, U6 Nut A, U7 Nut B | ~$2 ea |
| 6 | 220mΩ resistor | RSENSE, 1% tol, 0805 | 2 per driver (BRA, BRB) | $0.10 ea |
| 3 | 100nF capacitor | VM local bypass, 0402 | 1 per driver | $0.05 ea |
| 3 | 47µF / 25V electrolytic | VM bulk cap | 1 per driver | $0.20 ea |
| 3 | 100kΩ resistor | PDN_UART pullup to 3.3V | 1 per driver, 0402 | $0.05 ea |
| 3 | 4.7kΩ resistor | VREF divider high-side | 1 per driver, 0402 | $0.05 ea |
| 3 | 1kΩ resistor | VREF divider low-side | 1 per driver, 0402 | $0.05 ea |

**Subtotal: ~$15**

---

## Connectors

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 2 | Female header 1×20 | 2.54mm pitch | DevKit mounting | $0.50 ea |
| 1 | Phoenix MSTB 2.5/2-ST-5.08 | 5.08mm pluggable terminal | Main pump (header + plug) | $0.50 |
| 3 | JST S6B-PH-K-S | PH 2.0mm 6-pin right-angle TH header | Dosing stepper motors ×3 — mates with PHR-6 on pump cable (VCC/GND/A+/A−/B+/B−) | $0.20 ea |
| 1 | Phoenix MC 1.5/2-ST-3.5 | 3.5mm pluggable terminal, 2-pin | ATO solenoid valve | $0.40 |
| 1 | Pluggable terminal 2P | 3.5mm pitch | 12V power input (header + plug) | $0.50 |
| 3 | BNC panel mount female | For probes | pH/EC/RTD | $2 ea |
| 4 | JST-PH 4P | I2C sensors | Qwiic compat | $0.20 ea |
| 2 | JST-XH 2P | Float switch connectors (FLOAT_LOW + FLOAT_HIGH) | | $0.15 ea |
| 1 | JST-XH 4P | Ultrasonic | | $0.20 |
| 1 | 4-pin header | OLED display | 2.54mm | $0.20 |

**Subtotal: ~$11**

---

## PCB Fabrication

| Item | Description | Source | Price |
|------|-------------|--------|-------|
| PCB | 100×80mm, 2-layer, 5pcs | JLCPCB | $5-10 |
| Assembly | Optional SMT assembly | JLCPCB | $15-30 |

**Subtotal: $5-40**

---

## Enclosure

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | ABS enclosure | 158×90×60mm, IP65 | Amazon/AliExpress | $8-15 |
| 6 | Cable gland PG7 | Waterproof cable entry | Amazon | $0.50 ea |
| 3 | BNC bulkhead | Panel mount adapters | Amazon | $2 ea |

**Subtotal: $15-25**

---

## Power Supply

System requires **12V DC, ≥5A**. Peak load estimate: main pump (1.2A) + 3× dosing pumps
(0.75A each, only when stepping) + ATO valve (0.5A) + logic (0.5A) ≈ 4.5A peak, with
all loads simultaneous being unlikely. 5A rated supply provides adequate headroom; 6A
recommended for margin.

| Model | Output | Efficiency | Form Factor | Notes | Price |
|-------|--------|------------|-------------|-------|-------|
| **Mean Well LRS-75-12** ★ | 12V / 6A (75W) | 89% | Enclosed metal, 30mm low-profile | Convection cooled, −30 to +70°C, widely available | ~$18–25 |
| Mean Well LPV-60-12 | 12V / 5A (60W) | 83% | IP67 plastic, 162×43×32mm | Designed for LED strips; UL1310 Class 2 | ~$20–30 |
| Mean Well MDR-60-12 | 12V / 5A (60W) | — | DIN rail | Compact DIN mount for panel/cabinet builds | ~$25–35 |
| Mean Well HDR-60-12 | 12V / 4.5A (54W) | 91% | DIN rail | **Marginal** — only 4.5A, avoid | ~$20–30 |

**Recommended: Mean Well LRS-75-12** — 6A provides a comfortable 1.5A headroom over
worst-case peak load, enclosed metal case dissipates heat passively, and 30mm profile
fits standard enclosures. Available from DigiKey, Mouser, and Amazon.

**IP67 alternative: LPV-60-12** — Use in humid environments where the supply is mounted
inside the grow enclosure. 5A is sufficient if loads are not fully simultaneous. Note:
LPV series is designed as an LED driver (constant voltage); it works fine as a general
12V supply but lacks remote sense.

**Avoid HDR-60-12** — 4.5A output is marginal; derating at elevated temperature reduces
it further.

---

## Optional Accessories

| Qty | Part | Description | Price |
|-----|------|-------------|-------|
| 1 | SSD1306 OLED 0.96" | Local status display | $4 |
| 1 | WS2812B LED | Status indicator | $0.50 |
| 1 | Buzzer (passive) | Alarm notification | $0.50 |
| 4 | Silicone tubing 3mm | Dosing pump tubing, 1m each | $2/m |
| 1 | Calibration solutions | pH 4, 7, 10 + EC standards | $15-25 |

---

## Recommended Vendors

| Vendor | Best For | Notes |
|--------|----------|-------|
| LCSC | Components, ESP32 modules | Cheap shipping to CN/EU/US |
| Digikey/Mouser | Quality components | Fast US shipping |
| Atlas Scientific | Water quality sensors | Premium quality |
| DFRobot | Budget sensors | Good documentation |
| AliExpress | Modules, enclosures | 2-4 week shipping |
| Amazon | Quick delivery items | Higher prices |
| JLCPCB | PCB fab + assembly | Best value for prototypes |

---

## Purchasing Notes

1. **Start with DevKit**: Use ESP32-C6-DevKitC for initial prototyping before committing to custom PCB.

2. **Sensor Quality Matters**: For pH and EC, cheap sensors drift quickly. Budget sensors are OK for learning but plan to upgrade.

3. **Probe Lifespan**:
   - pH probes: 1-2 years typical
   - EC probes: 2-5 years
   - RTD probes: 5+ years (no consumable elements)

4. **Tubing**: Use only food-grade silicone for dosing pumps. Cheap tubing degrades with nutrients/acids.

5. **Power Supply**: Don't skimp on the 12V supply. A quality Mean Well supply prevents noise issues.
