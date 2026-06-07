# Nordic Reference Design Importer

## Mission

This directory exists to regenerate clean KiCad projects from Nordic Altium
reference designs. The final artifacts must be fresh KiCad files, not cleaned-up
KiCad import output.

For each design, produce:

- A `.kicad_pcb` with this repository's footprints placed at the same component
  origins, sides, and orientations as the Altium board.
- A `.kicad_sch` with the same references, values, footprints, and electrical
  connectivity as the Altium schematic.
- A `.kicad_pro`, `fp-lib-table`, and `sym-lib-table` that resolve the generated
  design without relying on the user's global KiCad configuration.

The imported KiCad files from `kicad-cli` are staging data only. Use them as an
oracle for placement, layer, net, route, zone, board outline, and value data,
then build the final KiCad files from clean library parts.

## Tooling

- Use the local Python environment:

  ```bash
  /home/h/Documents/Nordic/nordic-lib-kicad/reference_design_importer/.venv/bin/python
  ```

- Prefer `uv` for Python dependency work. Do not install KiUtils globally.
- Use KiUtils from the local `.venv` for reading/writing KiCad files whenever it
  can parse the file format.
- KiCad CLI is the authoritative Altium board importer. Current local KiCad is
  `10.0.3`; in this install, `kicad-cli pcb import` exists, but there is no
  schematic import subcommand. If a future KiCad exposes schematic import via
  CLI, use it only for staging and still generate the final schematic fresh.
- Avoid regex edits of KiCad files except for narrow compatibility preprocessing
  when KiUtils cannot parse a known KiCad-version field. Prefer KiUtils objects
  or a real s-expression parser for generated output.

Known KiUtils compatibility issue in this workspace: the pinned KiUtils version
currently fails on KiCad 10 footprint entries containing
`(duplicate_pad_numbers_are_jumpers no)`. Before using `Board.from_file()` on a
KiCad 10 import, either update/patch the local `.venv` KiUtils to preserve that
field or create a clearly named normalized staging copy that removes only that
unsupported key. Keep the raw import intact for audit.

## Library Locations

Repository root:

```text
/home/h/Documents/Nordic/nordic-lib-kicad
```

Use these footprint libraries for generated boards:

- `passives`: `/home/h/Documents/Nordic/nordic-lib-kicad/footprints/passives.pretty`
- `nordic-lib-kicad-nrf54l`: `/home/h/Documents/Nordic/nordic-lib-kicad/footprints/nordic-lib-kicad-nrf54l.pretty`
- Other Nordic libraries under `/home/h/Documents/Nordic/nordic-lib-kicad/footprints/*.pretty`

Use these symbol libraries:

- Generic passives and crystals: KiCad `Device` symbols such as `Device:C_Small`,
  `Device:R_Small`, `Device:L_Small`, `Device:Crystal_Small`, and
  `Device:Crystal_Small_GND24`.
- Nordic ICs/modules: the matching local symbol in
  `/home/h/Documents/Nordic/nordic-lib-kicad/symbols`.
- If a required non-passive symbol does not exist yet, generate a simple local
  symbol for the output project. Pin placement can be rough, but pins must be on
  grid, not overlap, and preserve pin names/numbers/types. Do not invent pin
  numbering.

Do not assume `libmanagement/fp-lib-table` is sufficient for generated designs:
it currently lists Nordic footprint libraries but not `passives`. Generated
projects must include `passives` explicitly.

For generated project library tables, absolute library URIs are acceptable and
less fragile than copying `${KIPRJMOD}/../...` paths from `libmanagement`, since
reference design output directories are nested differently.

## First Input Design

The first source design is:

```text
/home/h/Documents/Nordic/nordic-lib-kicad/reference_design_importer/nrf54l15_10_05/nRF54L15-QFAA Reference Layout 0_8/Altium Designer files
```

Files present:

- `nRF54L15_qfaa_4L_config1.PrjPCB`
- `nRF54L15_qfaa_4L_config1.SchDoc`
- `nRF54L15_qfaa_4L_config1.PcbDoc`

Stage the board import with:

```bash
ROOT=/home/h/Documents/Nordic/nordic-lib-kicad
SRC="$ROOT/reference_design_importer/nrf54l15_10_05/nRF54L15-QFAA Reference Layout 0_8/Altium Designer files"
STAGE="$ROOT/reference_design_importer/nrf54l15_10_05/stage"
mkdir -p "$STAGE"
kicad-cli pcb import \
  --format altium \
  --report-format json \
  --report-file "$STAGE/pcb-import-report.json" \
  -o "$STAGE/imported.kicad_pcb" \
  "$SRC/nRF54L15_qfaa_4L_config1.PcbDoc"
```

The probe import of this board produced 22 footprints, 243 tracks, 72 vias, and
19 zones. It also printed warnings for unused Altium internal plane layers. Do
not ignore layer/import warnings; record them in the conversion notes and verify
that the real 4-layer stackup maps to `F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.

## nPM1300 Input Design

The nPM1300 source design is:

```text
/home/h/Documents/Nordic/nordic-lib-kicad/reference_design_importer/npm1300/nPM1300-QEAA-Reference-Layout-1_2/Altium Designer files
```

Use `config1` as the superset source unless the user asks for a narrower
configuration:

- `npm1300_qeaa_config1.PrjPCB`
- `npm1300_qeaa_config1.SchDoc`
- `npm1300_qeaa_config1.PcbDoc`

Stage the board import with:

```bash
ROOT=/home/h/Documents/Nordic/nordic-lib-kicad
SRC="$ROOT/reference_design_importer/npm1300/nPM1300-QEAA-Reference-Layout-1_2/Altium Designer files"
STAGE="$ROOT/reference_design_importer/npm1300/stage"
mkdir -p "$STAGE"
kicad-cli pcb import \
  --format altium \
  --report-format json \
  --report-file "$STAGE/pcb-import-report.json" \
  -o "$STAGE/imported.kicad_pcb" \
  "$SRC/npm1300_qeaa_config1.PcbDoc"
```

The probe import of `npm1300_qeaa_config1` produced 22 footprints, 171 tracks,
52 vias, and 7 zones. KiCad again reported unmapped Altium internal plane
layers; record these warnings and verify the real 4-layer stackup maps to
`F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.

## Required Pipeline

1. Create a per-design output tree.

   Suggested layout:

   ```text
   <design>/
     stage/        # raw and normalized KiCad imports, disposable but auditable
     mappings/     # footprint and symbol mapping YAML/JSON
     generated/    # final KiCad project
     reports/      # ERC/DRC/diff reports
   ```

2. Import the Altium board to staging with `kicad-cli pcb import`.

3. Extract source facts from staging:

   - Footprint reference, value, library ID, side, `(at x y angle)`, lock state,
     DNP/exclude flags, and text visibility.
   - Pad numbers, pad names where available, and pad net assignments.
   - Board outline, stackup/layers, tracks, vias, zones, net names, rules, and
     design origin.
   - Any import report warnings/errors.

4. Extract schematic facts from the Altium schematic or a schematic staging
   source:

   - Component reference, value, source symbol, footprint field, and fields such
     as MPN/DNP if present.
   - Pin-to-net connectivity.
   - Power symbols, no-connects, labels, harnesses/buses, and sheet structure.

5. Build explicit mapping files. Do not hard-code mappings only in Python.

   Each footprint mapping entry should contain:

   - Source Altium/KiCad footprint aliases.
   - Target KiCad library ID.
   - Any origin or rotation correction needed to align pin 1 and pad centers.
   - A pad-number compatibility note, especially for ICs and crystals.
   - Whether the mapping is verified, provisional, or blocked.

6. Generate the final `.kicad_pcb` from clean library footprints.

   - Load the target footprint from this repository's `.pretty` library.
   - Set the reference, value, side, position, and orientation from the source.
   - Carry pad net assignments by pad number only after confirming pad-number
     compatibility.
   - Preserve board outline, routes, vias, zones, copper text, and stackup when
     the goal is a usable reference layout.
   - Keep the final footprint library IDs pointed at this repository, not at
     imported Altium library names or stock KiCad libraries.

7. Generate the final `.kicad_sch`.

   - Use `Device:C_Small`, `Device:R_Small`, `Device:L_Small`,
     `Device:Crystal_Small`, or `Device:Crystal_Small_GND24` for generic parts.
   - Use the matching local Nordic symbol for Nordic ICs/modules.
   - Put symbols on a clear grid with no overlaps. The schematic does not need
     to preserve Altium XY coordinates, but it must preserve references, values,
     footprint fields, and connectivity.
   - Prefer clear local labels over long point-to-point wires when recreating
     connectivity from net data.

8. Validate and diff.

   Required checks:

   ```bash
   kicad-cli sch erc --format json -o reports/erc.json generated/<design>.kicad_sch
   kicad-cli pcb drc --format json --refill-zones -o reports/drc.json generated/<design>.kicad_pcb
   kicad-cli sch export netlist --format kicadsexpr -o reports/generated.net generated/<design>.kicad_sch
   kicad-cli pcb export pos --format csv --units mm -o reports/generated-pos.csv generated/<design>.kicad_pcb
   ```

   Also produce a custom comparison against staging that verifies every source
   reference exists in the final board with the same value, side, X/Y coordinate,
   and orientation after any documented origin/rotation correction. Fail the run
   on missing refs, changed values, unresolved footprint mappings, unresolved
   symbol mappings, or pad-count mismatches.

## Footprint Mapping Rules

Passive packages should map by physical package, not by Altium library prefix.
The same package can appear under aliases such as `Parts$:...`, `Passive:...`,
or a bare imported library name.

Seed mappings observed in the first design:

| Source footprint alias | Target footprint |
| --- | --- |
| `CAPC0603X03L_C` | `passives:C_0201_0603Metric_L` |
| `Parts$:CAPC0603X03L_C` | `passives:C_0201_0603Metric_L` |
| `Passive:CAPC0603X03L_C` | `passives:C_0201_0603Metric_L` |
| `CAPC1005X04L` | `passives:C_0402_1005Metric_L` |
| `RESC0603X03L_C` | `passives:R_0201_0603Metric_L` |
| `INDC0603X03L_C` | `passives:L_0201_0603Metric_L` |
| `Passive:INDC0603X03L_C` | `passives:L_0201_0603Metric_L` |
| `0603:INDC1608X06L` | `passives:L_0603_1608Metric_L` |

Unresolved mappings observed in the first design:

- `Parts$:XTAL_2012`
- `Parts$:BT-XTAL_2016`
- `Misc:QFN40P600X600X90-48N` for `U1` value `nRF54L15-QFAA`

Do not silently map `Misc:QFN40P600X600X90-48N` to the local
`nordic-lib-kicad-nrf54l:QFN-52-1EP_6x6mm_P0.4mm_EP4.7x4.7mm_ThermalVias`.
The imported source footprint is a 48-pin QFN plus exposed pad. The local
footprint name says QFN-52. Verify the actual Nordic package, pad count, pad
numbers, exposed-pad handling, and symbol pin count first. If the correct QFAA
footprint is missing, create or add it before finalizing the conversion.

Do not keep stock KiCad crystal footprints in the final board unless the user
explicitly approves that exception. Add local crystal footprints or mark the
conversion blocked on unresolved footprint mappings.

nPM1300 config1 seed mappings:

| Source footprint alias | Target footprint |
| --- | --- |
| `AltiumLib:CAPC1608X06L` | `passives:C_0603_1608Metric_L` |
| `CAPC1608X06L:CAPC1608X06L` | `passives:C_0603_1608Metric_L` |
| `Parts$:CAPC1608X06L` | `passives:C_0603_1608Metric_L` |
| `CAPC0603X03L_C:CAPC0603X03L_C` | `passives:C_0201_0603Metric_L` |
| `RESC0603X03L_C:RESC0603X03L_C` | `passives:R_0201_0603Metric_L` |
| `Parts$:INDC2016X10N` | `passives:L_0806_2016Metric_L` |
| `2 pin starpoint:2 PIN STARPOINT` | `NetTie:NetTie-2_SMD_Pad0.5mm` |
| `Nordic_QFN50P500X500X90-33N:Nordic_QFN50P500X500X90-33N` | `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.6x3.6mm_ThermalVias` |

For nPM1300-QEAA, the local symbol
`nordic-lib-kicad-npm:nPM1300-QEXX` already points to the stock KiCad QFN-32
footprint above. The imported source footprint has pads `1` through `33`, where
`33` is the exposed pad/GND. The stock KiCad footprint has matching pad numbers,
including repeated pad `33` for the exposed pad and thermal vias, so assigning
nets by pad number preserves the intended GND exposed-pad connectivity.

## Symbol Mapping Rules

Passives:

- Capacitors: `Device:C_Small`
- Resistors: `Device:R_Small` unless matching an existing Nordic block requires
  `Device:R_Small_US`
- Inductors: `Device:L_Small`
- Two-pin crystals: `Device:Crystal_Small`
- Four-pad grounded crystals: `Device:Crystal_Small_GND24`

Nordic parts:

- Prefer an exact local symbol when present.
- For nPM1300-QEAA, use `nordic-lib-kicad-npm:nPM1300-QEXX` and verify that all
  33 source pads are present before generating the schematic and board.
- If only a family/package wildcard exists, such as
  `nordic-lib-kicad-nrf54l:nRF54L15-QFXX`, verify it covers the exact package
  value from the Altium source before using it for a QFAA/QFxx-specific design.
- Never use a symbol whose pin numbers do not match the footprint pads and
  schematic netlist.

Generated temporary symbols:

- Place pins on a 2.54 mm grid.
- Keep pin text readable and non-overlapping.
- Group pins by function when the source data makes that obvious.
- Use passive pins for generated simple two-terminal parts only when no better
  typed symbol exists.
- Put generated symbols in the output project or a clearly named generated
  symbol library, not mixed into the main Nordic symbol libraries unless the user
  asks for that library update.

## Schematic Layout Reference From `libmanagement`

Use `/home/h/Documents/Nordic/nordic-lib-kicad/libmanagement/libmanagement.kicad_sch`
as the human-laid style reference for this nRF54L/QF design family, not as an
import source. It is useful because it shows how the same electrical block is
made readable after cleanup.

Observed `libmanagement` layout facts:

- It uses a normal A4 sheet with 20 component symbols and 6 `power:GND`
  symbols. The board-derived first generated schematic has 22 component symbols
  because the PCB source also includes `X1` and `X2`.
- `U1` is placed at `71.12 105.41 0`. Its reference is at the symbol origin and
  its value is at `71.12 107.95 0`.
- Most passives are upright at orientation `0`. Reference/value fields are
  placed to the right of the symbol, offset by about `+2.54 mm` in X and
  `-1.27 mm` / `+1.27 mm` in Y. Example: `C1` is at `82.55 38.10 0`,
  reference at `85.09 36.8362 0`, and value `10uF` at `85.09 39.3762 0`.
- The RF chain is intentionally horizontal by rotating the series parts:
  `L2`, `L3`, and `L4` are at `113.03 105.41 90`,
  `123.19 105.41 90`, and `133.35 105.41 90`; `R1` is at
  `116.84 148.59 90`. Their reference/value fields are also rotated `90`.
- Values use ASCII units such as `uF` and `uH`. Do not emit micro-symbol unit
  variants in generated outputs.

Generated schematic layout rules learned from the comparison:

- Keep the generator's output on the normal page size. It is acceptable for the
  rough generated schematic to overflow A4 because manual cleanup is expected.
- Group symbols by their connection to `U1` or by a short connected component
  chain, but do not try to preserve Altium schematic coordinates.
- Use left-aligned visible reference/value fields for generated symbols. The
  current rough-layout convention is `x + 3.81 mm`, `y - 1.27 mm` for reference
  and `x + 3.81 mm`, `y + 1.27 mm` for value. This is less elegant than the
  hand-laid centered fields in `libmanagement`, but it prevents long values from
  centering across wires during rough placement.
- Use horizontal labels by default. Do not rotate net labels into vertical text
  stacks unless deliberately recreating a hand-routed RF chain.
- For vertical passive symbols, put enough horizontal lead between the pin and
  label so the net name does not collide with the reference/value fields; the
  first generator uses `12.7 mm` for these label leads.
- Route horizontal-pin symbols outward from the pin side. For example, a
  two-pin crystal's left pin must route left and its right pin must route right;
  routing both pins to the same side can short the crystal pins in the generated
  netlist.
- For duplicate co-located ground pins, such as the two grounded pins on
  `Device:Crystal_GND24_Small`, one `power:GND` symbol at the shared pin point
  is enough if KiCad connects all co-located symbol pins.
- Use `power:GND` symbols for ground, not plain `GND` labels. Keep the GND
  symbol orientation at `0` so the ground marker points down, and place the
  visible `GND` value text off to the side with left justification.
- `libmanagement` uses fewer shared ground symbols for a polished schematic.
  A generated schematic may use more local GND symbols to preserve connectivity
  mechanically, but a cleanup pass should consolidate them where readability
  improves.

## Completion Criteria

A conversion is done only when:

- The final board opens in KiCad without missing libraries.
- The final schematic opens in KiCad without missing libraries.
- Every source component reference is present in schematic and PCB.
- Values match the source design exactly, normalized only for encoding where
  needed, for example `uF` vs the source micro symbol.
- Board footprint side, X/Y, and rotation match the source after documented
  correction.
- All footprint and symbol mappings are verified.
- ERC, DRC, netlist export, and position export have been run and reports saved.
- Any remaining warnings are explained in `reports/conversion-notes.md`.
