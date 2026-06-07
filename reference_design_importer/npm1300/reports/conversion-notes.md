# nPM1300-QEAA Config1 Conversion Notes

Generated from:

```text
npm1300/nPM1300-QEAA-Reference-Layout-1_2/Altium Designer files/npm1300_qeaa_config1.PcbDoc
```

Output project:

```text
npm1300/generated/npm1300_qeaa_config1.kicad_pro
npm1300/generated/npm1300_qeaa_config1.kicad_pcb
npm1300/generated/npm1300_qeaa_config1.kicad_sch
```

## Footprints

- Passives map to `/home/h/Documents/Nordic/nordic-lib-kicad/footprints/passives.pretty`.
- `U1` maps to stock `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.6x3.6mm_ThermalVias`, matching the footprint field already used by the local `nordic-lib-kicad-npm:nPM1300-QEXX` symbol.
- `NT1` and `NT2` map to stock `NetTie:NetTie-2_SMD_Pad0.5mm`.

All 22 source footprints were regenerated with mapped KiCad footprints. Reference,
value, side, position, and rotation match the staged import; see
`placement-compare.json`.

## Reports

- `stage-drc.json`: DRC on the raw KiCad Altium import. It reports 313 violations.
- `drc.json`: DRC on the generated board. It reports 275 violations and 2 unconnected items, mostly inherited geometry/rule issues from the compact reference layout and the substituted clean footprints.
- `erc.json`: ERC on the generated net-labeled schematic. It reports 23 violations, mostly rough-schematic power/passive warnings.
- `generated.net`: schematic netlist export.
- `schematic-net-compare.json`: schematic netlist compared back to the staged board-derived pad mapping.
- `generated-pos.csv`: generated board position export.
- `generated-schematic.pdf`: generated schematic PDF.
- `generated-pcb-top.svg` and `generated-pcb-top.png`: rendered top-side board preview.

The schematic generator places components by shared net/cluster rather than a
flat grid. Buck inductors, output capacitors, VBUS/VDDIO parts, VSET resistors,
and PVSS net ties are grouped near their associated `U1` nets. GND pads are
terminated with 14 `power:GND` symbols instead of plain `GND` labels. The
generated schematic stays on A4 even where rough placement overflows.

Values are normalized to ASCII units (`uF`, `uH`) rather than micro-symbol
variants. Visible reference/value fields are left-aligned beside each generated
symbol, horizontal net labels are used by default, and vertical passive labels
use longer leads so values do not run directly into net names.

The generated schematic netlist was compared back to the staged board-derived
pad mapping: 75 expected component pins, 75 actual component pins, 0 missing,
and 0 wrong net assignments.

## Import Warnings

KiCad reported unmapped Altium `Internal Plane 1` through `Internal Plane 16`
layers during staging. The actual copper stackup imported as `F.Cu`, `In1.Cu`,
`In2.Cu`, and `B.Cu`.
