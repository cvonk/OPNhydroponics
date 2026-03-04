# Dosing Pump Guide

## Dosing Requirements — 50-gallon NFT System

**System volume:** 50 US gallons = 189 L

---

### Batch Dosing

Performed on a fresh reservoir fill or after a full system flush.

#### Nutrients (Part A and Part B)

Standard hydroponic 2-part concentrate at full strength: **5 mL/gallon** per part.

| Part | Volume | Notes |
|------|--------|-------|
| Nutrient A | 250 mL | Calcium + micronutrients |
| Nutrient B | 250 mL | Phosphorus + potassium |

Dose A and B sequentially (never premix concentrates — calcium precipitation risk).

At typical pump speed (30 mL/min): **8–9 min per part** → ~17 min total.
At max speed (70 mL/min): **3.6 min per part** → ~7 min total.

#### pH Down (Phosphoric Acid Concentrate)

pH target: 5.8–6.2. Typical tap water pH: 7.0–7.5.

| Water Hardness | Dose Rate | Volume for 50 gal |
|----------------|-----------|-------------------|
| Soft (<50 ppm alkalinity) | 0.5–1 mL/gal | 25–50 mL |
| Moderate (50–150 ppm) | 1–2 mL/gal | 50–100 mL |
| Hard (>150 ppm) | 2–4 mL/gal | 100–200 mL |

At 30 mL/min: **1.7–6.7 min** depending on water hardness.

⚠ Always dose pH Down **after** nutrients. Add in small increments (25 mL), wait
15 min for mixing, re-measure. Repeat until target is reached. Do not pre-calculate
and dose the full amount in one shot — overshooting pH is difficult to reverse.

---

### Maintenance Dosing

Performed daily or triggered by sensor readings. Much smaller volumes.

#### Nutrients (EC-based correction)

Cause: ATO adds pure/RO water → dilutes nutrients → EC drops.

Daily plant water consumption for a 50-gallon NFT system growing leafy greens/herbs:
**0.5–2 gallons/day** (100–750 mL/day depending on plant load and environment).

Each gallon of ATO water added requires ~5 mL of each nutrient part to restore
concentration, giving:

| ATO Rate | Nutrient A/day | Nutrient B/day |
|----------|---------------|---------------|
| 0.5 gal/day (light load) | ~2.5 mL | ~2.5 mL |
| 1.0 gal/day (typical) | ~5 mL | ~5 mL |
| 2.0 gal/day (high load) | ~10 mL | ~10 mL |

At 30 mL/min: **5–20 seconds per part** at maintenance rates.

In practice: trigger EC correction when measured EC drops >0.1 mS/cm below
setpoint and ATO volume since last dose is known.

#### pH Down (pH-triggered correction)

Cause: pH rises 0.3–0.7 units/day in active NFT systems (plant root CO₂ excretion,
preferential uptake of anions shifts solution pH upward).

Correction dose to drop pH by 0.1 unit in 189 L:

| pH Rise/Day | pH Down/Day | Notes |
|-------------|-------------|-------|
| 0.3 units (low) | 5–10 mL | Soft water, low plant load |
| 0.5 units (typical) | 10–20 mL | Moderate water, moderate load |
| 0.7 units (high) | 20–35 mL | Hard water or high root density |

At 30 mL/min: **10–70 seconds** at maintenance rates.

Control logic: dose pH Down only when pH > 6.2, in 2 mL increments, with 10-min
mixing intervals between increments to avoid overshoot.

---

## Pump Selection

### Nutrients (Part A and Part B)

Low chemical aggression — silicone tubing acceptable, Santoprene rollers OK.

| Model | Voltage | Flow Range | Tube ID | Notes |
|-------|---------|------------|---------|-------|
| **Kamoer KAS SF-12V** (current) | 12V (24V VM via TMC2209) | 11.5–71.5 mL/min | 3mm ID | 3-rotor stepper; order without drive board |
| Kamoer KCM-ST | 12–24V | ~0.5–35 mL/min | 2–4mm | Compact, lower max flow; verify datasheet |
| Anko M025 Series | 12–24V | ~0.5–25 mL/min | 2.5mm | High precision micro-dosing; verify datasheet |

For maintenance nutrient doses (2.5–10 mL), any of these is adequate.
For batch nutrient doses (250 mL), the KAS SF-12V at 70 mL/min (~3.5 min) is faster
than the KCM-ST or Anko M025 — prefer KAS SF-12V or a two-stage approach (fast
fill + slow trim).

**Tubing:** Silicone 3mm ID is acceptable for nutrient A/B. Santoprene rollers OK.
Replace silicone tubing every 6–12 months (wear at rotor contact points).

---

### pH Down (Concentrated Phosphoric Acid)

**⚠ Silicone is NOT acceptable for pH Down.** Concentrated phosphoric acid (85%,
as in commercial pH Down) causes silicone tubing to swell, delaminate, and fail
within weeks. This contaminates the reservoir and jams the pump head.

**Required: Pharmed BPT (Saint-Gobain)** — thick-walled peristaltic tubing with
superior acid resistance. Industry standard for peristaltic pumps handling acids,
aggressive solvents, and pharmaceutical fluids.

| Property | Silicone | Pharmed BPT |
|----------|----------|-------------|
| Phosphoric acid (85%) | ❌ Fails in weeks | ✅ Long-term compatible |
| Gas permeability | High | Low |
| Pressure rating | Low | High |
| Service life (acid) | 1–4 weeks | 6–18 months |
| Cost | Low | 2–3× silicone |

**Roller/head material:** Specify **EPDM or Viton rollers**. Standard Santoprene
rollers stiffen and crack with prolonged acid exposure. Viton offers superior
resistance; EPDM is acceptable for phosphoric/citric acid concentrations typical
in commercial pH Down.

| Model | Voltage | Flow Range | Tube ID | Chemical Rating | Notes |
|-------|---------|------------|---------|-----------------|-------|
| **Kamoer KPHM100-ST** | 12–24V | TBD — verify datasheet | 3mm ID BPT | Chemical resistant head | Verify roller material; specify BPT tube |
| Anko M045 Series | 12–24V | TBD — verify datasheet | 2.5–3mm | Chemical resistant | Specify EPDM/Viton rollers; verify |

⚠ Confirm roller material with supplier before ordering. Request Viton or EPDM
explicitly — default rollers on many pumps are Santoprene (NBR-based) which is
inadequate for concentrated acids.

**Pharmed BPT source:** Saint-Gobain direct, Cole-Parmer, or VWR (lab supply).
Order the correct ID (3mm) to match the pump head. BPT is not available on Amazon
in precise sizes reliably — use lab/industrial distributors.

---

## Driver

All pumps above are bipolar stepper motors. The **TMC2209** stepper driver applies
to all variants:

- VM: 4.75–29V (24V rail used)
- Current setpoint: 0.75A (RSENSE = 220mΩ, VREF = 0.58V, IRUN = 18)
- UART address: U5 (pH Down) = 0, U6 (Nutrient A) = 1, U7 (Nutrient B) = 2
- Dose accuracy: step count × tube displacement constant (~1 mL/rev for 3mm ID tube)
  calibrated once per tube installation; accurate until tube wear requires re-cal

---

## pH Down — Adaptive Dosing (PID Lite)

Fixed-volume dosing (e.g. always 5 mL) is inefficient: too small a dose when pH is
far from target (slow convergence), too large a dose when pH is near target (overshoot
risk). A simplified proportional controller achieves faster correction without
overshoot.

### Algorithm

```
error = pH_measured − pH_target          # positive = pH too high, need more acid

dose_mL = clamp(Kp × error, MIN_DOSE, MAX_DOSE)

if error > DEADBAND:
    dispense(dose_mL)
    wait(MIXING_TIME)                    # let solution homogenise before re-measuring
    re-measure pH
    repeat if still above target
```

### Tuning Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `pH_target` | 6.0 | Adjust per crop; 5.8–6.2 is typical NFT range |
| `Kp` | 1.33 mL / pH unit | Tune to water buffering capacity |
| `MIN_DOSE` | 0.1 mL | Minimum meaningful dose; limits pump noise |
| `MAX_DOSE` | 2.0 mL | Safety cap per cycle |
| `DEADBAND` | 0.05 pH | Ignore error smaller than probe noise floor |
| `MIXING_TIME` | 10–15 min | NFT: solution recirculates; allow full mix |

### Example Doses (Kp = 1.33)

| pH Measured | Error | Raw Dose | Clamped Dose |
|-------------|-------|----------|--------------|
| 7.5 | 1.5 | 2.0 mL | **2.0 mL** (at MAX_DOSE) |
| 6.8 | 0.8 | 1.1 mL | **1.1 mL** |
| 6.3 | 0.3 | 0.4 mL | **0.4 mL** |
| 6.2 | 0.2 | 0.27 mL | **0.27 mL** |
| 6.1 | 0.1 | 0.13 mL | **0.13 mL** |
| 6.05 | 0.05 | — | **skip** (within deadband) |

### Why Not Full PID

| Term | Verdict | Reason |
|------|---------|--------|
| **P** (proportional) | ✅ Use | Directly scales dose to error |
| **I** (integral) | ❌ Omit | Accumulates across mixing waits → overshoot on long corrections |
| **D** (derivative) | ❌ Omit | pH probe noise amplified by differentiation → erratic doses |

The proportional-only approach combined with the mandatory MIXING_TIME wait is
effectively a sampled proportional controller. Each dose-wait-measure cycle
is one control iteration. Integral windup and derivative noise are not concerns.

### Convergence Estimate (pH 7.5 → 6.0 in 50 gal)

Worst-case starting pH of 7.5, target 6.0 (error = 1.5), Kp = 1.33:

| Iteration | pH Before | Dose | pH After (estimated) |
|-----------|-----------|------|----------------------|
| 1 | 7.5 | 2.0 mL (capped) | ~7.0 |
| 2 | 7.0 | 1.33 mL | ~6.5 |
| 3 | 6.5 | 0.67 mL | ~6.2 |
| 4 | 6.2 | 0.27 mL | ~6.1 |
| 5 | 6.1 | 0.13 mL | ~6.05 |
| 6 | 6.05 | skip (deadband) | stable |

~5 iterations × 15 min mixing = **~75 min** to reach target from pH 7.5.
Compare to a fixed 0.5 mL dose: ~18 iterations = ~270 min for the same correction.

Kp should be re-tuned after initial installation since buffering capacity varies
significantly between water sources (soft vs hard water).

---

## Safety Watchdog Logic

### 1. Maximum Daily Dose Lockout

Track cumulative pH Down dispensed within a rolling 24-hour window. If the total
exceeds the threshold, halt further dosing and trigger an alert.

```
# Pseudocode
DAILY_LIMIT_ML = 20          # tune to system; ~10× normal daily maintenance dose

daily_total_ml += dose_ml    # accumulate on each dispense
if daily_total_ml >= DAILY_LIMIT_ML:
    lock_dosing(reason="daily pH Down limit exceeded")
    alert("pH Down limit: {daily_total_ml:.1f} mL dispensed today. Manual check required.")
    return                   # do not dispense further until operator resets
```

**Why 20 mL as a starting limit:**
Normal daily maintenance dose is 5–35 mL (see Dosing Requirements). A 20 mL default
is 1–4× typical daily use — strict enough to catch a runaway loop, loose enough not
to false-alarm on a hard-water day. Adjust after observing normal consumption over
the first week. Reset the accumulator at midnight or on a 24-hour rolling window.

**Alert channels:** Home Assistant notification, local OLED message, buzzer (if fitted).

### 2. No-Movement Sanity Check (Pump Fault Detection)

If pH does not decrease meaningfully after N consecutive doses, the pump is likely
dry-running, the tube has popped off, or the reservoir pH sensor is faulty.

```
# Pseudocode
MAX_NO_MOVE_DOSES = 3
MOVEMENT_THRESHOLD = 0.05    # minimum pH drop to count as "moved"

if abs(pH_before - pH_after) < MOVEMENT_THRESHOLD:
    no_move_count += 1
else:
    no_move_count = 0

if no_move_count >= MAX_NO_MOVE_DOSES:
    lock_dosing(reason="pump fault — no pH response after 3 doses")
    alert("pH unresponsive after 3 doses. Check pump tube, reservoir level, probe.")
```

**What this catches:**
- Tube disconnected from pump head or barb fitting
- Pump reservoir (acid bottle) empty
- Air bubble trapped in tube (especially after initial tube install)
- pH probe failure or dry probe (probe out of solution)

**What it does NOT catch:**
- Extremely high buffering capacity water that neutralises acid faster than expected
  → increase Kp or MAX_DOSE, or inspect water hardness
- Slow mixing in a large reservoir → increase MIXING_TIME

**Recovery:** operator must physically inspect and reset the lockout flag. Do not
auto-reset after a timeout — a silent auto-restart of a faulted acid pump is a safety
hazard.

### Watchdog State Summary

| Condition | Action | Reset |
|-----------|--------|-------|
| Daily dose > 20 mL | Lockout + alert | Manual operator reset |
| 3 doses, no pH movement | Lockout + alert | Manual operator reset |
| pH probe reads out of range (<2 or >12) | Do not dose | Auto-clears when probe reads valid |
| pH already at or below target | Skip dose | Auto-clears |

---

## Why 24V for the Pump Rail

The system uses a **single 24V rail** for all actuators. Key advantages over 12V:

**1. Broader pump and valve selection**
Most industrial-grade dosing pumps, solenoid valves, and peristaltic heads are
available in 24V variants. The 24V market has more options with chemical-resistant
wetted materials, higher flow range, and longer service ratings.

**2. Lower supply current for the same load power**
P = V × I. A 12W pump at 24V draws 0.5A; at 12V it draws 1.0A. Smaller wire
gauge, lower I²R losses in cables, less voltage drop across MOSFET Rds(on).

**3. Stepper motors: compatible at any VM within range**
The TMC2209 regulates coil current to the IRUN/RSENSE setpoint regardless of VM
(4.75–29V range). From the motor's perspective, 24V VM with 0.75A setpoint is
electrically equivalent to 12V VM at the same setpoint. No derating is needed.

**4. Better di/dt for stepper rise time**
Back-EMF limits step rate at high speed: coil current rise time = L/V (where V is
the voltage headroom above back-EMF). At 24V, the coil charges faster at higher RPM,
allowing a higher maximum reliable step rate if faster dosing is ever needed.

**5. Industry standard for automation**
24V DC is the IEC/DIN standard for industrial control and automation components.
Sensors, relays, valves, and actuators are commonly 24V-native.

**Why the Kamoer "KAS SF-12V" is fine at 24V VM:**
The "12V" in the name is the nominal motor voltage without a regulating driver.
With the TMC2209 regulating coil current, VM only affects headroom and rise time
— not the steady-state operating point. The motor sees its rated 0.75A regardless
of whether VM is 12V or 24V.
