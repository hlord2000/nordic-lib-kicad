# Symbol Arrangement Guide

This document summarizes the current symbol layout conventions in `symbols/*.kicad_sym`.
It is based on direct parsing of the KiCad S-expression files, not on `kiutils`.

## Reading Symbol Layout

- Pin side is encoded by pin angle: `0` means left edge, `180` means right edge, `270` means top edge, and `90` means bottom edge.
- Left and right pins are read top-to-bottom by descending `Y`. Top and bottom pins are read left-to-right by ascending `X`.
- KiCad nested symbol names such as `_0_0`, `_1_0`, `_2_0` are part of the raw symbol storage. `_0_0` commonly holds pins shared by the visible unit; `_1_0`, `_2_0`, etc. hold unit-specific pins. `_1_1` and similar blocks are usually graphics or alternate body blocks.
- Symbols that use `(extends "...")` inherit the base symbol geometry and usually only change properties such as value, description, footprint, filters, or datasheet.

## General Arrangement

### SoC and SiP Symbols

- The main I/O edge is usually the left edge. It starts with clock/crystal pins (`XC1`, `XC2`, sometimes `XL1`, `XL2` as pin names or alternates), then GPIO groups in port order.
- USB-capable SoCs place `D+` and `D-` at the upper left before or near the crystal pins.
- NFC-capable SoCs keep the NFC pair embedded in the GPIO sequence:
  - nRF52: `P0.09`/`P0.10` or `P0.09/NFC1`/`P0.10/NFC2` on the left.
  - nRF53: `P0.02`/`P0.03` or `P0.02/NFC1`/`P0.03/NFC2`.
  - nRF54L and BL/BM15x modules: `P1.02`/`P1.03` with `NFC1`/`NFC2` alternates.
  - BM20x modules: `P2.10/NFC1` and `P2.11/NFC2` at the lower right.
- RF antenna pins are normally on the right. For most SoCs `ANT` is at the right-center area, commonly around `y=0`. nRF9 SiPs place `ANT` near the upper right and also expose `GPS` on the right. RF FEM/module symbols may use `TRX`, `ANT1`, `ANT2`, or `OUT_ANT` instead.
- Debug/reset pins are usually at the lower right in this order from top to bottom: `~{RESET}`, `SWDCLK`, `SWDIO`. Exceptions are modules whose castellated or LGA edge grouping puts debug on the left, and nRF54LS05A where `P1.30` and `P1.29` carry `SWDCLK` and `SWDIO` as alternates.

### Power, Ground, and Regulator Pins

- Power input pins are usually on the top edge. Grounds are usually on the bottom edge.
- Duplicate package supply pins are hidden and stacked at the same coordinate as a visible representative supply pin.
- Duplicate grounds, exposed pads, shield grounds, and analog grounds are hidden and stacked at the visible bottom ground pin unless a distinct net is required.
- nRF52 decoupling/regulator pins use the right edge for `DEC*` pins and the top edge for `DCC`. USB/high-voltage variants add `VBUS`, `VDDH`, `DECUSB`, and sometimes `DCCH`.
- nRF53 places several regulator/decoupling pins interleaved with I/O: `DCC`, `DECR`, `DECRF`, `DCCD`, and `DECD` on the left side region; `DECA`, `DECN`, `DCCH`, and `DECUSB` on the right side region.
- nRF54L places decoupling/regulator pins at the top of the right edge, generally `DECA`, `DECRF`, `DECD`, `DCC`, then `ANT`, then reset/SWD.
- nRF54LV adds charge-pump/low-voltage pins on the right: `DECA`, `DECB`, `DECRF`, `DECD`, `DCC`, `CFLYH`, `CFLYL`, then `ANT` and reset/SWD.
- nPM PMIC symbols place source supplies on the top or upper left, regulator outputs and switch nodes on the right, configuration/control pins on the left, and grounds on the bottom.
- nRF7 Wi-Fi companion symbols place digital host/control pins on the left, RF/buck/analog supply pins on the right, supplies on the top, and ground on the bottom.

### Alternate Modes

- Primary pin names should remain the package or port names when that is what the existing symbol uses. Peripheral functions should be expressed as KiCad `alternate` entries.
- Current alternate-mode families include:
  - nRF52: `AIN`, `XL`, `NFC`, and trace alternates on larger parts.
  - nRF53: `AIN`, `XL`, `NFC`, `TWI`, `QSPI`, high-speed SPI, and trace alternates, mainly on `nRF5340-QKXX`.
  - nRF54L and nRF54 modules: `AIN`, `ASI`, `ASO`, `RADIO`, `QSPI`, `SPIM`, `SPIS`, `UARTE`, `TRACE`, `SWO`, and package-specific functions.
  - nRF54LV: `AIN`, `TRACE`, `ASI`, `ASO`, `FLPR`, `RADIO`, `QSPI`, `SWO`, and crystal alternates depending on package.
  - nRF7: QSPI pins expose SPI alternate names.
  - nPM2100: `VOUTLDO` has `LSOUT` as an alternate.

## Per-Library Symbol Summary

### `nordic-lib-kicad-npm.kicad_sym`

- `nPM1100-CAXX`: PMIC/charger BGA. Left: USB `D+`/`D-`, NTC/config/charge pins. Right: `DEC`, `VOUTBSET0`, `VOUTBSET1`, `VOUTB`, `SW`, mode/ISET/shutdown pins. Top: `VBAT`, `VBUS`, `VSYS`. Bottom: stacked `VSS`.
- `nPM1100-QDXX`: Same arrangement as `nPM1100-CAXX`, with QFN grounding split as visible `AVSS` and `PVSS`.
- `nPM1300-CAXX`: Left: `VBUS`, USB-C CC pins, LEDs, GPIO/I2C, `VSET1`, `VSET2`, `SHPHLD`. Right: `VBUSOUT`, buck `VOUT1/SW1/PVSS1`, buck `VOUT2/SW2/PVSS2`, LDO/load-switch paths, `VBAT`, `NTC`. Top: `VDDIO`, `PVDD`, `VSYS`. Bottom: stacked `VSS`.
- `nPM1300-QEXX`: Same logical grouping as `nPM1300-CAXX`; bottom ground is visible `AVSS`.
- `nPM2100-CAXX`: Left: `VBAT`, `SW`, `VSET`, I2C, GPIO. Right: `VOUT`, `VOUTLDO`, `VINT`, `SHPHLD`, `PG/RESET`, `SYSGDEN`. Bottom: `PVSS` with hidden analog grounds stacked. `VOUTLDO` has `LSOUT` alternate.
- `nPM2100-QEXX`: Same as `nPM2100-CAXX`; bottom stack also includes exposed pad/analog ground pins.
- `nPM6001-CAXX`: Left: enable/interrupt/ready, `BUCK_MODE0..2`, GPIO supply, GPIO, TWI supply, SDA/SCL. Right: repeated buck output pairs `SW0/VO0` through `SW3/VO3`, then `VIN_LDO0/VLDO0` and `VIN_LDO1/VLDO1`. Top: `VIN` and `VIN_BUCK0..3`. Bottom: stacked `VSS`.

### `nordic-lib-kicad-nrf21.kicad_sym`

- `nRF21540-QDXX`: RF FEM. Left: mode/RX/TX/PDN/SPI controls plus `TRX` and `ANT_SEL`. Right: `ANT1` and `ANT2`. Top: stacked `VDD`. Bottom: stacked `VSS`.

### `nordic-lib-kicad-nrf52.kicad_sym`

- `nRF52805-CAXX`: Compact WLCSP. Left: `XC1`, `XC2`, selected `P0` GPIO. Right: `DEC1`, `DEC2`, `DEC4`, `ANT`, then `~{RESET}`, `SWDCLK`, `SWDIO`. Top: stacked `VDD` and `DCC`. Bottom: stacked `VSS`.
- `nRF52810-CAXX`: Same pattern as `nRF52805-CAXX`, with a larger selected `P0` set.
- `nRF52810-QCXX`: Same pattern; right decoupling includes `DEC3`.
- `nRF52810-QFXX`: Same pattern with the broadest `P0` exposure for the nRF52810 package.
- `nRF52820-CFXX`: USB-capable. Left: `D+`, `D-`, `XC1`, `XC2`, selected GPIO. Right: `DEC1`, `DEC4`, `DEC5`, `DEC6`, `DECUSB`, `ANT`, reset/SWD. Top: `VBUS`, stacked `VDD`, `DCC`, `VDDH`. Bottom: stacked `VSS`.
- `nRF52820-QDXX`: Same as `nRF52820-CFXX`, with `DEC3` also present on the right.
- `nRF52832-CIXX`: NFC-capable. Left: crystals, `P0.00`, `P0.01`, NFC pair `P0.09`/`P0.10`, then remaining GPIO. Right: `DEC1..DEC4`, `ANT`, selected GPIO, reset/SWD. Top: stacked `VDD` and `DCC`. Bottom: stacked `VSS`.
- `nRF52832-QFXX`: Same layout as `nRF52832-CIXX` with QFN pin numbers and hidden QFN supply/ground stacks.
- `nRF52833-CJXX`: USB and NFC. Left: USB, crystals, NFC pair, expanded `P0`/`P1` GPIO. Right: decoupling including `DECUSB`, `ANT`, selected GPIO, reset/SWD. Top: `VBUS`, stacked `VDD`, `DCC`, `VDDH`. Bottom: stacked `VSS`.
- `nRF52833-QDXX`: Compact USB/NFC package. Same grouping as `nRF52833-CJXX`, with a smaller GPIO set and right-side `DEC1`, `DEC3`, `DEC4`, `DEC5`, `DEC6`, `DECUSB`.
- `nRF52833-QIXX`: Expanded USB/NFC aQFN layout, same grouping as `nRF52833-CJXX`.
- `nRF52840-CKXX`: USB/NFC/QSPI-capable CSP. Left: USB, crystals, NFC pair, expanded GPIO. Right: `DEC1`, `DEC4`, `DEC5/NC`, `DEC6`, `DECUSB`, `ANT`, selected GPIO, reset/SWD. Top: `VBUS`, stacked `VDD`, `DCC`, `VDDH`, `DCCH`.
- `nRF52840-QFXX`: QFN-48 variant. Left: crystals, NFC pair, GPIO. Right: `DEC1`, `DEC3`, `DEC4`, `DEC6`, `ANT`, selected GPIO, reset/SWD. Top: stacked `VDD` and `DCC`.
- `nRF52840-QIXX`: Expanded aQFN layout. Left: USB, crystals, NFC pair, expanded GPIO. Right: `DEC1..DEC6`, `DECUSB`, `ANT`, selected GPIO, reset/SWD. Top: `VBUS`, stacked `VDD`, `DCC`, `VDDH`, `DCCH`.
- `nRF52811-CAXX`: Extends `nRF52810-CAXX`.
- `nRF52811-QCXX`: Extends `nRF52810-QCXX`.
- `nRF52811-QFXX`: Extends `nRF52810-QFXX`.

### `nordic-lib-kicad-nrf52-modules.kicad_sym`

- `E73-2G4M08S1C`: Module. Left: `P0.18/~{RESET}`, `SWDCLK`, `SWDIO`, `VBUS`, USB, selected `P0` GPIO. Right: analog-capable GPIO, `P0.09/NFC1`, `P0.10/NFC2`, and `P1` GPIO. Top: `VDD`, `VDDH`, `DCCH`. Bottom: stacked `GND`.
- `ISP1907-LL`: Module. Left: `P0.21/~{RESET}`, `SWDCLK`, `SWDIO`, `OUT_MOD`, `OUT_ANT`. Right: selected GPIO. Top: `VCC`. Bottom: heavily stacked `VSS`.

### `nordic-lib-kicad-nrf53.kicad_sym`

- `nRF5340-CLXX`: Two-unit SoC layout. I/O unit uses left-side crystals, low-frequency crystal pins in names, USB, NFC pair, analog-capable GPIO, and interleaved regulator pins. Right side holds higher GPIO groups, `DECA`, `DECN`, `DCCH`, `DECUSB`, `ANT`, and reset/SWD. Top supplies are `VDD`, `VDDH`, `VBUS`; bottom is stacked `VSS`.
- `nRF5340-QKXX`: Same overall layout as `nRF5340-CLXX`, but more functions are represented as alternates: `XL`, `NFC`, `AIN`, `TWI`, `QSPI`, high-speed SPI, and trace. Reset/SWD is lower right, with `~{RESET}` above `SWDIO` and `SWDCLK`.

### `nordic-lib-kicad-nrf53-modules.kicad_sym`

- `E83-2G4M03S`: Module. Left: large GPIO block including QSPI and I2C-named pins. Right: `VBUS`, USB, `P0.00/XL1`, `P0.01/XL2`, `P0.02/NFC1`, `P0.03/NFC2`, analog-capable GPIO, and debug/reset. Top: `VDDH`, `VDD`. Bottom: stacked `GND`.
- `ISP2053-AX`: Module. Left: GPIO block with `P0.02/NFC1` and `P0.03/NFC2` near the lower left. Right: `VBUS`, USB, `OUT_ANT`, `OUT_MOD`, `SWDIO`, `SWDCLK`, `~{RST}`, and trace/GPIO pins. Top: `DCCH`, `VDDH`, `VDD`. Bottom: stacked `VSS`.

### `nordic-lib-kicad-nrf54l.kicad_sym`

- `nRF54L15-CAXX`: WLCSP. Left: `XC1`, `XC2`, GPIO with `P1.02`/`P1.03` carrying NFC alternates. Right: `DECA`, `DECRF`, `DECD`, `DCC`, `ANT`, `~{RESET}`, `SWDCLK`, `SWDIO`. Top: stacked `VDD`. Bottom: stacked `VSS`.
- `nRF54L15-QDXX`: Same functional order as `nRF54L15-CAXX`, with the QFN-40 GPIO subset and hidden QFN supply/ground stacks.
- `nRF54L15-QFXX`: Same functional order as `nRF54L15-CAXX`, with the QFN-48 GPIO set.
- `nRF54L15-QGXX`: Same functional order as `nRF54L15-CAXX`, with the largest QFN GPIO set.
- `nRF54LM20A-PAXX`: Multi-unit FCCSP symbol. Unit 1 carries supplies, `VBUS`, crystals, USB, `TXRTUNE`, `DECUSB`, and hidden supply/ground stacks. Other units expose large GPIO groups on the right, with `DCC`, `DECD`, `DECA`, and `DECRF` interleaved by group, `ANT` before reset/SWD, and `~{RESET}`, `SWDCLK`, `SWDIO` on the lower right.
- `nRF54LM20A-QGAA`: Multi-unit QFN symbol. Left: `VBUS`, crystals, USB, `TXRTUNE`, `DECUSB`. Right: `DCC`, GPIO groups, `DECD`, `DECA`, `DECRF`, `ANT`, reset/SWD. Top: stacked `VDD`. Bottom: stacked `VSS`.
- `nRF54LM20A-QGXX`: Same layout as `nRF54LM20A-QGAA`.
- `nRF54LS05A-QFXX`: Entry nRF54L QFN. Left: crystals and GPIO. Right: `DECA`, `DECRF`, `DECD`, `DCC`, `ANT`, `~{RESET}`, `P1.30` with `SWDCLK` alternate, and `P1.29` with `SWDIO` alternate. Top: `VDD`. Bottom: stacked `VSS`.
- `nRF54LV10A-CAAA`: CSP low-voltage variant. Left: crystals and GPIO. Right: `DECA`, `DECB`, `DECRF`, `DECD`, `DCC`, `CFLYH`, `CFLYL`, `ANT`, reset/SWD. Top: `VDDL`. Bottom: stacked `VSS`.
- `nRF54LV10A-CAXX`: Same as `nRF54LV10A-CAAA`.
- `nRF54LV10A-QFAA`: QFN low-voltage variant. Same right-side regulator order as the CSP variant, with a larger visible GPIO set and broad alternates including `FLPR`, `RADIO`, `QSPI`, and trace.
- `nRF54LV10A-QFXX`: Same as `nRF54LV10A-QFAA`.
- `nRF54L05-QDXX`: Extends `nRF54L15-QDXX`.
- `nRF54L05-QFXX`: Extends `nRF54L15-QFXX`.
- `nRF54L10-QDXX`: Extends `nRF54L15-QDXX`.
- `nRF54L10-QFXX`: Extends `nRF54L15-QFXX`.
- `nRF54LS05B-QFXX`: Extends `nRF54LS05A-QFXX`.

### `nordic-lib-kicad-nrf54-modules.kicad_sym`

- `BC15x`: Module. Left: `P1`/`P0` GPIO. Right: additional `P0` GPIO plus `~{RESET}`, `SWDCLK`, `SWDIO`. Top: `VDD`. Bottom: stacked `GND`.
- `BL54L15-453-000xxx`: Module. Left: nRF54L-style GPIO with `P1.02`/`P1.03` NFC alternates. Right: reset/SWD. Top: `VDD`. Bottom: stacked `VSS`.
- `BM15x`: Module. Same logical grouping as `BL54L15-453-000xxx`, with bottom `GND` and hidden ground stack, plus package-specific pins such as `K8` and `J6` in the GPIO sequence.
- `BM20x`: Module. Left: `VBUS`, USB, `P6`/`P7`/`P9` bus pins, then reset/SWD near the lower left. Right: `P0`, `P1`, and `P2` GPIO, ending with `P2.10/NFC1` and `P2.11/NFC2`. Top: `VDD`, `VDD_HV`, `VDD_P9`. Bottom: stacked `GND`.
- `BL54L10-453-000xxx`: Extends `BL54L15-453-000xxx`.

### `nordic-lib-kicad-nrf7.kicad_sym`

- `nRF7001-QFXX`: Wi-Fi companion, 2.4 GHz. Left: `XOP`, `XON`, QSPI host pins, `BUCKEN`, coexistence pins, `HOST_IRQ`, `SW_CTRL0`, `SW_CTRL1`. Right: `TXRF0`, buck output, PA/LDO pins, RF and buck supplies. Top: `VBAT`, `IOVDD`, `OTPVDD`, `PWRIOVDD`. Bottom: stacked `VSS`.
- `nRF7002-CEXX`: Same logical grouping as `nRF7001-QFXX`, but with both `TXRF0` and `TXRF1` and many hidden CSP grounds.
- `nRF7002-QFXX`: Same logical grouping as `nRF7002-CEXX`, with QFN hidden supply/ground stacks.
- `nRF7000-QFXX`: Extends `nRF7002-QFXX`.

### `nordic-lib-kicad-nrf9.kicad_sym`

- `nRF9151-LAXX`: Cellular SiP. Left: `ENABLE`, `P0.00..P0.20`, `P0.26..P0.31`, MAGPIO, SIM, and COEX pins. Right: `DEC0`, `ANT`, `AUX`, `GPS`, trace GPIO `P0.21..P0.25`, `VIO`, `SCLK`, `SDATA`, reset/SWD. Top: `VDD`, `VDD_GPIO`, `SIM_1V8`. Bottom: stacked `GND` shield/ground pins.
- `nRF9160-SIXX`: Same logical grouping as `nRF9151-LAXX`. Top supplies are `VDD1`, `VDD2`, `VDD_GPIO`, `SIM_1V8`; bottom is stacked `VSS` and shield grounds.
- `nRF9161-SIXX`: Same logical grouping as `nRF9160-SIXX`.

## Maintenance Checklist

- Keep pins on the existing grid and preserve side semantics from the raw pin angles.
- Preserve family-specific ordering before optimizing for pin-number order.
- Put new supply pins on top and new ground pins on bottom unless the existing symbol family clearly does otherwise.
- Stack hidden duplicate supply/ground pins with the visible representative pin.
- Keep `ANT`/RF pins on the right for SoCs unless the module edge convention already uses another side.
- Keep `~{RESET}`, `SWDCLK`, and `SWDIO` together; for most SoCs place them at lower right with reset above the two SWD pins.
- Add peripheral functions as KiCad `alternate` entries when the library already treats the port/package name as primary.

## KiCad Footprint Generator Workflow

This repository includes a local checkout of `kicad-footprint-generator/`. Use it for generated LGA, CSP/WLCSP, BGA-like, QFN, and DFN footprints when a suitable generator exists. Prefer parameterized generator definitions over hand-editing generated `.kicad_mod` geometry.

### Setup

From the generator checkout:

```sh
cd kicad-footprint-generator
python -m venv .venv
source .venv/bin/activate
./manage.sh update_dev_packages
```

Use `./manage.sh update_3d_packages` only when generating 3D models. `manage.sh update_dev_packages` installs the package in editable mode and pulls in the development tools needed for generator work.

Useful checks:

```sh
./manage.sh tests
./manage.sh format_check
```

If `generate.py` fails with an import such as `ModuleNotFoundError: No module named 'KicadModTree'` or `No module named 'generators'`, activate the virtual environment and rerun `./manage.sh update_dev_packages`.

### Generator Definition Locations

Current upstream-style layout:

- `data/package/grid_array/csp.yaml`: CSP, WLCSP, and other matrix/grid packages.
- `data/package/grid_array/lga.yaml`: LGA modules or packages that are better represented as a grid array.
- `data/package/no_lead/lga.yaml`: perimeter or no-lead LGA packages derived by IPC no-lead equations.
- `data/package/no_lead/qfn-*.yaml`: QFN, DFN, VQFN, UQFN, and related no-lead packages.
- `src/generators/package/grid_array`: grid-array generator implementation.
- `src/generators/package/no_lead`: no-lead generator implementation.

Use `package/grid_array` for CSP/WLCSP/LGA packages with matrix pads, skipped pads, staggered rows, off-center grids, or multiple pitches. Use `package/no_lead` for QFN/DFN and LGA footprints where body, lead, and exposed-pad dimensions should drive IPC-derived pads.

### CSP, WLCSP, BGA, and Grid LGA Definitions

Typical fields:

```yaml
Nordic_WLCSP-20_1.94x2.40mm_Layout4x5_P0.4mm:
  size_source: "https://datasheet-or-package-drawing"
  description: "Nordic WLCSP package"
  device_type: "WLCSP"
  manufacturer: "Nordic"
  body_size_x: 1.94
  body_size_y: 2.40
  pitch: 0.4
  layout_x: 4
  layout_y: 5
  ball_diameter: 0.25
  ball_type: "collapsible"
  mask_margin: 0.05
```

Use `pad_diameter` instead of `ball_diameter`/`ball_type` when the package drawing gives an explicit land pattern or the footprint is manufacturer-specific. Add `pad_skips`, `row_skips`, `area_skips`, `staggered`, `first_ball`, `offset_x`, `offset_y`, or `secondary_layouts` for non-rectangular, staggered, off-center, or multi-pitch arrays.

### QFN, DFN, and No-Lead LGA Definitions

Typical fields:

```yaml
Nordic_QFN-52-1EP_6x6mm_P0.4mm_EP4.7x4.7mm:
  size_source: "https://datasheet-or-package-drawing"
  device_type: "QFN"
  manufacturer: "Nordic"
  ipc_class: "qfn"
  body_size_x: 5.90 .. 6.00 .. 6.10
  body_size_y: 5.90 .. 6.00 .. 6.10
  overall_height: 0.80 .. 0.85 .. 0.90
  num_pins_x: 13
  num_pins_y: 13
  pitch: 0.4
  lead_width: 0.15 .. 0.20 .. 0.25
  lead_len: 0.30 .. 0.40 .. 0.50
  EP_size_x: 4.60 .. 4.70 .. 4.80
  EP_size_y: 4.60 .. 4.70 .. 4.80
  EP_num_paste_pads: [3, 3]
  thermal_vias:
    count: [4, 4]
    drill: 0.2
    paste_via_clearance: 0.1
```

For no-lead packages, `num_pins_x` is the pin count on each horizontal side and `num_pins_y` is the pin count on each vertical side. For example, a square QFN-52 uses `num_pins_x: 13` and `num_pins_y: 13`.

For pull-back LGA pads, use `ipc_class: "qfn_pull_back"` and provide `lead_to_edge`, `lead_center_pos_x`/`lead_center_pos_y`, `lead_center_to_center_x`/`lead_center_to_center_y`, or `body_to_inside_lead_edge` as appropriate for the datasheet dimensions.

### Running Generators

From `kicad-footprint-generator/src/generators` after activating the virtual environment:

```sh
./generate.py -h
./generate.py -f ../../generated -g package/grid_array -p 'Nordic_WLCSP-*'
./generate.py -f ../../generated -g package/no_lead -p 'Nordic_QFN-*'
```

Useful filters:

- `-g package/grid_array` or `-g package/no_lead` selects the generator.
- `-p 'NameGlob*'` selects specific package definitions.
- `-c '*/qfn-4x.yaml'` can limit processing to a specific YAML file; include the `*/` prefix because category filtering sees full file paths.
- `-j 1 -v` is useful while debugging one definition.

Generated footprints usually appear in:

- `generated/Package_CSP.pretty/*.kicad_mod`
- `generated/Package_LGA.pretty/*.kicad_mod`
- `generated/Package_DFN_QFN.pretty/*.kicad_mod`

Copy generated outputs into this library's package-appropriate `.pretty` directory under `footprints/`, then inspect the footprint in KiCad against the Nordic datasheet or package drawing.

### Local Commit and Push

For this Nordic library, commit only the relevant generated footprint files and any intentional supporting metadata:

```sh
git switch -c add-nordic-footprints
git status
git add footprints/<library>.pretty/<footprint>.kicad_mod
git commit -m "Add Nordic package footprints"
git push -u origin add-nordic-footprints
```

Do not include unrelated untracked files or generator checkout changes unless they are intentionally part of the work.

### Upstreaming to KiCad

KiCad upstream uses GitLab merge requests. For generator-backed footprints, prepare a merge request against `kicad/libraries/kicad-footprint-generator` with the YAML definition changes, datasheet or package-drawing links, and screenshots or visual diffs. If generated `.kicad_mod` outputs are also needed in `kicad/libraries/kicad-footprints`, create or coordinate a companion merge request and link the two.

Keep upstream contributions small and reviewable:

- Start from current upstream `master`.
- Put one logical footprint family or generator change per branch.
- Use KLC naming and existing library conventions.
- Avoid manufacturer prefixes when a footprint is generic.
- Use manufacturer or part-number names only when the land pattern is truly manufacturer-specific.
- Include clear source URLs in `size_source`.
- Run the relevant generator and `./manage.sh tests` before pushing generator changes.

Typical upstream generator branch flow:

```sh
cd kicad-footprint-generator
git remote add upstream https://gitlab.com/kicad/libraries/kicad-footprint-generator.git
git fetch upstream
git switch -c add-nordic-packages upstream/master
git add data/package/...
git commit -m "Add Nordic package definitions"
git push -u <gitlab-fork-remote> add-nordic-packages
```
