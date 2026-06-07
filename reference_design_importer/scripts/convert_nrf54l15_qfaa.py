#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


REPO = Path("/home/h/Documents/Nordic/nordic-lib-kicad")
WORK = REPO / "reference_design_importer"
DESIGN = WORK / "nrf54l15_10_05"
SRC = DESIGN / "nRF54L15-QFAA Reference Layout 0_8" / "Altium Designer files"
STAGE = DESIGN / "stage"
GENERATED = DESIGN / "generated"
MAPPINGS = DESIGN / "mappings"
REPORTS = DESIGN / "reports"

DESIGN_NAME = "nRF54L15_qfaa_4L_config1"
IMPORTED_PCB = STAGE / "imported.kicad_pcb"
FINAL_PCB = GENERATED / f"{DESIGN_NAME}.kicad_pcb"
FINAL_SCH = GENERATED / f"{DESIGN_NAME}.kicad_sch"
FINAL_PRO = GENERATED / f"{DESIGN_NAME}.kicad_pro"


@dataclass(frozen=True)
class FootprintTarget:
    lib_id: str
    path: Path
    status: str = "verified"


@dataclass
class FootprintInfo:
    source_lib_id: str
    reference: str
    value: str
    layer: str
    at: str
    pad_nets: dict[str, str]
    path: str | None
    sheetname: str | None
    sheetfile: str | None
    reference_property: str
    value_property: str
    block: str


FOOTPRINT_MAP: dict[str, FootprintTarget] = {
    "CAPC0603X03L_C:CAPC0603X03L_C": FootprintTarget(
        "passives:C_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/C_0201_0603Metric_L.kicad_mod",
    ),
    "Parts$:CAPC0603X03L_C": FootprintTarget(
        "passives:C_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/C_0201_0603Metric_L.kicad_mod",
    ),
    "Passive:CAPC0603X03L_C": FootprintTarget(
        "passives:C_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/C_0201_0603Metric_L.kicad_mod",
    ),
    "Parts$:CAPC1005X04L": FootprintTarget(
        "passives:C_0402_1005Metric_L",
        REPO / "footprints/passives.pretty/C_0402_1005Metric_L.kicad_mod",
    ),
    "RESC0603X03L_C:RESC0603X03L_C": FootprintTarget(
        "passives:R_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/R_0201_0603Metric_L.kicad_mod",
    ),
    "INDC0603X03L_C:INDC0603X03L_C": FootprintTarget(
        "passives:L_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/L_0201_0603Metric_L.kicad_mod",
    ),
    "Passive:INDC0603X03L_C": FootprintTarget(
        "passives:L_0201_0603Metric_L",
        REPO / "footprints/passives.pretty/L_0201_0603Metric_L.kicad_mod",
    ),
    "0603:INDC1608X06L": FootprintTarget(
        "passives:L_0603_1608Metric_L",
        REPO / "footprints/passives.pretty/L_0603_1608Metric_L.kicad_mod",
    ),
    "Parts$:XTAL_2012": FootprintTarget(
        "Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm",
        Path("/usr/share/kicad/footprints/Crystal.pretty/Crystal_SMD_2012-2Pin_2.0x1.2mm.kicad_mod"),
    ),
    "Parts$:BT-XTAL_2016": FootprintTarget(
        "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm",
        Path("/usr/share/kicad/footprints/Crystal.pretty/Crystal_SMD_2016-4Pin_2.0x1.6mm.kicad_mod"),
    ),
    "Misc:QFN40P600X600X90-48N": FootprintTarget(
        "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm_ThermalVias",
        Path("/usr/share/kicad/footprints/Package_DFN_QFN.pretty/QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm_ThermalVias.kicad_mod"),
    ),
}


SYMBOL_MAP = {
    "C": ("Device:C_Small", "C_Small"),
    "R": ("Device:R_Small", "R_Small"),
    "L": ("Device:L_Small", "L_Small"),
    "FB": ("Device:FerriteBead_Small", "FerriteBead_Small"),
    "X2": ("Device:Crystal_GND24_Small", "Crystal_GND24_Small"),
    "X": ("Device:Crystal_Small", "Crystal_Small"),
    "U": ("nordic-lib-kicad-nrf54l:nRF54L15-QFXX", "nRF54L15-QFXX"),
}


GRID_MM = 1.27
U1_POSITION = (127.0, 101.6)
SCHEMATIC_GROUP_SPACING = 20.32


def q(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def normalize_value(value: str) -> str:
    return value.replace("\u00b5", "u").replace("\u03bc", "u")


def new_uuid() -> str:
    return str(uuid.uuid4())


def round_grid(value: float) -> float:
    return round(value / GRID_MM) * GRID_MM


def ref_sort_key(reference: str) -> tuple[str, int, str]:
    match = re.match(r"([A-Z]+)(\d+)(.*)", reference)
    if not match:
        return (reference, 0, "")
    return (match.group(1), int(match.group(2)), match.group(3))


def ensure_dirs() -> None:
    for directory in (STAGE, GENERATED, MAPPINGS, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)


def run_import() -> None:
    subprocess.run(
        [
            "kicad-cli",
            "pcb",
            "import",
            "--format",
            "altium",
            "--report-format",
            "json",
            "--report-file",
            str(STAGE / "pcb-import-report.json"),
            "-o",
            str(IMPORTED_PCB),
            str(SRC / f"{DESIGN_NAME}.PcbDoc"),
        ],
        check=True,
    )


def block_ranges(text: str, start_pat: str) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    i = 0
    while True:
        start = text.find(start_pat, i)
        if start < 0:
            return ranges
        depth = 0
        in_string = False
        escape = False
        for pos in range(start, len(text)):
            char = text[pos]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    ranges.append((start, pos + 1, text[start : pos + 1]))
                    i = pos + 1
                    break
        else:
            raise ValueError(f"unclosed block starting at {start}")


def first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def parse_footprint(block: str) -> FootprintInfo:
    source_lib_id = first_match(r'^\(footprint "([^"]+)"', block)
    reference = first_match(r'\(property "Reference" "([^"]+)"', block)
    raw_value = first_match(r'\(property "Value" "([^"]*)"', block)
    value = normalize_value(raw_value or "")
    layer = first_match(r'^\s*\(layer "([^"]+)"\)', block)
    at = first_match(r'^\s*\(at ([^)]+)\)', block)
    path = first_match(r'^\s*\(path "([^"]+)"\)', block)
    sheetname = first_match(r'^\s*\(sheetname "([^"]+)"\)', block)
    sheetfile = first_match(r'^\s*\(sheetfile "([^"]+)"\)', block)
    if not all([source_lib_id, reference, raw_value is not None, layer, at]):
        raise ValueError(f"could not parse footprint block:\n{block[:500]}")
    reference_property = extract_property_block(block, "Reference")
    value_property = set_property(extract_property_block(block, "Value"), "Value", value)
    pad_nets: dict[str, str] = {}
    for _, _, pad in block_ranges(block, "(pad "):
        pad_num = first_match(r'^\(pad "([^"]*)"', pad)
        net = first_match(r'\(net "([^"]+)"\)', pad)
        if pad_num and net:
            pad_nets[pad_num] = net
    return FootprintInfo(
        source_lib_id=source_lib_id,
        reference=reference,
        value=value,
        layer=layer,
        at=at,
        pad_nets=pad_nets,
        path=path,
        sheetname=sheetname,
        sheetfile=sheetfile,
        reference_property=reference_property,
        value_property=value_property,
        block=block,
    )


def extract_property_block(block: str, name: str) -> str:
    for _, _, candidate in block_ranges(block, f'(property "{name}"'):
        return candidate
    raise ValueError(f"missing property {name}")


def replace_property_block(block: str, name: str, replacement: str) -> str:
    for start, end, _ in block_ranges(block, f'(property "{name}"'):
        return block[:start] + replacement + block[end:]
    raise ValueError(f"missing target property {name}")


def set_property(block: str, name: str, value: str) -> str:
    return re.sub(
        rf'(\(property "{re.escape(name)}" )"[^"]*"',
        rf'\1"{q(value)}"',
        block,
        count=1,
    )


def swap_to_bottom_layers(block: str) -> str:
    replacements = {
        '"F.Cu"': '"B.Cu"',
        '"F.Mask"': '"B.Mask"',
        '"F.Paste"': '"B.Paste"',
        '"F.SilkS"': '"B.SilkS"',
        '"F.Fab"': '"B.Fab"',
        '"F.CrtYd"': '"B.CrtYd"',
        '"F.Adhes"': '"B.Adhes"',
    }
    for old, new in replacements.items():
        block = block.replace(old, new)
    return block


def with_pad_nets(block: str, pad_nets: dict[str, str]) -> str:
    ranges = block_ranges(block, "(pad ")
    pieces: list[str] = []
    cursor = 0
    for start, end, pad in ranges:
        pieces.append(block[cursor:start])
        pad_num = first_match(r'^\(pad "([^"]*)"', pad)
        if pad_num in pad_nets:
            pad = re.sub(r'\n\s+\(net "[^"]+"\)', "", pad)
            layers = re.search(r'\n(\s*)\(layers [^)]+\)', pad)
            if not layers:
                raise ValueError(f"pad {pad_num} has no layers block")
            insert_at = layers.end()
            indent = layers.group(1)
            pad = (
                pad[:insert_at]
                + f'\n{indent}(net "{q(pad_nets[pad_num])}")'
                + pad[insert_at:]
            )
        pieces.append(pad)
        cursor = end
    pieces.append(block[cursor:])
    return "".join(pieces)


def build_target_footprint(info: FootprintInfo) -> str:
    target = FOOTPRINT_MAP.get(info.source_lib_id)
    if not target:
        raise ValueError(f"no footprint mapping for {info.reference}: {info.source_lib_id}")
    if not target.path.exists():
        raise FileNotFoundError(target.path)
    block = target.path.read_text()
    block = re.sub(r'^\(footprint "([^"]+)"', f'(footprint "{q(target.lib_id)}"', block, count=1)
    if info.layer == "B.Cu":
        block = swap_to_bottom_layers(block)
    block = replace_property_block(block, "Reference", info.reference_property)
    block = replace_property_block(block, "Value", info.value_property)
    layer_match = re.search(r'\n\s*\(layer "[^"]+"\)', block)
    if not layer_match:
        raise ValueError(f"target footprint has no layer: {target.path}")
    extras = [f'\n\t(uuid "{new_uuid()}")', f"\n\t(at {info.at})"]
    if info.path:
        extras.append(f'\n\t(path "{q(info.path)}")')
    if info.sheetname:
        extras.append(f'\n\t(sheetname "{q(info.sheetname)}")')
    if info.sheetfile:
        extras.append(f'\n\t(sheetfile "{q(info.sheetfile)}")')
    block = block[: layer_match.end()] + "".join(extras) + block[layer_match.end() :]
    block = with_pad_nets(block, info.pad_nets)
    return block


def generate_pcb() -> list[FootprintInfo]:
    text = IMPORTED_PCB.read_text()
    ranges = block_ranges(text, "(footprint ")
    footprints = [parse_footprint(block) for _, _, block in ranges]
    replacements: list[str] = []
    for info in footprints:
        replacements.append(build_target_footprint(info))
    out: list[str] = []
    cursor = 0
    for (start, end, _), replacement in zip(ranges, replacements):
        out.append(text[cursor:start])
        out.append(replacement)
        cursor = end
    out.append(text[cursor:])
    final = "".join(out)
    final = final.replace('(generator "pcbnew")', '(generator "reference_design_importer")', 1)
    FINAL_PCB.write_text(final)
    return footprints


def extract_named_symbol(library: Path, symbol_name: str, embedded_name: str) -> str:
    text = library.read_text()
    block = None
    for _, _, candidate in block_ranges(text, f'(symbol "{symbol_name}"'):
        block = candidate
        break
    if block is None:
        raise ValueError(f"symbol {symbol_name} not found in {library}")
    return re.sub(
        rf'^\(symbol "{re.escape(symbol_name)}"',
        f'(symbol "{q(embedded_name)}"',
        block,
        count=1,
    )


def parse_symbol_pins(symbol_block: str) -> dict[str, tuple[float, float, float]]:
    pins: dict[str, tuple[float, float, float]] = {}
    for _, _, pin in block_ranges(symbol_block, "(pin "):
        number = first_match(r'\(number "([^"]+)"', pin)
        at = first_match(r'\(at ([^)]+)\)', pin)
        if not number or not at:
            continue
        vals = [float(v) for v in at.split()]
        if len(vals) == 2:
            vals.append(0.0)
        pins.setdefault(number, (vals[0], vals[1], vals[2]))
    return pins


def symbol_for_ref(reference: str) -> tuple[str, str]:
    if reference == "X2":
        return SYMBOL_MAP["X2"]
    if reference.startswith("FB"):
        return SYMBOL_MAP["FB"]
    prefix = re.match(r"[A-Z]+", reference)
    if not prefix:
        raise ValueError(f"cannot infer symbol for {reference}")
    if prefix.group(0).startswith("U"):
        return SYMBOL_MAP["U"]
    key = prefix.group(0)[0]
    if key not in SYMBOL_MAP:
        raise ValueError(f"no symbol mapping for {reference}")
    return SYMBOL_MAP[key]


def footprint_for(info: FootprintInfo) -> str:
    return FOOTPRINT_MAP[info.source_lib_id].lib_id


def symbol_instance(info: FootprintInfo, x: float, y: float) -> str:
    lib_id, _ = symbol_for_ref(info.reference)
    footprint = footprint_for(info)
    ref = info.reference
    value = info.value
    return f'''\
\t(symbol
\t\t(lib_id "{q(lib_id)}")
\t\t(at {x:.2f} {y:.2f} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "{q(ref)}"
\t\t\t(at {x + 3.81:.2f} {y - 1.27:.2f} 0)
\t\t\t(show_name no)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "{q(value)}"
\t\t\t(at {x + 3.81:.2f} {y + 1.27:.2f} 0)
\t\t\t(show_name no)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" "{q(footprint)}"
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(show_name no)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(show_name no)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(instances
\t\t\t(project "{q(DESIGN_NAME)}"
\t\t\t\t(path "/{new_uuid()}"
\t\t\t\t\t(reference "{q(ref)}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''


def label_for(net: str, x: float, y: float, rot: float) -> str:
    return f'''\
\t(label "{q(net)}"
\t\t(at {x:.2f} {y:.2f} {rot:.0f})
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify left bottom)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
'''


def wire_for(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'''\
\t(wire
\t\t(pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
\t\t(stroke (width 0) (type default))
\t\t(uuid "{new_uuid()}")
\t)
'''


def gnd_symbol_instance(index: int, x: float, y: float) -> str:
    ref = f"#PWR{index:03d}"
    return f'''\
\t(symbol
\t\t(lib_id "power:GND")
\t\t(at {x:.2f} {y:.2f} 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x:.2f} {y + 6.35:.2f} 0)
\t\t\t(show_name no)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Value" "GND"
\t\t\t(at {x + 2.54:.2f} {y + 1.27:.2f} 0)
\t\t\t(show_name no)
\t\t\t(effects
\t\t\t\t(font (size 1.27 1.27))
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(show_name no)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(show_name no)
\t\t\t(hide yes)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(instances
\t\t\t(project "{q(DESIGN_NAME)}"
\t\t\t\t(path "/{new_uuid()}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''


def label_or_ground_for(net: str, x: float, y: float, rot: float, pwr_index: list[int]) -> str:
    if net.upper() == "GND":
        symbol = gnd_symbol_instance(pwr_index[0], x, y)
        pwr_index[0] += 1
        return symbol
    return label_for(net, x, y, rot)


def net_label_for(net: str, x: float, y: float, justify: str = "left") -> str:
    return f'''\
\t(label "{q(net)}"
\t\t(at {x:.2f} {y:.2f} 0)
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify {justify} bottom)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
'''


def pin_label_items(
    info: FootprintInfo,
    x: float,
    y: float,
    symbol_pins: dict[str, dict[str, tuple[float, float, float]]],
    pwr_index: list[int],
) -> str:
    lib_id, bare = symbol_for_ref(info.reference)
    pins = symbol_pins[lib_id]
    items: list[str] = []
    connected_points: set[tuple[float, float, str]] = set()
    for pad_num, net in sorted(info.pad_nets.items(), key=lambda kv: (len(kv[0]), kv[0])):
        if pad_num not in pins:
            continue
        px, py, prot = pins[pad_num]
        sx = x + px
        sy = y - py
        point_key = (round(sx, 4), round(sy, 4), net)
        if point_key in connected_points:
            continue
        connected_points.add(point_key)
        if net.upper() == "GND":
            direction_y = -1 if sy <= y else 1
            ex = sx
            ey = sy + direction_y * 7.62
            items.append(wire_for(sx, sy, ex, ey))
            items.append(gnd_symbol_instance(pwr_index[0], ex, ey))
            pwr_index[0] += 1
            continue
        if info.reference.startswith("U"):
            direction_x = -1 if sx < x else 1
            wire_length = 7.62
        elif abs(px) > abs(py):
            direction_x = -1 if px < 0 else 1
            wire_length = 7.62
        else:
            direction_x = 1
            wire_length = 12.7
        ex = sx + direction_x * wire_length
        ey = sy
        items.append(wire_for(sx, sy, ex, ey))
        items.append(net_label_for(net, ex, ey, "right" if direction_x < 0 else "left"))
    return "".join(items)


def pin_point_for(
    info: FootprintInfo,
    pin_number: str,
    position: tuple[float, float],
    symbol_pins: dict[str, dict[str, tuple[float, float, float]]],
) -> tuple[float, float, float] | None:
    lib_id, _ = symbol_for_ref(info.reference)
    pin = symbol_pins[lib_id].get(pin_number)
    if pin is None:
        return None
    px, py, prot = pin
    return (position[0] + px, position[1] - py, prot)


def choose_component_anchor(
    info: FootprintInfo,
    net_to_u1_points: dict[str, list[tuple[float, float]]],
    net_to_refs: dict[str, set[str]],
    ref_to_info: dict[str, FootprintInfo],
) -> str:
    ordered_nets = [
        net
        for _, net in sorted(info.pad_nets.items(), key=lambda kv: (len(kv[0]), kv[0]))
        if net.upper() != "GND"
    ]
    for net in ordered_nets:
        if net in net_to_u1_points:
            return net

    seen_nets = set(ordered_nets)
    seen_refs = {info.reference}
    queue = list(ordered_nets)
    cluster_u1_nets: list[str] = []
    while queue:
        net = queue.pop(0)
        if net in net_to_u1_points:
            cluster_u1_nets.append(net)
        for ref in sorted(net_to_refs.get(net, set()), key=ref_sort_key):
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            for next_net in ref_to_info[ref].pad_nets.values():
                if next_net.upper() == "GND" or next_net in seen_nets:
                    continue
                seen_nets.add(next_net)
                queue.append(next_net)

    if cluster_u1_nets:
        return sorted(set(cluster_u1_nets))[0]
    if ordered_nets:
        return ordered_nets[0]
    return "GND"


def schematic_positions(
    footprints: list[FootprintInfo],
    symbol_pins: dict[str, dict[str, tuple[float, float, float]]],
) -> dict[str, tuple[float, float]]:
    ref_to_info = {fp.reference: fp for fp in footprints}
    u1 = next(fp for fp in footprints if fp.reference.startswith("U"))
    positions: dict[str, tuple[float, float]] = {u1.reference: U1_POSITION}

    net_to_refs: dict[str, set[str]] = {}
    for fp in footprints:
        for net in fp.pad_nets.values():
            net_to_refs.setdefault(net, set()).add(fp.reference)

    net_to_u1_points: dict[str, list[tuple[float, float]]] = {}
    for pin_number, net in u1.pad_nets.items():
        point = pin_point_for(u1, pin_number, U1_POSITION, symbol_pins)
        if point is None:
            continue
        px, py, _ = point
        net_to_u1_points.setdefault(net, []).append((px, py))

    anchor_for_ref: dict[str, str] = {}
    for fp in footprints:
        if fp.reference == u1.reference:
            continue
        anchor_for_ref[fp.reference] = choose_component_anchor(
            fp, net_to_u1_points, net_to_refs, ref_to_info
        )

    refs_by_anchor: dict[str, list[str]] = {}
    for ref, anchor in anchor_for_ref.items():
        refs_by_anchor.setdefault(anchor, []).append(ref)
    for refs in refs_by_anchor.values():
        refs.sort(key=ref_sort_key)

    groups_by_side: dict[int, list[dict[str, object]]] = {-1: [], 1: []}
    fallback_y = U1_POSITION[1] + 83.82
    for anchor, refs in sorted(refs_by_anchor.items()):
        points = net_to_u1_points.get(anchor)
        if points:
            ax = sum(x for x, _ in points) / len(points)
            ay = sum(y for _, y in points) / len(points)
            side = -1 if ax < U1_POSITION[0] else 1
        else:
            ax = U1_POSITION[0]
            ay = fallback_y
            fallback_y += 20.32
            side = 1
        groups_by_side[side].append({"anchor": anchor, "center_y": ay, "refs": refs})

    for side, groups in groups_by_side.items():
        groups.sort(key=lambda group: (float(group["center_y"]), str(group["anchor"])))
        column = 0
        previous_bottom = 12.7
        max_y = 190.5
        for group in groups:
            refs = group["refs"]
            assert isinstance(refs, list)
            height = max(12.7, len(refs) * SCHEMATIC_GROUP_SPACING)
            center_y = float(group["center_y"])
            top = center_y - height / 2
            if top < previous_bottom + 5.08:
                center_y += previous_bottom + 5.08 - top
            if center_y + height / 2 > max_y and previous_bottom > 12.7:
                column += 1
                previous_bottom = 12.7
                center_y = max(float(group["center_y"]), previous_bottom + 5.08 + height / 2)
            previous_bottom = center_y + height / 2
            x = round_grid(U1_POSITION[0] + side * (76.2 + column * 38.1))
            for index, ref in enumerate(refs):
                y = center_y + (index - (len(refs) - 1) / 2) * SCHEMATIC_GROUP_SPACING
                positions[ref] = (x, round_grid(y))

    return positions


def generate_schematic(footprints: list[FootprintInfo]) -> None:
    device_lib = Path("/usr/share/kicad/symbols/Device.kicad_sym")
    power_lib = Path("/usr/share/kicad/symbols/power.kicad_sym")
    nordic_lib = REPO / "symbols/nordic-lib-kicad-nrf54l.kicad_sym"
    needed = sorted({symbol_for_ref(fp.reference) for fp in footprints})
    needed.append(("power:GND", "GND"))
    symbol_blocks: dict[str, str] = {}
    symbol_pins: dict[str, dict[str, tuple[float, float, float]]] = {}
    for lib_id, bare in needed:
        if lib_id.startswith("nordic-lib-kicad"):
            source = nordic_lib
        elif lib_id.startswith("power:"):
            source = power_lib
        else:
            source = device_lib
        block = extract_named_symbol(source, bare, lib_id)
        symbol_blocks[lib_id] = block
        symbol_pins[lib_id] = parse_symbol_pins(block)

    ordered = sorted(footprints, key=lambda fp: (not fp.reference.startswith("U"), fp.reference))
    positions = schematic_positions(footprints, symbol_pins)

    symbols = []
    labels = []
    pwr_index = [1]
    for fp in ordered:
        x, y = positions[fp.reference]
        symbols.append(symbol_instance(fp, x, y))
        labels.append(pin_label_items(fp, x, y, symbol_pins, pwr_index))

    lib_symbols = "\n".join("\t\t" + line if line else "" for block in symbol_blocks.values() for line in block.splitlines())
    sch = f'''\
(kicad_sch
\t(version 20260306)
\t(generator "reference_design_importer")
\t(generator_version "0.1")
\t(uuid "{new_uuid()}")
\t(paper "A4")
\t(lib_symbols
{lib_symbols}
\t)
{"".join(symbols)}
{"".join(labels)}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
\t(embedded_fonts no)
)
'''
    FINAL_SCH.write_text(sch)


def write_project_files(footprints: list[FootprintInfo]) -> None:
    (GENERATED / "fp-lib-table").write_text(
        f'''\
(fp_lib_table
  (version 7)
  (lib (name "passives")(type "KiCad")(uri "{REPO}/footprints/passives.pretty")(options "")(descr "Nordic generated passives"))
  (lib (name "Crystal")(type "KiCad")(uri "/usr/share/kicad/footprints/Crystal.pretty")(options "")(descr "KiCad stock crystal footprints"))
  (lib (name "Package_DFN_QFN")(type "KiCad")(uri "/usr/share/kicad/footprints/Package_DFN_QFN.pretty")(options "")(descr "KiCad stock QFN footprints"))
)
'''
    )
    (GENERATED / "sym-lib-table").write_text(
        f'''\
(sym_lib_table
  (version 7)
  (lib (name "Device")(type "KiCad")(uri "/usr/share/kicad/symbols/Device.kicad_sym")(options "")(descr "KiCad stock device symbols"))
  (lib (name "power")(type "KiCad")(uri "/usr/share/kicad/symbols/power.kicad_sym")(options "")(descr "KiCad stock power symbols"))
  (lib (name "nordic-lib-kicad-nrf54l")(type "KiCad")(uri "{REPO}/symbols/nordic-lib-kicad-nrf54l.kicad_sym")(options "")(descr "Nordic nRF54L symbols"))
)
'''
    )
    source_project = REPO / "libmanagement/libmanagement.kicad_pro"
    if source_project.exists():
        shutil.copyfile(source_project, FINAL_PRO)
    else:
        FINAL_PRO.write_text('{"meta": {"version": 1}}\n')

    mapping = []
    for fp in sorted(footprints, key=lambda item: item.reference):
        target = FOOTPRINT_MAP[fp.source_lib_id]
        symbol_lib_id, _ = symbol_for_ref(fp.reference)
        mapping.append(
            {
                "reference": fp.reference,
                "value": fp.value,
                "source_footprint": fp.source_lib_id,
                "target_footprint": target.lib_id,
                "target_footprint_path": str(target.path),
                "symbol": symbol_lib_id,
                "side": fp.layer,
                "at": fp.at,
                "pad_nets": fp.pad_nets,
                "status": target.status,
            }
        )
    (MAPPINGS / "nrf54l15_qfaa_mapping.json").write_text(json.dumps(mapping, indent=2, sort_keys=True))


def validate_against_stage(footprints: list[FootprintInfo]) -> None:
    final = FINAL_PCB.read_text()
    final_infos = [parse_footprint(block) for _, _, block in block_ranges(final, "(footprint ")]
    by_ref = {info.reference: info for info in final_infos}
    errors = []
    for source in footprints:
        generated = by_ref.get(source.reference)
        if not generated:
            errors.append(f"missing generated footprint {source.reference}")
            continue
        if generated.value != source.value:
            errors.append(f"{source.reference}: value {generated.value!r} != {source.value!r}")
        if generated.layer != source.layer:
            errors.append(f"{source.reference}: layer {generated.layer!r} != {source.layer!r}")
        if generated.at != source.at:
            errors.append(f"{source.reference}: at {generated.at!r} != {source.at!r}")
    report = {
        "source_footprints": len(footprints),
        "generated_footprints": len(final_infos),
        "errors": errors,
    }
    (REPORTS / "placement-compare.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> int:
    ensure_dirs()
    run_import()
    footprints = generate_pcb()
    generate_schematic(footprints)
    write_project_files(footprints)
    validate_against_stage(footprints)
    print(f"generated {FINAL_PRO}")
    print(f"generated {FINAL_PCB}")
    print(f"generated {FINAL_SCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
