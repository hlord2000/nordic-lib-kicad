# nRF54L15-QFAA Conversion Notes

Generated from:

```text
nrf54l15_10_05/nRF54L15-QFAA Reference Layout 0_8/Altium Designer files/nRF54L15_qfaa_4L_config1.PcbDoc
```

Output project:

```text
nrf54l15_10_05/generated/nRF54L15_qfaa_4L_config1.kicad_pro
nrf54l15_10_05/generated/nRF54L15_qfaa_4L_config1.kicad_pcb
nrf54l15_10_05/generated/nRF54L15_qfaa_4L_config1.kicad_sch
```

## Footprints

- Passives map to `/home/h/Documents/Nordic/nordic-lib-kicad/footprints/passives.pretty`.
- `X1` maps to stock `Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm`.
- `X2` maps to stock `Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm`.
- `U1` maps to stock `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm_ThermalVias`.

All 22 source footprints were regenerated with mapped KiCad footprints. Reference,
value, side, position, and rotation match the staged import; see
`placement-compare.json`.

## Reports

- `stage-drc.json`: DRC on the raw KiCad Altium import. It reports 497 violations.
- `drc.json`: DRC on the generated board. It reports 458 violations, mostly inherited
  board-rule/geometry issues such as 0.15 mm tracks against a 0.20 mm minimum,
  soldermask/silkscreen clearances, and QFN thermal-via drill constraints.
- `erc.json`: ERC on the generated net-labeled schematic. It reports 35 violations:
  mostly isolated labels on one-pin nets, plus power-drive warnings.
- `generated.net`: schematic netlist export.
- `generated-pos.csv`: generated board position export.
- `generated-schematic.pdf`: generated schematic PDF.
- `generated-pcb-top.png`: rendered top-side board preview.

The schematic generator now places components by shared net/cluster instead of
a flat grid. For example, the VDD decouplers, DECA/DECD parts, RF matching
chain, and crystal parts are grouped near their associated U1-side nets. GND
pads are terminated with 15 `power:GND` symbols instead of plain `GND` labels.
The generated schematic stays on the normal A4 sheet even if the rough generated
placement overflows; manual schematic cleanup is expected.

Values are normalized to ASCII units (`uF`, `uH`) rather than micro-symbol
variants. Visible reference/value fields are left-aligned beside each generated
symbol, horizontal net labels are used by default, and vertical passive labels
use longer leads so values do not run directly into net names. Horizontal-pin
symbols, including `X1` and `X2`, route outward from their pin side to avoid
shorting both crystal pins through a generated label wire.

The generated schematic netlist was compared back to the staged board-derived
pad mapping: 93 expected component pins, 93 actual component pins, 0 missing,
and 0 wrong net assignments.

## Import Warnings

KiCad reported unmapped Altium `Internal Plane 1` through `Internal Plane 16`
layers during staging. The actual copper stackup imported as `F.Cu`, `In1.Cu`,
`In2.Cu`, and `B.Cu`.
