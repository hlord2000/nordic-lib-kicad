# Nordic Symbol Utilities

Utilities for parsing and generating KiCad symbols using the kiutils library.

## Setup

```bash
# From the repository root
uv venv
source .venv/bin/activate
uv pip install -e ./kiutils
```

## Usage

### List symbols in a library

```bash
python scripts/symbol_utils.py parse symbols/nordic-lib-kicad-nrf52.kicad_sym --list
```

### Parse a specific symbol

```bash
python scripts/symbol_utils.py parse symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX --verbose
```

### Extract pin table

```bash
# Table format (default)
python scripts/symbol_utils.py pins symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX

# CSV format
python scripts/symbol_utils.py pins symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX --format csv

# JSON format
python scripts/symbol_utils.py pins symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX --format json
```

### Extract complete symbol definition to JSON

```bash
python scripts/symbol_utils.py extract symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX --output my_symbol.json
```

### Generate a symbol from JSON definition

```bash
python scripts/symbol_utils.py generate my_symbol.json --output my_symbol.kicad_sym
```

### Validate a symbol against KLC rules

```bash
python scripts/symbol_utils.py validate symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX
```

## JSON Definition Format

The symbol definition JSON format for generation:

```json
{
  "name": "MyChip",
  "reference": "U",
  "footprint": "Package_QFP:LQFP-48_7x7mm_P0.5mm",
  "datasheet": "https://example.com/datasheet.pdf",
  "description": "My example chip",
  "keywords": "example chip mcu",
  "fp_filters": "LQFP?48*",
  "left_pins": [
    {
      "number": "1",
      "name": "PA0",
      "electrical_type": "bidirectional",
      "graphical_style": "line",
      "hidden": false,
      "alternates": [
        {"name": "ADC0", "electrical_type": "input", "graphical_style": "line"}
      ]
    }
  ],
  "right_pins": [],
  "top_pins": [
    {"number": "10", "name": "VDD", "electrical_type": "power_in", "graphical_style": "line", "hidden": false, "alternates": []}
  ],
  "bottom_pins": [
    {"number": "11", "name": "VSS", "electrical_type": "power_in", "graphical_style": "line", "hidden": false, "alternates": []}
  ]
}
```

### Pin Electrical Types

- `input` - Input pin
- `output` - Output pin
- `bidirectional` - Bidirectional I/O pin
- `power_in` - Power input (VDD, VCC)
- `power_out` - Power output (voltage regulator output)
- `passive` - Passive pin (resistors, capacitors, ground pads)
- `open_collector` - Open collector output
- `open_emitter` - Open emitter output
- `tri_state` - Tri-state output
- `unspecified` - Unspecified type
- `no_connect` - Not connected

### Pin Graphical Styles

- `line` - Standard line
- `inverted` - Inverted (bubble)
- `clock` - Clock input
- `inverted_clock` - Inverted clock
- `input_low` - Active low input
- `clock_low` - Active low clock
- `output_low` - Active low output
- `edge_clock_high` - Edge-triggered clock
- `non_logic` - Non-logic pin

## KLC Compliance

Generated symbols are designed to be KLC (KiCad Library Convention) compliant:

- S3.3: 10mil (0.254mm) stroke width on outlines
- S4.1: All pins on 100mil (2.54mm) grid
- Proper pin grouping by function (left/right/top/bottom)
- Standard property fields (Reference, Value, Footprint, Datasheet, Description)

Note: The KLC checker in kicad-library-utils may report some format warnings due to differences in KiCad version output formats. The generated symbols are functionally correct and compatible with KiCad.
