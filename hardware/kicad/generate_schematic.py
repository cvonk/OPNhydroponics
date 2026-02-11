#!/usr/bin/env python3
"""
Generate KiCad 8 schematic for OPNhydroponics controller carrier PCB.

This script generates a complete .kicad_sch file with:
- Power input, protection, and regulation
- ESP32-C6-DevKitC-1 pin headers
- I2C sensor connectors (EZO pH/EC/DO, BME280, BH1750, OLED)
- 1-Wire, ultrasonic, and float switch interfaces
- 6× MOSFET driver circuits (pumps + ATO valve)
- WS2812B status LED
- Test points

Run: python generate_schematic.py
Output: hydroponics-controller.kicad_sch
"""

import uuid
import textwrap

# ---------------------------------------------------------------------------
# UUID helper
# ---------------------------------------------------------------------------
_uuid_counter = 0

def new_uuid():
    global _uuid_counter
    _uuid_counter += 1
    return f"a0000000-0000-4000-8000-{_uuid_counter:012d}"

# ---------------------------------------------------------------------------
# S-expression helpers
# ---------------------------------------------------------------------------
def xy(x, y):
    return f"(xy {x:.2f} {y:.2f})"

def at(x, y, rot=0):
    return f"(at {x:.2f} {y:.2f} {rot})"

def effects(size=1.27, hide=False):
    h = " hide" if hide else ""
    return f"(effects (font (size {size} {size})){h})"

def prop(name, value, x, y, rot=0, size=1.27, hide=False):
    return f'    (property "{name}" "{value}" {at(x, y, rot)} {effects(size, hide)})'

# ---------------------------------------------------------------------------
# Library symbol definitions
# ---------------------------------------------------------------------------
def lib_sym_resistor():
    return textwrap.dedent("""\
    (symbol "Device:R"
      (pin_numbers hide) (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54)
          (stroke (width 0) (type default)) (fill (type none))))
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_capacitor():
    return textwrap.dedent("""\
    (symbol "Device:C"
      (pin_numbers hide) (pin_names (offset 0.254) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "C" (at -1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0.9652 -2.54 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))
          (stroke (width 0.3048) (type default)) (fill (type none)))
        (polyline (pts (xy -1.524 0.508) (xy 1.524 0.508))
          (stroke (width 0.3048) (type default)) (fill (type none))))
      (symbol "C_1_1"
        (pin passive line (at 0 2.54 270) (length 2.032)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -2.54 90) (length 2.032)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_capacitor_polar():
    return textwrap.dedent("""\
    (symbol "Device:CP"
      (pin_numbers hide) (pin_names (offset 0.254) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "CP" (at -1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "CP_0_1"
        (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))
          (stroke (width 0.3048) (type default)) (fill (type none)))
        (polyline (pts (xy -1.524 0.508) (xy 1.524 0.508))
          (stroke (width 0.3048) (type default)) (fill (type none)))
        (polyline (pts (xy -0.508 1.27) (xy 0.508 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0.762) (xy 0 1.778))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "CP_1_1"
        (pin passive line (at 0 2.54 270) (length 2.032)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -2.54 90) (length 2.032)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_diode_schottky():
    return textwrap.dedent("""\
    (symbol "Device:D_Schottky"
      (pin_numbers hide) (pin_names (offset 1.016) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "D_Schottky" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_Schottky_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "D_Schottky_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54)
          (name "K" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54)
          (name "A" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_diode_tvs():
    return textwrap.dedent("""\
    (symbol "Device:D_TVS"
      (pin_numbers hide) (pin_names (offset 1.016) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "D_TVS" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_TVS_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "D_TVS_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54)
          (name "A1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54)
          (name "A2" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_fuse():
    return textwrap.dedent("""\
    (symbol "Device:Fuse"
      (pin_numbers hide) (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "F" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "Fuse" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Fuse_0_1"
        (rectangle (start -0.762 -2.54) (end 0.762 2.54)
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0 -2.54))
          (stroke (width 0) (type default)) (fill (type none))))
      (symbol "Fuse_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_nmos():
    """N-channel MOSFET: pin 1=G, pin 2=D, pin 3=S"""
    return textwrap.dedent("""\
    (symbol "Device:Q_NMOS_GDS"
      (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_NMOS_GDS" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_NMOS_GDS_0_1"
        (polyline (pts (xy 0.254 0) (xy -2.54 0))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 2.54) (xy 2.54 1.778) (xy 0.762 1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 -2.54) (xy 2.54 -1.778) (xy 0.762 -1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 -0.508) (xy 2.54 -0.508) (xy 2.54 -1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 0.508) (xy 1.524 0.254) (xy 1.524 0.762) (xy 0.762 0.508))
          (stroke (width 0) (type default)) (fill (type outline)))
        (circle (center 1.651 0) (radius 2.794)
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "Q_NMOS_GDS_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54)
          (name "G" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54)
          (name "D" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54)
          (name "S" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_pmos():
    """P-channel MOSFET: pin 1=G, pin 2=S, pin 3=D"""
    return textwrap.dedent("""\
    (symbol "Device:Q_PMOS_GSD"
      (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_PMOS_GSD" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_PMOS_GSD_0_1"
        (polyline (pts (xy 0.254 0) (xy -2.54 0))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 2.54) (xy 2.54 1.778) (xy 0.762 1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 -2.54) (xy 2.54 -1.778) (xy 0.762 -1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 0.508) (xy 2.54 0.508) (xy 2.54 1.778))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.524 -0.254) (xy 0.762 0.508) (xy 1.524 0.762))
          (stroke (width 0) (type default)) (fill (type outline)))
        (circle (center 1.651 0) (radius 2.794)
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "Q_PMOS_GSD_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54)
          (name "G" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54)
          (name "S" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54)
          (name "D" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_ams1117():
    """AMS1117-3.3 LDO: pin 1=GND/ADJ, pin 2=VOUT, pin 3=VIN"""
    return textwrap.dedent("""\
    (symbol "Regulator_Linear:AMS1117-3.3"
      (pin_names (offset 0.254))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "AMS1117-3.3" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-223-3_TabPin2" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "http://www.advanced-monolithic.com/pdf/ds1117.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "AMS1117-3.3_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81)
          (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "AMS1117-3.3_1_1"
        (pin power_in line (at 0 -6.35 90) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 7.62 0 180) (length 2.54)
          (name "VO" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -7.62 0 0) (length 2.54)
          (name "VI" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_conn(n_pins):
    """Generic N-pin connector symbol."""
    local_name = f"Conn_01x{n_pins:02d}_Pin"
    sym_name = f"Connector:{local_name}"
    lines = []
    lines.append(f'    (symbol "{sym_name}"')
    lines.append(f'      (pin_names (offset 1.016))')
    lines.append(f'      (exclude_from_sim no) (in_bom yes) (on_board yes)')
    lines.append(f'      (property "Reference" "J" (at 0 {n_pins * 1.27 + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'      (property "Value" "Conn_01x{n_pins:02d}" (at 0 {-n_pins * 1.27 - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    lines.append(f'      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    # Body
    half_h = n_pins * 1.27
    lines.append(f'      (symbol "{local_name}_1_1"')
    lines.append(f'        (rectangle (start -1.27 {half_h:.2f}) (end 1.27 {-half_h:.2f})')
    lines.append(f'          (stroke (width 0.254) (type default)) (fill (type background)))')
    # Pins
    for i in range(n_pins):
        py = half_h - 1.27 - i * 2.54
        lines.append(f'        (pin passive line (at -3.81 {py:.2f} 0) (length 2.54)')
        lines.append(f'          (name "Pin_{i+1}" (effects (font (size 1.27 1.27))))')
        lines.append(f'          (number "{i+1}" (effects (font (size 1.27 1.27)))))')
    lines.append(f'      )')
    lines.append(f'    )')
    return "\n".join(lines)

def lib_sym_ws2812b():
    """WS2812B LED: pin 1=VDD, pin 2=DOUT, pin 3=VSS, pin 4=DIN"""
    return textwrap.dedent("""\
    (symbol "LED:WS2812B"
      (pin_names (offset 0.254))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "WS2812B" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "WS2812B_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08)
          (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "WS2812B_1_1"
        (pin power_in line (at 0 7.62 270) (length 2.54)
          (name "VDD" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27)))))
        (pin output line (at 7.62 0 180) (length 2.54)
          (name "DOUT" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -7.62 90) (length 2.54)
          (name "VSS" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27)))))
        (pin input line (at -7.62 0 0) (length 2.54)
          (name "DIN" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_test_point():
    return textwrap.dedent("""\
    (symbol "Connector:TestPoint"
      (pin_numbers hide) (pin_names (offset 0.762) hide)
      (exclude_from_sim no) (in_bom no) (on_board yes)
      (property "Reference" "TP" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "TestPoint" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "TestPoint:TestPoint_Pad_1.0x1.0mm" (at 5.08 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 5.08 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "TestPoint_0_1"
        (circle (center 0 1.27) (radius 0.762)
          (stroke (width 0) (type default)) (fill (type none))))
      (symbol "TestPoint_1_1"
        (pin passive line (at 0 -1.27 90) (length 1.778)
          (name "1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))))
    )""")

def lib_sym_power(name, pin_num="1", value=None):
    """Power symbol (GND, +3.3V, +5V, +12V, PWR_FLAG)."""
    val = value or name
    sym_id = f"power:{name}"
    if name == "GND":
        return textwrap.dedent(f"""\
    (symbol "{sym_id}"
      (power) (pin_numbers hide) (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "{val}" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "{name}_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54)
            (xy -1.27 -1.27) (xy 0 -1.27))
          (stroke (width 0) (type default)) (fill (type none))))
      (symbol "{name}_1_1"
        (pin power_in line (at 0 0 270) (length 0)
          (name "{val}" (effects (font (size 1.27 1.27))))
          (number "{pin_num}" (effects (font (size 1.27 1.27))))))
    )""")
    elif name == "PWR_FLAG":
        return textwrap.dedent(f"""\
    (symbol "{sym_id}"
      (power) (pin_numbers hide) (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom no) (on_board yes)
      (property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "PWR_FLAG_0_0"
        (pin power_out line (at 0 0 90) (length 0)
          (name "pwr" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))))
    )""")
    else:
        return textwrap.dedent(f"""\
    (symbol "{sym_id}"
      (power) (pin_numbers hide) (pin_names (offset 0) hide)
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "{val}" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "{name}_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27))
          (stroke (width 0) (type default)) (fill (type none)))
        (pin power_in line (at 0 0 90) (length 1.27)
          (name "{val}" (effects (font (size 1.27 1.27))))
          (number "{pin_num}" (effects (font (size 1.27 1.27))))))
    )""")

# ---------------------------------------------------------------------------
# Component instance builders
# ---------------------------------------------------------------------------
class SchematicBuilder:
    def __init__(self):
        self.items = []  # All schematic items (symbols, wires, labels, text)
        self.pwr_idx = 0

    def _pwr_ref(self):
        self.pwr_idx += 1
        return f"#PWR{self.pwr_idx:03d}"

    def _flg_ref(self):
        self.pwr_idx += 1
        return f"#FLG{self.pwr_idx:03d}"

    def add_symbol(self, lib_id, ref, value, x, y, rot=0, footprint="",
                   pin_uuids=None, mirror=False, extra_props=None):
        """Add a component instance."""
        uid = new_uuid()
        mir = ""
        if mirror:
            mir = " (mirror x)"
        lines = []
        lines.append(f'  (symbol (lib_id "{lib_id}") {at(x, y, rot)}{mir} (unit 1)')
        lines.append(f'    (in_bom yes) (on_board yes) (dnp no)')
        lines.append(f'    (uuid "{uid}")')
        # Properties
        rx, ry = x + 2.54, y
        lines.append(f'    (property "Reference" "{ref}" {at(rx, ry)} {effects()})')
        lines.append(f'    (property "Value" "{value}" {at(rx, ry - 2.54)} {effects()})')
        if footprint:
            lines.append(f'    (property "Footprint" "{footprint}" {at(x, y)} {effects(hide=True)})')
        else:
            lines.append(f'    (property "Footprint" "" {at(x, y)} {effects(hide=True)})')
        lines.append(f'    (property "Datasheet" "~" {at(x, y)} {effects(hide=True)})')
        if extra_props:
            for pn, pv in extra_props.items():
                lines.append(f'    (property "{pn}" "{pv}" {at(x, y)} {effects(hide=True)})')
        # Pin UUIDs
        if pin_uuids:
            for pin_num, puid in pin_uuids.items():
                lines.append(f'    (pin "{pin_num}" (uuid "{puid}"))')
        else:
            # Auto-generate based on common pin counts
            for p in range(1, 30):
                lines.append(f'    (pin "{p}" (uuid "{new_uuid()}"))')
        lines.append(f'  )')
        self.items.append("\n".join(lines))
        return uid

    def add_power(self, name, x, y, rot=0):
        """Add a power symbol (GND, +12V, +5V, +3.3V)."""
        uid = new_uuid()
        if name == "PWR_FLAG":
            ref = self._flg_ref()
        else:
            ref = self._pwr_ref()
        lines = []
        lines.append(f'  (symbol (lib_id "power:{name}") {at(x, y, rot)} (unit 1)')
        lines.append(f'    (in_bom yes) (on_board yes) (dnp no)')
        lines.append(f'    (uuid "{uid}")')
        lines.append(f'    (property "Reference" "{ref}" {at(x, y)} {effects(hide=True)})')
        lines.append(f'    (property "Value" "{name}" {at(x, y + 2.54)} {effects()})')
        lines.append(f'    (property "Footprint" "" {at(x, y)} {effects(hide=True)})')
        lines.append(f'    (property "Datasheet" "" {at(x, y)} {effects(hide=True)})')
        lines.append(f'    (pin "1" (uuid "{new_uuid()}"))')
        lines.append(f'  )')
        self.items.append("\n".join(lines))

    def add_global_label(self, name, x, y, rot=0, shape="passive"):
        """Add a global label."""
        uid = new_uuid()
        lines = []
        lines.append(f'  (global_label "{name}" (shape {shape}) {at(x, y, rot)}')
        lines.append(f'    (effects (font (size 1.27 1.27)))')
        lines.append(f'    (uuid "{uid}")')
        lines.append(f'    (property "Intersheets" "" {at(x, y)} {effects(hide=True)})')
        lines.append(f'  )')
        self.items.append("\n".join(lines))

    def add_wire(self, x1, y1, x2, y2):
        """Add a wire segment."""
        uid = new_uuid()
        self.items.append(
            f'  (wire (pts {xy(x1, y1)} {xy(x2, y2)})\n'
            f'    (stroke (width 0) (type default))\n'
            f'    (uuid "{uid}")\n'
            f'  )'
        )

    def add_junction(self, x, y):
        uid = new_uuid()
        self.items.append(
            f'  (junction (at {x:.2f} {y:.2f}) (diameter 0) (color 0 0 0 0)\n'
            f'    (uuid "{uid}")\n'
            f'  )'
        )

    def add_no_connect(self, x, y):
        uid = new_uuid()
        self.items.append(f'  (no_connect (at {x:.2f} {y:.2f}) (uuid "{uid}"))')

    def add_text(self, text, x, y, size=2.54):
        uid = new_uuid()
        self.items.append(
            f'  (text "{text}" {at(x, y)}\n'
            f'    (effects (font (size {size} {size}) bold))\n'
            f'    (uuid "{uid}")\n'
            f'  )'
        )

    def add_text_box(self, text, x, y, w, h, size=1.27):
        """Add a dashed text box (section border)."""
        uid = new_uuid()
        self.items.append(
            f'  (rectangle (start {x:.2f} {y:.2f}) (end {x+w:.2f} {y+h:.2f})\n'
            f'    (stroke (width 0.254) (type dash))\n'
            f'    (fill (type none))\n'
            f'    (uuid "{uid}")\n'
            f'  )'
        )


# ---------------------------------------------------------------------------
# Build the full schematic
# ---------------------------------------------------------------------------
def build_schematic():
    sb = SchematicBuilder()

    # ===================================================================
    # SECTION 1: POWER INPUT & PROTECTION
    # ===================================================================
    sx, sy = 25.40, 30.48   # Section origin

    sb.add_text("POWER INPUT & PROTECTION", sx, sy - 5.08, size=3.0)
    sb.add_text_box("", sx - 2.54, sy - 7.62, 170.18, 55.88)

    # J1 - 12V Power Input (2-pin screw terminal)
    jx, jy = sx, sy + 10.16
    sb.add_symbol("Connector:Conn_01x02_Pin", "J1", "12V_IN",
                  jx, jy, footprint="Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal")
    sb.add_global_label("+12V_RAW", jx - 3.81, jy + 1.27, rot=180)
    sb.add_wire(jx - 3.81, jy + 1.27, jx - 3.81, jy + 1.27)
    sb.add_power("GND", jx - 3.81 - 2.54, jy - 1.27, rot=0)
    sb.add_wire(jx - 3.81, jy - 1.27, jx - 3.81 - 2.54, jy - 1.27)

    # F1 - PTC Fuse (5A)
    fx, fy = sx + 20.32, sy + 11.43
    sb.add_symbol("Device:Fuse", "F1", "RXEF500 5A", fx, fy, rot=90,
                  footprint="Fuse:Fuse_1812_4532Metric")
    sb.add_global_label("+12V_RAW", fx - 3.81, fy, rot=180)
    sb.add_global_label("12V_FUSED", fx + 3.81, fy, rot=0)

    # D1 - TVS Diode (SMBJ15A)
    dx, dy = sx + 40.64, sy + 11.43
    sb.add_symbol("Device:D_TVS", "D1", "SMBJ15A", dx, dy + 7.62, rot=0,
                  footprint="Diode_SMD:D_SMB_Handsoldering")
    sb.add_global_label("12V_FUSED", dx - 3.81, dy + 7.62, rot=180)
    sb.add_power("GND", dx + 3.81, dy + 7.62 + 2.54)
    sb.add_wire(dx + 3.81, dy + 7.62, dx + 3.81, dy + 7.62 + 2.54)

    # Q1 - P-MOSFET reverse polarity protection (SI2301)
    qx, qy = sx + 60.96, sy + 11.43
    sb.add_symbol("Device:Q_PMOS_GSD", "Q1", "SI2301", qx, qy,
                  footprint="Package_TO_SOT_SMD:SOT-23")
    # R1 - 10k gate to source
    sb.add_symbol("Device:R", "R1", "10k", qx - 10.16, qy + 5.08,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    # R2 - 100k gate to GND
    sb.add_symbol("Device:R", "R2", "100k", qx - 10.16, qy - 7.62,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_global_label("12V_FUSED", qx - 15.24, qy, rot=180)
    sb.add_global_label("+12V", qx + 2.54, qy + 5.08, rot=0)
    sb.add_power("GND", qx - 10.16, qy - 11.43 - 3.81)

    # ===================================================================
    # SECTION 2: VOLTAGE REGULATORS
    # ===================================================================
    rx, ry = sx + 105.0, sy  # Regulator section origin

    sb.add_text("VOLTAGE REGULATORS", rx, ry - 5.08, size=3.0)

    # Buck converter module (MP1584EN) - represented as 3-pin module
    bx, by = rx, ry + 10.16
    sb.add_symbol("Connector:Conn_01x03_Pin", "U1", "MP1584EN Module",
                  bx, by, footprint="")
    sb.add_text("12V->5V Buck", bx + 5.08, by - 5.08, size=1.27)
    sb.add_global_label("+12V", bx - 3.81, by + 2.54, rot=180)
    sb.add_power("GND", bx - 3.81 - 2.54, by)
    sb.add_wire(bx - 3.81, by, bx - 3.81 - 2.54, by)
    sb.add_global_label("+5V", bx - 3.81, by - 2.54, rot=180)

    # C_BUCK_OUT - 22µF output cap for buck
    sb.add_symbol("Device:C", "C1", "22uF", bx + 10.16, by + 5.08,
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    sb.add_global_label("+5V", bx + 10.16, by + 5.08 - 2.54, rot=0)
    sb.add_power("GND", bx + 10.16, by + 5.08 + 2.54)

    # U2 - AMS1117-3.3 LDO
    ux, uy = rx + 30.48, ry + 10.16
    sb.add_symbol("Regulator_Linear:AMS1117-3.3", "U2", "AMS1117-3.3",
                  ux, uy, footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    sb.add_global_label("+5V", ux - 7.62, uy, rot=180)
    sb.add_global_label("+3V3", ux + 7.62, uy, rot=0)
    sb.add_power("GND", ux, uy + 6.35)

    # C_LDO_IN - 10µF input
    sb.add_symbol("Device:C", "C2", "10uF", ux - 12.70, uy + 5.08,
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    sb.add_global_label("+5V", ux - 12.70, uy + 5.08 - 2.54, rot=0)
    sb.add_power("GND", ux - 12.70, uy + 5.08 + 2.54)

    # C_LDO_OUT - 10µF output
    sb.add_symbol("Device:C", "C3", "10uF", ux + 12.70, uy + 5.08,
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    sb.add_global_label("+3V3", ux + 12.70, uy + 5.08 - 2.54, rot=0)
    sb.add_power("GND", ux + 12.70, uy + 5.08 + 2.54)

    # PWR_FLAG symbols
    pfx = rx + 55.0
    sb.add_power("PWR_FLAG", pfx, ry + 5.08, rot=0)
    sb.add_global_label("+12V", pfx, ry + 5.08, rot=0)
    sb.add_power("PWR_FLAG", pfx + 12.70, ry + 5.08, rot=0)
    sb.add_global_label("+5V", pfx + 12.70, ry + 5.08, rot=0)
    sb.add_power("PWR_FLAG", pfx + 25.40, ry + 5.08, rot=0)
    sb.add_global_label("+3V3", pfx + 25.40, ry + 5.08, rot=0)
    sb.add_power("PWR_FLAG", pfx + 38.10, ry + 5.08, rot=0)
    sb.add_power("GND", pfx + 38.10, ry + 5.08)

    # ===================================================================
    # SECTION 3: ESP32-C6 DEVKIT HEADERS
    # ===================================================================
    ex, ey = 130.0, 88.90

    sb.add_text("ESP32-C6-DevKitC-1-N8 HEADERS", ex, ey - 5.08, size=3.0)
    sb.add_text_box("", ex - 2.54, ey - 7.62, 124.46, 135.0)

    # Left header J16 (1x20) - mapped to specific GPIOs
    hx, hy = ex + 20.32, ey + 10.16
    sb.add_symbol("Connector:Conn_01x20_Pin", "J16", "DevKit_Left",
                  hx, hy, footprint="Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical")

    # Label the left header pins
    left_pins = [
        ("+3V3", "power_in"),
        ("+3V3", "power_in"),
        ("~{RST}", "input"),
        ("GPIO0_BOOT", "bidirectional"),
        ("I2C_SDA", "bidirectional"),
        ("I2C_SCL", "output"),
        ("ONEWIRE", "bidirectional"),
        ("US_TRIG", "output"),
        ("US_ECHO", "input"),
        ("PUMP_MAIN", "output"),
        ("PUMP_PH_UP", "output"),
        ("GPIO8_RSVD", "passive"),
        ("PUMP_NUT_A", "output"),
        ("PUMP_NUT_B", "output"),
        ("FLOAT_LOW", "input"),
        ("FLOAT_HIGH", "input"),
        ("LED_DATA", "output"),
        ("GPIO14_SPARE", "passive"),
        ("UART_TX", "output"),
        ("GND_L", "passive"),
    ]
    pin_y_start = hy + (20 * 1.27 - 1.27)
    for i, (label_name, shape) in enumerate(left_pins):
        py = pin_y_start - i * 2.54
        if label_name.startswith("+") or label_name.startswith("GND"):
            if label_name.startswith("+3V3"):
                sb.add_power("+3V3", hx - 3.81 - 5.08, py, rot=90)
                sb.add_wire(hx - 3.81, py, hx - 3.81 - 5.08, py)
            elif label_name == "GND_L":
                sb.add_power("GND", hx - 3.81 - 5.08, py, rot=90)
                sb.add_wire(hx - 3.81, py, hx - 3.81 - 5.08, py)
        elif label_name.startswith("~"):
            sb.add_no_connect(hx - 3.81, py)
        elif label_name == "GPIO8_RSVD":
            sb.add_no_connect(hx - 3.81, py)
        elif label_name == "GPIO14_SPARE":
            sb.add_no_connect(hx - 3.81, py)
        else:
            sb.add_global_label(label_name, hx - 3.81 - 2.54, py, rot=180, shape=shape)
            sb.add_wire(hx - 3.81, py, hx - 3.81 - 2.54, py)

    # Right header J17 (1x20)
    h2x, h2y = ex + 60.96, ey + 10.16
    sb.add_symbol("Connector:Conn_01x20_Pin", "J17", "DevKit_Right",
                  h2x, h2y, footprint="Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical")

    right_pins = [
        ("+5V", "power_in"),
        ("GND_R", "passive"),
        ("UART_RX", "input"),
        ("GPIO17_SPARE", "passive"),
        ("USB_DN", "passive"),
        ("USB_DP", "passive"),
        ("ATO_VALVE", "output"),
        ("PUMP_PH_DN", "output"),
        ("GPIO22_SPARE", "passive"),
        ("GPIO23_SPARE", "passive"),
        ("NC1", "passive"),
        ("NC2", "passive"),
        ("NC3", "passive"),
        ("NC4", "passive"),
        ("NC5", "passive"),
        ("NC6", "passive"),
        ("NC7", "passive"),
        ("NC8", "passive"),
        ("NC9", "passive"),
        ("NC10", "passive"),
    ]
    for i, (label_name, shape) in enumerate(right_pins):
        py = pin_y_start - i * 2.54
        if label_name == "+5V":
            sb.add_power("+5V", h2x - 3.81 - 5.08, py, rot=90)
            sb.add_wire(h2x - 3.81, py, h2x - 3.81 - 5.08, py)
        elif label_name == "GND_R":
            sb.add_power("GND", h2x - 3.81 - 5.08, py, rot=90)
            sb.add_wire(h2x - 3.81, py, h2x - 3.81 - 5.08, py)
        elif label_name.startswith("NC") or label_name.startswith("USB") or label_name.startswith("GPIO"):
            sb.add_no_connect(h2x - 3.81, py)
        else:
            sb.add_global_label(label_name, h2x - 3.81 - 2.54, py, rot=180, shape=shape)
            sb.add_wire(h2x - 3.81, py, h2x - 3.81 - 2.54, py)

    # ===================================================================
    # SECTION 4: I2C BUS & SENSOR CONNECTORS
    # ===================================================================
    ix, iy = 25.40, 100.0

    sb.add_text("I2C BUS & SENSOR CONNECTORS", ix, iy - 5.08, size=3.0)
    sb.add_text_box("", ix - 2.54, iy - 7.62, 100.0, 90.0)

    # I2C pull-up resistors
    sb.add_symbol("Device:R", "R3", "4.7k", ix + 5.08, iy + 5.08,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_power("+3V3", ix + 5.08, iy + 5.08 - 3.81, rot=0)
    sb.add_global_label("I2C_SDA", ix + 5.08, iy + 5.08 + 3.81, rot=270)

    sb.add_symbol("Device:R", "R4", "4.7k", ix + 15.24, iy + 5.08,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_power("+3V3", ix + 15.24, iy + 5.08 - 3.81, rot=0)
    sb.add_global_label("I2C_SCL", ix + 15.24, iy + 5.08 + 3.81, rot=270)

    # I2C bus decoupling
    sb.add_symbol("Device:C", "C4", "100nF", ix + 25.40, iy + 5.08,
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    sb.add_power("+3V3", ix + 25.40, iy + 5.08 - 2.54, rot=0)
    sb.add_power("GND", ix + 25.40, iy + 5.08 + 2.54)

    # I2C Sensor connectors (JST-PH 4-pin, Qwiic compatible)
    # Pin order: GND, 3.3V, SDA, SCL
    i2c_connectors = [
        ("J8", "EZO-pH", ix + 5.08, iy + 25.40),
        ("J9", "EZO-EC", ix + 25.40, iy + 25.40),
        ("J10", "EZO-DO", ix + 45.72, iy + 25.40),
        ("J11", "BME280", ix + 66.04, iy + 25.40),
        ("J12", "BH1750", ix + 5.08, iy + 50.80),
        ("J21", "OLED", ix + 25.40, iy + 50.80),
    ]
    for ref, val, cx, cy in i2c_connectors:
        sb.add_symbol("Connector:Conn_01x04_Pin", ref, val,
                      cx, cy, footprint="Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical")
        # Pin 1 = GND, Pin 2 = 3.3V, Pin 3 = SDA, Pin 4 = SCL
        pin_top = cy + (4 * 1.27 - 1.27)
        sb.add_power("GND", cx - 3.81 - 2.54, pin_top, rot=90)
        sb.add_wire(cx - 3.81, pin_top, cx - 3.81 - 2.54, pin_top)
        sb.add_power("+3V3", cx - 3.81 - 2.54, pin_top - 2.54, rot=90)
        sb.add_wire(cx - 3.81, pin_top - 2.54, cx - 3.81 - 2.54, pin_top - 2.54)
        sb.add_global_label("I2C_SDA", cx - 3.81 - 2.54, pin_top - 5.08, rot=180)
        sb.add_wire(cx - 3.81, pin_top - 5.08, cx - 3.81 - 2.54, pin_top - 5.08)
        sb.add_global_label("I2C_SCL", cx - 3.81 - 2.54, pin_top - 7.62, rot=180)
        sb.add_wire(cx - 3.81, pin_top - 7.62, cx - 3.81 - 2.54, pin_top - 7.62)

    # BNC connectors for probes
    sb.add_text("BNC Probe Connectors", ix + 45.72, iy + 50.80 - 5.08, size=1.5)
    bnc_conns = [
        ("J22", "BNC_pH", ix + 45.72, iy + 55.88),
        ("J23", "BNC_EC", ix + 60.96, iy + 55.88),
        ("J24", "BNC_DO", ix + 76.20, iy + 55.88),
    ]
    for ref, val, cx, cy in bnc_conns:
        sb.add_symbol("Connector:Conn_01x02_Pin", ref, val,
                      cx, cy, footprint="Connector:BNC_TEConnectivity_1478204_Vertical")
        pin_top = cy + (2 * 1.27 - 1.27)
        sb.add_text("To EZO PRB", cx + 3.0, cy, size=1.0)
        sb.add_power("GND", cx - 3.81 - 2.54, pin_top - 2.54, rot=90)
        sb.add_wire(cx - 3.81, pin_top - 2.54, cx - 3.81 - 2.54, pin_top - 2.54)

    # ===================================================================
    # SECTION 5: 1-WIRE, ULTRASONIC, FLOAT SWITCHES
    # ===================================================================
    ox, oy = 25.40, 195.0

    sb.add_text("1-WIRE / ULTRASONIC / FLOAT SWITCHES", ox, oy - 5.08, size=3.0)
    sb.add_text_box("", ox - 2.54, oy - 7.62, 100.0, 70.0)

    # --- 1-Wire Section ---
    sb.add_text("1-Wire (DS18B20)", ox, oy + 2.54, size=1.5)

    # R5 - 1-Wire pull-up 4.7k
    sb.add_symbol("Device:R", "R5", "4.7k", ox + 5.08, oy + 10.16,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_power("+3V3", ox + 5.08, oy + 10.16 - 3.81, rot=0)
    sb.add_global_label("ONEWIRE", ox + 5.08, oy + 10.16 + 3.81, rot=270)

    # J13 - 1-Wire connector (3-pin JST-PH: GND, DATA, 3.3V)
    sb.add_symbol("Connector:Conn_01x03_Pin", "J13", "1-Wire",
                  ox + 20.32, oy + 12.70,
                  footprint="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical")
    pin_top = oy + 12.70 + (3 * 1.27 - 1.27)
    sb.add_power("GND", ox + 20.32 - 3.81 - 2.54, pin_top, rot=90)
    sb.add_wire(ox + 20.32 - 3.81, pin_top, ox + 20.32 - 3.81 - 2.54, pin_top)
    sb.add_global_label("ONEWIRE", ox + 20.32 - 3.81 - 2.54, pin_top - 2.54, rot=180)
    sb.add_wire(ox + 20.32 - 3.81, pin_top - 2.54, ox + 20.32 - 3.81 - 2.54, pin_top - 2.54)
    sb.add_power("+3V3", ox + 20.32 - 3.81 - 2.54, pin_top - 5.08, rot=90)
    sb.add_wire(ox + 20.32 - 3.81, pin_top - 5.08, ox + 20.32 - 3.81 - 2.54, pin_top - 5.08)

    # --- Ultrasonic Section ---
    sb.add_text("Ultrasonic (HC-SR04)", ox + 35.56, oy + 2.54, size=1.5)

    # J14 - Ultrasonic connector (4-pin: VCC, TRIG, ECHO, GND)
    sb.add_symbol("Connector:Conn_01x04_Pin", "J14", "HC-SR04",
                  ox + 40.64, oy + 12.70,
                  footprint="Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical")
    pin_top = oy + 12.70 + (4 * 1.27 - 1.27)
    sb.add_power("+5V", ox + 40.64 - 3.81 - 2.54, pin_top, rot=90)
    sb.add_wire(ox + 40.64 - 3.81, pin_top, ox + 40.64 - 3.81 - 2.54, pin_top)
    sb.add_global_label("US_TRIG", ox + 40.64 - 3.81 - 2.54, pin_top - 2.54, rot=180)
    sb.add_wire(ox + 40.64 - 3.81, pin_top - 2.54, ox + 40.64 - 3.81 - 2.54, pin_top - 2.54)

    # ECHO voltage divider (5V -> 3.3V): R6=1k series, R7=2.2k to GND
    echo_x = ox + 55.88
    sb.add_symbol("Device:R", "R6", "1k", echo_x, oy + 12.70,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_wire(ox + 40.64 - 3.81, pin_top - 5.08, echo_x, pin_top - 5.08)
    sb.add_wire(echo_x, pin_top - 5.08, echo_x, oy + 12.70 - 3.81)

    sb.add_symbol("Device:R", "R7", "2.2k", echo_x, oy + 25.40,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_wire(echo_x, oy + 12.70 + 3.81, echo_x, oy + 25.40 - 3.81)
    sb.add_junction(echo_x, oy + 12.70 + 3.81)
    sb.add_global_label("US_ECHO", echo_x + 5.08, oy + 12.70 + 3.81, rot=0)
    sb.add_wire(echo_x, oy + 12.70 + 3.81, echo_x + 5.08, oy + 12.70 + 3.81)
    sb.add_power("GND", echo_x, oy + 25.40 + 3.81)

    sb.add_power("GND", ox + 40.64 - 3.81 - 2.54, pin_top - 7.62, rot=90)
    sb.add_wire(ox + 40.64 - 3.81, pin_top - 7.62, ox + 40.64 - 3.81 - 2.54, pin_top - 7.62)

    # --- Float Switch Section ---
    sb.add_text("Float Switches", ox + 72.0, oy + 2.54, size=1.5)

    float_switches = [
        ("R8", "10k", "C5", "100nF", "J15", "Float_Low", "FLOAT_LOW", ox + 72.0, oy + 10.16),
        ("R9", "10k", "C6", "100nF", "J16B", "Float_High", "FLOAT_HIGH", ox + 88.0, oy + 10.16),
    ]
    # Note: J16B is intentionally different ref to avoid conflict with J16 DevKit
    # Let me fix the refs
    float_switches = [
        ("R8", "10k", "C5", "100nF", "J15", "Float_Low", "FLOAT_LOW", ox + 72.0, oy + 10.16),
        ("R9", "10k", "C6", "100nF", "J18", "Float_High", "FLOAT_HIGH", ox + 88.0, oy + 10.16),
    ]

    for r_ref, r_val, c_ref, c_val, j_ref, j_val, label, fx2, fy2 in float_switches:
        # Pull-up resistor
        sb.add_symbol("Device:R", r_ref, r_val, fx2, fy2,
                      footprint="Resistor_SMD:R_0805_2012Metric")
        sb.add_power("+3V3", fx2, fy2 - 3.81, rot=0)

        # Junction point
        sb.add_junction(fx2, fy2 + 3.81)
        sb.add_global_label(label, fx2 + 5.08, fy2 + 3.81, rot=0)
        sb.add_wire(fx2, fy2 + 3.81, fx2 + 5.08, fy2 + 3.81)

        # Debounce capacitor
        sb.add_symbol("Device:C", c_ref, c_val, fx2, fy2 + 12.70,
                      footprint="Capacitor_SMD:C_0805_2012Metric")
        sb.add_wire(fx2, fy2 + 3.81, fx2, fy2 + 12.70 - 2.54)
        sb.add_power("GND", fx2, fy2 + 12.70 + 2.54)

        # Float switch connector (2-pin)
        sb.add_symbol("Connector:Conn_01x02_Pin", j_ref, j_val,
                      fx2 - 10.16, fy2 + 10.16,
                      footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical")
        pin_top2 = fy2 + 10.16 + (2 * 1.27 - 1.27)
        sb.add_wire(fx2 - 10.16 - 3.81, pin_top2, fx2, fy2 + 3.81)
        sb.add_power("GND", fx2 - 10.16 - 3.81 - 2.54, pin_top2 - 2.54, rot=90)
        sb.add_wire(fx2 - 10.16 - 3.81, pin_top2 - 2.54, fx2 - 10.16 - 3.81 - 2.54, pin_top2 - 2.54)

    # ===================================================================
    # SECTION 6: MOSFET PUMP/VALVE DRIVERS
    # ===================================================================
    mx, my = 270.0, 30.48

    sb.add_text("PUMP & VALVE DRIVERS (12V)", mx, my - 5.08, size=3.0)
    sb.add_text_box("", mx - 2.54, my - 7.62, 145.0, 200.0)

    drivers = [
        ("Q2", "IRLZ44N", "R10", "100R", "R11", "10k", "D2", "SS34",
         "J2", "Main_Pump", "PUMP_MAIN", my + 5.08),
        ("Q3", "IRLZ44N", "R12", "100R", "R13", "10k", "D3", "SS34",
         "J3", "pH_Up_Pump", "PUMP_PH_UP", my + 35.56),
        ("Q4", "IRLZ44N", "R14", "100R", "R15", "10k", "D4", "SS34",
         "J4", "pH_Down_Pump", "PUMP_PH_DN", my + 66.04),
        ("Q5", "IRLZ44N", "R16", "100R", "R17", "10k", "D5", "SS34",
         "J5", "Nutrient_A", "PUMP_NUT_A", my + 96.52),
        ("Q6", "IRLZ44N", "R18", "100R", "R19", "10k", "D6", "SS34",
         "J6", "Nutrient_B", "PUMP_NUT_B", my + 127.0),
        ("Q7", "IRLZ44N", "R20", "100R", "R21", "10k", "D7", "SS34",
         "J7", "ATO_Valve", "ATO_VALVE", my + 157.48),
    ]

    for (q_ref, q_val, rg_ref, rg_val, rpd_ref, rpd_val,
         d_ref, d_val, j_ref, j_val, gpio_label, dy2) in drivers:

        # MOSFET
        qx2 = mx + 40.64
        sb.add_symbol("Device:Q_NMOS_GDS", q_ref, q_val, qx2, dy2,
                      footprint="Package_TO_SOT_THT:TO-220-3_Vertical")

        # Gate series resistor (100Ω)
        sb.add_symbol("Device:R", rg_ref, rg_val, qx2 - 17.78, dy2, rot=90,
                      footprint="Resistor_SMD:R_0805_2012Metric")
        sb.add_wire(qx2 - 17.78 + 3.81, dy2, qx2 - 5.08, dy2)
        sb.add_global_label(gpio_label, qx2 - 17.78 - 3.81, dy2, rot=180)

        # Gate pull-down resistor (10k)
        sb.add_symbol("Device:R", rpd_ref, rpd_val, qx2 - 10.16, dy2 + 10.16,
                      footprint="Resistor_SMD:R_0805_2012Metric")
        sb.add_wire(qx2 - 10.16, dy2 + 10.16 - 3.81, qx2 - 10.16, dy2)
        sb.add_junction(qx2 - 10.16, dy2)
        sb.add_power("GND", qx2 - 10.16, dy2 + 10.16 + 3.81)

        # Flyback diode (cathode to +12V, anode to drain)
        sb.add_symbol("Device:D_Schottky", d_ref, d_val,
                      qx2 + 15.24, dy2, rot=90,
                      footprint="Diode_SMD:D_SMA_Handsoldering")
        sb.add_wire(qx2 + 2.54, dy2 + 5.08, qx2 + 15.24, dy2 + 5.08)
        sb.add_wire(qx2 + 15.24, dy2 + 5.08, qx2 + 15.24, dy2 + 3.81)
        sb.add_wire(qx2 + 15.24, dy2 - 3.81, qx2 + 15.24, dy2 - 5.08)
        sb.add_wire(qx2 + 2.54, dy2 - 5.08, qx2 + 15.24, dy2 - 5.08)

        # +12V to drain (via load)
        sb.add_power("+12V", qx2 + 2.54, dy2 + 5.08 + 5.08, rot=0)
        sb.add_wire(qx2 + 2.54, dy2 + 5.08, qx2 + 2.54, dy2 + 5.08 + 5.08)

        # GND on source
        sb.add_power("GND", qx2 + 2.54, dy2 - 5.08 - 2.54)
        sb.add_wire(qx2 + 2.54, dy2 - 5.08, qx2 + 2.54, dy2 - 5.08 - 2.54)

        # Output connector (2-pin screw terminal)
        sb.add_symbol("Connector:Conn_01x02_Pin", j_ref, j_val,
                      qx2 + 30.48, dy2,
                      footprint="Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal")
        j_pin_top = dy2 + (2 * 1.27 - 1.27)
        # Pin 1 = PUMP+ (connects to 12V via load)
        sb.add_wire(qx2 + 30.48 - 3.81, j_pin_top, qx2 + 2.54, dy2 + 5.08)
        sb.add_junction(qx2 + 2.54, dy2 + 5.08)
        # Pin 2 = PUMP- (connects to drain)
        sb.add_wire(qx2 + 30.48 - 3.81, j_pin_top - 2.54, qx2 + 2.54, dy2 + 5.08 - 2.54)

    # ===================================================================
    # SECTION 7: WS2812B STATUS LED
    # ===================================================================
    lx, ly = 130.0, 235.0

    sb.add_text("STATUS LED", lx, ly - 5.08, size=3.0)
    sb.add_text_box("", lx - 2.54, ly - 7.62, 60.0, 40.0)

    # WS2812B
    sb.add_symbol("LED:WS2812B", "D8", "WS2812B", lx + 20.32, ly + 10.16,
                  footprint="LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm")
    sb.add_power("+5V", lx + 20.32, ly + 10.16 - 7.62, rot=0)
    sb.add_power("GND", lx + 20.32, ly + 10.16 + 7.62)

    # R22 - Series resistor on data line (100Ω)
    sb.add_symbol("Device:R", "R22", "100R", lx + 5.08, ly + 10.16, rot=90,
                  footprint="Resistor_SMD:R_0805_2012Metric")
    sb.add_global_label("LED_DATA", lx + 5.08 - 3.81, ly + 10.16, rot=180)
    sb.add_wire(lx + 5.08 + 3.81, ly + 10.16, lx + 20.32 - 7.62, ly + 10.16)

    # C7 - Decoupling cap (100nF)
    sb.add_symbol("Device:C", "C7", "100nF", lx + 35.56, ly + 10.16,
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    sb.add_power("+5V", lx + 35.56, ly + 10.16 - 2.54, rot=0)
    sb.add_power("GND", lx + 35.56, ly + 10.16 + 2.54)

    # DOUT - no connect (single LED)
    sb.add_no_connect(lx + 20.32 + 7.62, ly + 10.16)

    # ===================================================================
    # SECTION 8: TEST POINTS
    # ===================================================================
    tx, ty = 270.0, 240.0

    sb.add_text("TEST POINTS", tx, ty - 5.08, size=3.0)
    sb.add_text_box("", tx - 2.54, ty - 7.62, 80.0, 30.0)

    test_points = [
        ("TP1", "+3V3", "+3V3"),
        ("TP2", "+5V", "+5V"),
        ("TP3", "+12V", "+12V"),
        ("TP4", "GND", "GND"),
        ("TP5", "SDA", "I2C_SDA"),
        ("TP6", "SCL", "I2C_SCL"),
        ("TP7", "1-Wire", "ONEWIRE"),
    ]
    for i, (ref, val, net) in enumerate(test_points):
        tpx = tx + 5.08 + i * 10.16
        tpy = ty + 10.16
        sb.add_symbol("Connector:TestPoint", ref, val, tpx, tpy,
                      footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
        if net in ("+3V3", "+5V", "+12V"):
            sb.add_power(net, tpx, tpy - 1.27 - 2.54, rot=0)
            sb.add_wire(tpx, tpy - 1.27, tpx, tpy - 1.27 - 2.54)
        elif net == "GND":
            sb.add_power("GND", tpx, tpy - 1.27 + 2.54)
            sb.add_wire(tpx, tpy - 1.27, tpx, tpy - 1.27 + 2.54)
        else:
            sb.add_global_label(net, tpx, tpy - 1.27, rot=90)

    return sb


# ---------------------------------------------------------------------------
# Assemble the full .kicad_sch file
# ---------------------------------------------------------------------------
def generate():
    sb = build_schematic()

    root_uuid = new_uuid()

    # Collect all lib_symbols
    lib_syms = []
    lib_syms.append(lib_sym_resistor())
    lib_syms.append(lib_sym_capacitor())
    lib_syms.append(lib_sym_capacitor_polar())
    lib_syms.append(lib_sym_diode_schottky())
    lib_syms.append(lib_sym_diode_tvs())
    lib_syms.append(lib_sym_fuse())
    lib_syms.append(lib_sym_nmos())
    lib_syms.append(lib_sym_pmos())
    lib_syms.append(lib_sym_ams1117())
    lib_syms.append(lib_sym_ws2812b())
    lib_syms.append(lib_sym_test_point())
    # Connectors
    for n in [2, 3, 4, 20]:
        lib_syms.append(lib_sym_conn(n))
    # Power symbols
    for name in ["+3V3", "+5V", "+12V", "GND", "PWR_FLAG"]:
        lib_syms.append(lib_sym_power(name))

    output = []
    output.append('(kicad_sch')
    output.append('  (version 20231120)')
    output.append('  (generator "eeschema")')
    output.append('  (generator_version "8.0")')
    output.append(f'  (uuid "{root_uuid}")')
    output.append('  (paper "A3")')
    output.append('')
    output.append('  (lib_symbols')
    for ls in lib_syms:
        output.append(ls)
    output.append('  )')
    output.append('')

    # All schematic items
    for item in sb.items:
        output.append(item)

    output.append('')
    output.append('  (sheet_instances')
    output.append('    (path "/"')
    output.append('      (page "1")')
    output.append('    )')
    output.append('  )')
    output.append(')')
    output.append('')

    return "\n".join(output)


if __name__ == "__main__":
    import os
    content = generate()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "hydroponics-controller.kicad_sch")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {out_path}")
    print(f"Components and nets written successfully.")
    print(f"Open in KiCad 8.0+ to view and refine layout.")
