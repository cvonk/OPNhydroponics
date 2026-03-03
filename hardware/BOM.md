# Bill of Materials (BOM)

## Summary

| Category | Cost |
|----------|------|
| Microcontroller | $8 |
| Power Management | $15 |
| Water Quality Sensors (Atlas Scientific) | ~$397 |
| Environmental Sensors | $20 |
| Actuators (pumps + ATO valve) | $75 |
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
| 1 | 12V DC pump | Brushless, 800L/H min | Amazon/AliExpress | $15 |

Recommended models:
- Generic brushless 12V submersible
- AUBIG DC40E-1250 (12V, 500L/H, 5m head)

### Dosing Pumps

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 3-4 | Peristaltic pump 12V | ~100mL/min, 3mm tubing | AliExpress | $12 ea |

Required: pH Down, Nutrient A, Nutrient B (3 pumps)
Optional: pH Up (if your system tends toward acidic - most don't need this)

Recommended:
- Kamoer KFS (quality, $20 ea)
- Generic 12V peristaltic (budget, $6 ea)

### ATO Solenoid Valve

| Qty | Part | Description | Source | Price |
|-----|------|-------------|--------|-------|
| 1 | 12V NC Solenoid Valve | 1/2" normally closed, food safe | Amazon/AliExpress | $8 |

Recommended:
- US Solid 12V NC solenoid (food grade)
- Must be NC (normally closed) for fail-safe operation

**Actuators Subtotal: ~$75**

---

## Pump/Valve Driver Components

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 1 | IRLR2905 | N-MOSFET 55V/42A, DPAK | Main pump driver (Q1) | — |
| 7 | AO3400A | N-MOSFET 30V/5.7A, SOT-23 | Dosing pumps + ATO valve (Q2–Q8) | — |
| 2 | MMBT3904 | NPN transistor, SOT-23 | Float switch hardware cutoffs (Q9, Q10) | $0.05 ea |
| 8 | 10kΩ resistor | Gate pull-down | 0805 | $0.05 ea |
| 8 | 100Ω resistor | Gate series | 0805 | $0.05 ea |
| 2 | 4.7kΩ resistor | NPN base resistor (Q9, Q10) | 0805 | $0.05 ea |

**Subtotal: ~$6**

---

## Connectors

| Qty | Part | Description | Notes | Price |
|-----|------|-------------|-------|-------|
| 2 | Female header 1×20 | 2.54mm pitch | DevKit mounting | $0.50 ea |
| 1 | Phoenix MSTB 2.5/2-ST-5.08 | 5.08mm pluggable terminal | Main pump (header + plug) | $0.50 |
| 5 | Phoenix MC 1.5/2-ST-3.5 | 3.5mm pluggable terminal | Dosing pumps ×4 + ATO valve (header + plug) | $0.40 ea |
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

## Optional Accessories

| Qty | Part | Description | Price |
|-----|------|-------------|-------|
| 1 | SSD1306 OLED 0.96" | Local status display | $4 |
| 1 | WS2812B LED | Status indicator | $0.50 |
| 1 | Buzzer (passive) | Alarm notification | $0.50 |
| 1 | 12V 5A power supply | Mean Well or equiv | $10-20 |
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
