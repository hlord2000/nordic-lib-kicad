#!/usr/bin/env python3
"""
Symbol Utilities for Nordic KiCad Library

This module provides utilities for parsing and generating KiCad symbols
using the kiutils library. It enables:
- Parsing existing symbols to extract pin tables
- Generating new symbols from pin table definitions
- Analyzing symbol structure for KLC compliance

Usage:
    # Parse a symbol and show its structure
    python symbol_utils.py parse symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX

    # Extract pin table as CSV
    python symbol_utils.py pins symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX --format csv

    # Generate a symbol from a pin table JSON
    python symbol_utils.py generate pin_table.json --output output.kicad_sym

    # Validate a symbol against KLC rules
    python symbol_utils.py validate symbols/nordic-lib-kicad-nrf52.kicad_sym --symbol nRF52805-CAXX
"""

import argparse
import json
import sys
import csv
import io
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from kiutils.symbol import SymbolLib, Symbol, SymbolPin, SymbolAlternativePin
from kiutils.items.common import Position, Effects, Font, Property, Fill, Stroke, Justify
from kiutils.items.syitems import SyRect


# Constants for symbol layout (KLC compliant)
# KLC S4.1: Pins must be on 100mil (2.54mm) grid
PIN_LENGTH = 2.54
PIN_SPACING = 2.54  # 100mil grid spacing
FONT_SIZE = 1.27
# KLC S3.3: Symbol outline should be 10mil (0.254mm)
RECT_STROKE_WIDTH = 0.254  # 10mil stroke width for KLC compliance
RECT_STROKE_TYPE = "default"
GRID_SIZE = 2.54  # 100mil grid


def snap_to_grid(value: float, grid: float = GRID_SIZE) -> float:
    """Snap a value to the nearest grid point (100mil by default)."""
    return round(value / grid) * grid


def parse_pin_name(name: str) -> Tuple[str, int, int]:
    """
    Parse a pin name into sortable components.

    Returns tuple of (category, port, pin_num) for sorting.
    Categories (lower number = higher priority/position):
    - 0: Crystal (XC1, XC2, XL1, XL2)
    - 1: GPIO Port 1 (P1.xx)
    - 2: GPIO Port 0 (P0.xx)
    - 3: GPIO Port 2+ (P2.xx, etc.)
    - 4: Antenna (ANT)
    - 5: Debug (RESET, SWDIO, SWDCLK)
    - 6: Power (VDD, VDDL, VSS, DCC)
    - 7: Decoupling (DEC*, CFLY*)
    - 9: Other
    """
    import re

    name_upper = name.upper().replace('~{', '').replace('}', '')

    # Crystal pins
    if name_upper.startswith('XC') or name_upper.startswith('XL'):
        match = re.search(r'(\d+)', name)
        num = int(match.group(1)) if match else 0
        return (0, 0, num)

    # GPIO pins - P<port>.<pin>
    gpio_match = re.match(r'P(\d+)\.(\d+)', name)
    if gpio_match:
        port = int(gpio_match.group(1))
        pin = int(gpio_match.group(2))
        # P1 first (category 1), then P0 (category 2), then P2+ (category 3)
        if port == 1:
            return (1, port, pin)
        elif port == 0:
            return (2, port, pin)
        else:
            return (3, port, pin)

    # Antenna
    if name_upper == 'ANT':
        return (4, 0, 0)

    # Debug pins
    if name_upper in ('RESET', 'SWDIO', 'SWDCLK', 'SWO'):
        order = {'RESET': 0, 'SWDIO': 1, 'SWDCLK': 2, 'SWO': 3}
        return (5, 0, order.get(name_upper, 99))

    # Power pins
    if name_upper.startswith('VDD') or name_upper == 'DCC':
        return (6, 0, 0 if name_upper.startswith('VDD') else 1)
    if name_upper.startswith('VSS'):
        return (6, 1, 0)

    # Decoupling caps
    if name_upper.startswith('DEC') or name_upper.startswith('CFLY'):
        order = {'DECRF': 0, 'DECA': 1, 'DECB': 2, 'DECD': 3, 'CFLYL': 4, 'CFLYH': 5}
        return (7, 0, order.get(name_upper, 99))

    # Everything else
    return (9, 0, 0)


def sort_pins_by_name(pins: List['PinDefinition']) -> List['PinDefinition']:
    """Sort pins by their name according to Nordic convention."""
    return sorted(pins, key=lambda p: parse_pin_name(p.name))


def parse_pin_number(number: str) -> Tuple[bool, int, str]:
    """
    Parse a pin number for sorting.

    Returns tuple of (is_numeric, numeric_value, alpha_part) for sorting.
    Handles both numeric (1, 2, 48) and BGA-style (A1, B2, F5) pin numbers.
    """
    import re

    # Try pure numeric first
    if number.isdigit():
        return (True, int(number), '')

    # Try BGA style (letter + number)
    match = re.match(r'([A-Z]+)(\d+)', number.upper())
    if match:
        letter_part = match.group(1)
        num_part = int(match.group(2))
        # Convert letter to number (A=0, B=1, etc.) for sorting
        letter_val = sum((ord(c) - ord('A')) * (26 ** i)
                        for i, c in enumerate(reversed(letter_part)))
        return (False, letter_val * 100 + num_part, letter_part)

    # Fallback
    return (False, 0, number)


def sort_pins_by_number(pins: List['PinDefinition']) -> List['PinDefinition']:
    """Sort pins by their pin number (numeric or BGA-style)."""
    return sorted(pins, key=lambda p: parse_pin_number(p.number))


@dataclass
class PinDefinition:
    """Represents a single pin definition for symbol generation."""
    number: str
    name: str
    electrical_type: str = "bidirectional"  # input, output, bidirectional, power_in, power_out, passive, etc.
    graphical_style: str = "line"  # line, inverted, clock, etc.
    hidden: bool = False
    alternates: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_symbol_pin(cls, pin: SymbolPin) -> 'PinDefinition':
        """Create a PinDefinition from a kiutils SymbolPin."""
        alternates = []
        for alt in pin.alternatePins:
            alternates.append({
                'name': alt.pinName,
                'electrical_type': alt.electricalType,
                'graphical_style': alt.graphicalStyle
            })
        return cls(
            number=pin.number,
            name=pin.name,
            electrical_type=pin.electricalType,
            graphical_style=pin.graphicalStyle,
            hidden=pin.hide,
            alternates=alternates
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SymbolDefinition:
    """Represents a complete symbol definition for generation."""
    name: str
    reference: str = "U"
    footprint: str = ""
    datasheet: str = ""
    description: str = ""
    keywords: str = ""
    fp_filters: str = ""

    # Pin groups by side
    left_pins: List[PinDefinition] = field(default_factory=list)
    right_pins: List[PinDefinition] = field(default_factory=list)
    top_pins: List[PinDefinition] = field(default_factory=list)
    bottom_pins: List[PinDefinition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'reference': self.reference,
            'footprint': self.footprint,
            'datasheet': self.datasheet,
            'description': self.description,
            'keywords': self.keywords,
            'fp_filters': self.fp_filters,
            'left_pins': [p.to_dict() for p in self.left_pins],
            'right_pins': [p.to_dict() for p in self.right_pins],
            'top_pins': [p.to_dict() for p in self.top_pins],
            'bottom_pins': [p.to_dict() for p in self.bottom_pins],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolDefinition':
        """Create from dictionary (JSON deserialization)."""
        def parse_pins(pin_list: List[Dict]) -> List[PinDefinition]:
            return [PinDefinition(**p) for p in pin_list]

        return cls(
            name=data['name'],
            reference=data.get('reference', 'U'),
            footprint=data.get('footprint', ''),
            datasheet=data.get('datasheet', ''),
            description=data.get('description', ''),
            keywords=data.get('keywords', ''),
            fp_filters=data.get('fp_filters', ''),
            left_pins=parse_pins(data.get('left_pins', [])),
            right_pins=parse_pins(data.get('right_pins', [])),
            top_pins=parse_pins(data.get('top_pins', [])),
            bottom_pins=parse_pins(data.get('bottom_pins', [])),
        )


class SymbolParser:
    """Parses existing KiCad symbols and extracts information."""

    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self.library: Optional[SymbolLib] = None

    def load(self) -> SymbolLib:
        """Load the symbol library."""
        if self.library is None:
            self.library = SymbolLib.from_file(str(self.library_path))
        return self.library

    def list_symbols(self) -> List[str]:
        """List all symbol names in the library."""
        lib = self.load()
        return [s.entryName for s in lib.symbols]

    def get_symbol(self, symbol_name: str) -> Optional[Symbol]:
        """Get a specific symbol by name."""
        lib = self.load()
        for symbol in lib.symbols:
            if symbol.entryName == symbol_name:
                return symbol
        return None

    def get_symbol_info(self, symbol_name: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        symbol = self.get_symbol(symbol_name)
        if symbol is None:
            return {}

        info = {
            'name': symbol.entryName,
            'in_bom': symbol.inBom,
            'on_board': symbol.onBoard,
            'properties': {},
            'units': [],
            'total_pins': 0,
        }

        # Extract properties
        for prop in symbol.properties:
            info['properties'][prop.key] = prop.value

        # Extract unit information
        for unit in symbol.units:
            unit_info = {
                'id': unit.libId,
                'pin_count': len(unit.pins),
                'graphic_items': len(unit.graphicItems),
            }
            info['units'].append(unit_info)
            info['total_pins'] += len(unit.pins)

        return info

    def extract_pins(self, symbol_name: str) -> List[PinDefinition]:
        """Extract all pins from a symbol."""
        symbol = self.get_symbol(symbol_name)
        if symbol is None:
            return []

        pins = []
        for unit in symbol.units:
            for pin in unit.pins:
                pins.append(PinDefinition.from_symbol_pin(pin))

        return pins

    def extract_pin_table(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Extract pins as a flat table (for CSV export)."""
        pins = self.extract_pins(symbol_name)
        table = []
        for pin in pins:
            row = {
                'number': pin.number,
                'name': pin.name,
                'electrical_type': pin.electrical_type,
                'graphical_style': pin.graphical_style,
                'hidden': pin.hidden,
                'alternates': '; '.join([f"{a['name']}:{a['electrical_type']}" for a in pin.alternates])
            }
            table.append(row)
        return table

    def infer_pin_sides(self, symbol_name: str) -> Dict[str, List[PinDefinition]]:
        """Infer which side each pin belongs to based on position and angle."""
        symbol = self.get_symbol(symbol_name)
        if symbol is None:
            return {'left': [], 'right': [], 'top': [], 'bottom': []}

        sides = {'left': [], 'right': [], 'top': [], 'bottom': []}

        for unit in symbol.units:
            for pin in unit.pins:
                pin_def = PinDefinition.from_symbol_pin(pin)
                angle = pin.position.angle if pin.position.angle is not None else 0

                # Angle 0 = pointing right (pin on left side)
                # Angle 180 = pointing left (pin on right side)
                # Angle 90 = pointing up (pin on bottom)
                # Angle 270 = pointing down (pin on top)
                if angle == 0:
                    sides['left'].append(pin_def)
                elif angle == 180:
                    sides['right'].append(pin_def)
                elif angle == 90:
                    sides['bottom'].append(pin_def)
                elif angle == 270:
                    sides['top'].append(pin_def)
                else:
                    # Default to left for unusual angles
                    sides['left'].append(pin_def)

        return sides


class SymbolGenerator:
    """Generates KiCad symbols from definitions."""

    def __init__(self):
        self.generator_name = "nordic_symbol_utils"

    def create_symbol(self, definition: SymbolDefinition) -> Symbol:
        """Create a Symbol from a SymbolDefinition."""
        symbol = Symbol()
        symbol.entryName = definition.name
        symbol.inBom = True
        symbol.onBoard = True

        # Create standard properties
        symbol.properties = [
            self._create_property("Reference", definition.reference, 0, 0, 0),
            self._create_property("Value", definition.name, 0, -2.54, 1),
            self._create_property("Footprint", definition.footprint, 0, -5.08, 2, hide=True),
            self._create_property("Datasheet", definition.datasheet, 0, -7.62, 3, hide=True),
            self._create_property("Description", definition.description, 0, -10.16, 4, hide=True),
        ]

        if definition.keywords:
            symbol.properties.append(
                self._create_property("ki_keywords", definition.keywords, 0, 0, None, hide=True)
            )
        if definition.fp_filters:
            symbol.properties.append(
                self._create_property("ki_fp_filters", definition.fp_filters, 0, 0, None, hide=True)
            )

        # Create the unit with pins and rectangle
        unit = self._create_unit(definition)
        symbol.units.append(unit)

        return symbol

    def _create_property(self, key: str, value: str, x: float, y: float,
                        prop_id: Optional[int] = None, hide: bool = False) -> Property:
        """Create a property with standard formatting."""
        prop = Property()
        prop.key = key
        prop.value = value
        prop.id = prop_id
        prop.position = Position(X=x, Y=y, angle=0)
        prop.effects = Effects(
            font=Font(width=FONT_SIZE, height=FONT_SIZE),
            hide=hide
        )
        return prop

    def _create_unit(self, definition: SymbolDefinition, sort_pins: bool = True) -> Symbol:
        """Create a symbol unit with pins and graphics (KLC compliant).

        Args:
            definition: The symbol definition with pins organized by side
            sort_pins: If True, sort pins by name within each side
        """
        unit = Symbol()
        unit.entryName = definition.name
        unit.unitId = 1
        unit.styleId = 0

        # Sort pins by name if requested
        left_pins = sort_pins_by_name(definition.left_pins) if sort_pins else definition.left_pins
        right_pins = sort_pins_by_name(definition.right_pins) if sort_pins else definition.right_pins
        top_pins = sort_pins_by_name(definition.top_pins) if sort_pins else definition.top_pins
        bottom_pins = sort_pins_by_name(definition.bottom_pins) if sort_pins else definition.bottom_pins

        # Calculate dimensions based on pin counts
        # Count only visible pins for spacing calculation
        left_count = len([p for p in left_pins if not p.hidden])
        right_count = len([p for p in right_pins if not p.hidden])
        top_count = len([p for p in top_pins if not p.hidden])
        bottom_count = len([p for p in bottom_pins if not p.hidden])

        # Calculate rectangle dimensions - ensure grid alignment
        vertical_pins = max(left_count, right_count)
        horizontal_pins = max(top_count, bottom_count)

        # Calculate minimum dimensions and snap to grid
        # Height: need space for all vertical pins plus padding
        min_height = snap_to_grid(max(vertical_pins * PIN_SPACING + 2 * PIN_SPACING, 10.16))
        # Width: need space for all horizontal pins plus padding
        min_width = snap_to_grid(max(horizontal_pins * PIN_SPACING + 4 * PIN_SPACING, 15.24))

        rect_half_height = snap_to_grid(min_height / 2)
        rect_half_width = snap_to_grid(min_width / 2)

        # Create rectangle with KLC-compliant stroke width
        rect = SyRect()
        rect.start = Position(X=-rect_half_width, Y=rect_half_height)
        rect.end = Position(X=rect_half_width, Y=-rect_half_height)
        rect.stroke = Stroke(width=RECT_STROKE_WIDTH, type=RECT_STROKE_TYPE)
        rect.fill = Fill(type="background")
        unit.graphicItems.append(rect)

        # Calculate pin positions - ensure grid alignment
        # KLC S4.1: All pins must be on 100mil (2.54mm) grid

        # Left pins (pointing right, angle=0)
        # Start from top, working down
        left_x = snap_to_grid(-rect_half_width - PIN_LENGTH)
        left_y_start = snap_to_grid(rect_half_height - PIN_SPACING)
        self._add_pins_to_unit_positioned(unit, left_pins,
                                          base_x=left_x,
                                          start_y=left_y_start,
                                          angle=0,
                                          direction='vertical')

        # Right pins (pointing left, angle=180)
        right_x = snap_to_grid(rect_half_width + PIN_LENGTH)
        right_y_start = snap_to_grid(rect_half_height - PIN_SPACING)
        self._add_pins_to_unit_positioned(unit, right_pins,
                                          base_x=right_x,
                                          start_y=right_y_start,
                                          angle=180,
                                          direction='vertical')

        # Top pins (pointing down, angle=270)
        # Center horizontally
        top_width_needed = len([p for p in top_pins if not p.hidden]) * PIN_SPACING
        top_x_start = snap_to_grid(-top_width_needed / 2 + PIN_SPACING / 2)
        top_y = snap_to_grid(rect_half_height + PIN_LENGTH)
        self._add_pins_to_unit_positioned(unit, top_pins,
                                          base_x=top_x_start,
                                          start_y=top_y,
                                          angle=270,
                                          direction='horizontal')

        # Bottom pins (pointing up, angle=90)
        # Center horizontally
        bottom_width_needed = len([p for p in bottom_pins if not p.hidden]) * PIN_SPACING
        bottom_x_start = snap_to_grid(-bottom_width_needed / 2 + PIN_SPACING / 2)
        bottom_y = snap_to_grid(-rect_half_height - PIN_LENGTH)
        self._add_pins_to_unit_positioned(unit, bottom_pins,
                                          base_x=bottom_x_start,
                                          start_y=bottom_y,
                                          angle=90,
                                          direction='horizontal')

        return unit

    def _add_pins_to_unit_positioned(self, unit: Symbol, pins: List[PinDefinition],
                                      base_x: float, start_y: float, angle: float,
                                      direction: str) -> None:
        """Add pins to unit with proper positioning for hidden pins.

        Hidden pins are placed at the same position as the previous visible pin.
        This ensures stacked pins (like multiple VSS) share the same location.
        """
        x = snap_to_grid(base_x)
        y = snap_to_grid(start_y)
        last_visible_x = x
        last_visible_y = y

        for pin_def in pins:
            if pin_def.hidden:
                # Hidden pins go at the same position as the last visible pin
                pin = self._create_pin(pin_def, last_visible_x, last_visible_y, angle)
            else:
                pin = self._create_pin(pin_def, x, y, angle)
                last_visible_x = x
                last_visible_y = y
                # Only advance position for visible pins
                if direction == 'vertical':
                    y = snap_to_grid(y - PIN_SPACING)
                else:
                    x = snap_to_grid(x + PIN_SPACING)

            unit.pins.append(pin)

    def _add_pins_to_unit(self, unit: Symbol, pins: List[PinDefinition],
                         start_x: float, start_y: float, angle: float,
                         direction: str) -> None:
        """Add a list of pins to a unit (KLC S4.1: grid-aligned). DEPRECATED."""
        x, y = snap_to_grid(start_x), snap_to_grid(start_y)

        for pin_def in pins:
            pin = self._create_pin(pin_def, x, y, angle)
            unit.pins.append(pin)

            if direction == 'vertical':
                y = snap_to_grid(y - PIN_SPACING)
            else:
                x = snap_to_grid(x + PIN_SPACING)

    def _create_pin(self, pin_def: PinDefinition, x: float, y: float, angle: float) -> SymbolPin:
        """Create a SymbolPin from a PinDefinition (KLC compliant)."""
        pin = SymbolPin()
        pin.electricalType = pin_def.electrical_type
        pin.graphicalStyle = pin_def.graphical_style
        # Ensure positions are grid-aligned (KLC S4.1)
        pin.position = Position(X=snap_to_grid(x), Y=snap_to_grid(y), angle=angle)
        pin.length = PIN_LENGTH
        pin.name = pin_def.name
        pin.number = pin_def.number
        pin.hide = pin_def.hidden

        # Set effects for name and number
        pin.nameEffects = Effects(font=Font(width=FONT_SIZE, height=FONT_SIZE))
        pin.numberEffects = Effects(font=Font(width=FONT_SIZE, height=FONT_SIZE))

        # Add alternate pin functions
        for alt in pin_def.alternates:
            alt_pin = SymbolAlternativePin()
            alt_pin.pinName = alt['name']
            alt_pin.electricalType = alt.get('electrical_type', 'bidirectional')
            alt_pin.graphicalStyle = alt.get('graphical_style', 'line')
            pin.alternatePins.append(alt_pin)

        return pin

    def create_library(self, symbols: List[Symbol], version: str = "20241209") -> SymbolLib:
        """Create a symbol library containing the given symbols."""
        lib = SymbolLib()
        lib.version = version
        lib.generator = self.generator_name
        lib.symbols = symbols
        return lib

    def save_library(self, library: SymbolLib, output_path: str) -> None:
        """Save a symbol library to file."""
        library.to_file(output_path)


class KLCValidator:
    """Validates symbols against KiCad Library Convention rules."""

    def __init__(self, klc_check_path: Optional[str] = None):
        if klc_check_path:
            self.klc_check_path = Path(klc_check_path)
        else:
            # Try to find it relative to this script
            script_dir = Path(__file__).parent.parent
            self.klc_check_path = script_dir / "kicad-library-utils" / "klc-check" / "check_symbol.py"

    def validate(self, library_path: str, symbol_name: Optional[str] = None) -> Tuple[int, str]:
        """
        Validate a symbol library or specific symbol against KLC rules.

        Returns:
            Tuple of (error_count, output_text)
        """
        if not self.klc_check_path.exists():
            return (-1, f"KLC checker not found at {self.klc_check_path}")

        cmd = [sys.executable, str(self.klc_check_path), library_path]
        if symbol_name:
            cmd.extend(["-c", symbol_name])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout + result.stderr
            return (result.returncode, output)
        except Exception as e:
            return (-1, f"Failed to run KLC checker: {e}")


def cmd_parse(args):
    """Handle the 'parse' command."""
    parser = SymbolParser(args.library)

    if args.list:
        symbols = parser.list_symbols()
        print(f"Symbols in {args.library}:")
        for sym in symbols:
            print(f"  - {sym}")
        return

    if args.symbol:
        info = parser.get_symbol_info(args.symbol)
        if not info:
            print(f"Symbol '{args.symbol}' not found")
            sys.exit(1)

        print(f"Symbol: {info['name']}")
        print(f"  In BOM: {info['in_bom']}")
        print(f"  On Board: {info['on_board']}")
        print(f"  Total Pins: {info['total_pins']}")
        print(f"  Units: {len(info['units'])}")
        print("\nProperties:")
        for key, value in info['properties'].items():
            print(f"  {key}: {value}")

        if args.verbose:
            print("\nUnits:")
            for unit in info['units']:
                print(f"  {unit['id']}: {unit['pin_count']} pins, {unit['graphic_items']} graphics")


def cmd_pins(args):
    """Handle the 'pins' command."""
    parser = SymbolParser(args.library)

    if not args.symbol:
        print("Error: --symbol is required for pins command")
        sys.exit(1)

    table = parser.extract_pin_table(args.symbol)
    if not table:
        print(f"No pins found for symbol '{args.symbol}'")
        sys.exit(1)

    if args.format == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['number', 'name', 'electrical_type',
                                                     'graphical_style', 'hidden', 'alternates'])
        writer.writeheader()
        writer.writerows(table)
        print(output.getvalue())
    elif args.format == 'json':
        print(json.dumps(table, indent=2))
    else:
        # Default table format
        print(f"{'Number':<10} {'Name':<20} {'Type':<15} {'Style':<10} {'Hidden':<8} Alternates")
        print("-" * 80)
        for row in table:
            hidden = 'Yes' if row['hidden'] else ''
            print(f"{row['number']:<10} {row['name']:<20} {row['electrical_type']:<15} "
                  f"{row['graphical_style']:<10} {hidden:<8} {row['alternates']}")


def cmd_extract(args):
    """Handle the 'extract' command - extract a symbol definition."""
    parser = SymbolParser(args.library)

    if not args.symbol:
        print("Error: --symbol is required for extract command")
        sys.exit(1)

    # Get basic symbol info
    symbol = parser.get_symbol(args.symbol)
    if not symbol:
        print(f"Symbol '{args.symbol}' not found")
        sys.exit(1)

    # Infer pin sides
    sides = parser.infer_pin_sides(args.symbol)

    # Build definition
    properties = {p.key: p.value for p in symbol.properties}

    definition = SymbolDefinition(
        name=symbol.entryName,
        reference=properties.get('Reference', 'U'),
        footprint=properties.get('Footprint', ''),
        datasheet=properties.get('Datasheet', ''),
        description=properties.get('Description', ''),
        keywords=properties.get('ki_keywords', ''),
        fp_filters=properties.get('ki_fp_filters', ''),
        left_pins=sides['left'],
        right_pins=sides['right'],
        top_pins=sides['top'],
        bottom_pins=sides['bottom'],
    )

    output = json.dumps(definition.to_dict(), indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Extracted to {args.output}")
    else:
        print(output)


def cmd_generate(args):
    """Handle the 'generate' command."""
    # Load definition from JSON
    with open(args.definition, 'r') as f:
        data = json.load(f)

    definition = SymbolDefinition.from_dict(data)

    generator = SymbolGenerator()
    symbol = generator.create_symbol(definition)
    library = generator.create_library([symbol])

    output_path = args.output or f"{definition.name}.kicad_sym"
    generator.save_library(library, output_path)
    print(f"Generated symbol library: {output_path}")


def cmd_validate(args):
    """Handle the 'validate' command."""
    validator = KLCValidator(args.klc_path)
    error_count, output = validator.validate(args.library, args.symbol)

    print(output)
    sys.exit(0 if error_count == 0 else 1)


def cmd_analyze(args):
    """Handle the 'analyze' command - show pin positions from existing symbols."""
    parser = SymbolParser(args.library)
    symbol = parser.get_symbol(args.symbol)

    if not symbol:
        print(f"Symbol '{args.symbol}' not found")
        sys.exit(1)

    # Group pins by side based on position and rotation
    sides = {'left': [], 'right': [], 'top': [], 'bottom': []}

    for unit in symbol.units:
        for pin in unit.pins:
            x, y = pin.position.X, pin.position.Y
            rot = pin.position.angle if pin.position.angle is not None else 0

            pin_info = {
                'number': pin.number,
                'name': pin.name,
                'x': x,
                'y': y,
                'type': pin.electricalType,
                'hidden': pin.hide,
            }

            if rot == 0:
                sides['left'].append(pin_info)
            elif rot == 180:
                sides['right'].append(pin_info)
            elif rot == 270:
                sides['top'].append(pin_info)
            elif rot == 90:
                sides['bottom'].append(pin_info)

    # Sort by position
    sides['left'].sort(key=lambda p: -p['y'])  # top to bottom
    sides['right'].sort(key=lambda p: -p['y'])
    sides['top'].sort(key=lambda p: p['x'])  # left to right
    sides['bottom'].sort(key=lambda p: p['x'])

    # Calculate rectangle bounds
    all_x = [p['x'] for side in sides.values() for p in side]
    all_y = [p['y'] for side in sides.values() for p in side]
    if all_x and all_y:
        print(f"Pin position bounds: X=[{min(all_x):.2f}, {max(all_x):.2f}], Y=[{min(all_y):.2f}, {max(all_y):.2f}]")

    for side_name in ['left', 'right', 'top', 'bottom']:
        pins = sides[side_name]
        if not pins:
            continue

        print(f"\n{side_name.upper()} PINS ({len(pins)} pins):")
        print(f"  {'Num':<6} {'Name':<20} {'X':>8} {'Y':>8} {'Type':<12} {'Hidden'}")
        print("  " + "-" * 70)
        for p in pins:
            hidden = 'HIDDEN' if p['hidden'] else ''
            print(f"  {p['number']:<6} {p['name']:<20} {p['x']:>8.2f} {p['y']:>8.2f} {p['type']:<12} {hidden}")


def main():
    parser = argparse.ArgumentParser(
        description="Symbol utilities for Nordic KiCad Library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse and display symbol information')
    parse_parser.add_argument('library', help='Path to .kicad_sym library file')
    parse_parser.add_argument('--symbol', '-s', help='Specific symbol to parse')
    parse_parser.add_argument('--list', '-l', action='store_true', help='List all symbols')
    parse_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parse_parser.set_defaults(func=cmd_parse)

    # Pins command
    pins_parser = subparsers.add_parser('pins', help='Extract pin information')
    pins_parser.add_argument('library', help='Path to .kicad_sym library file')
    pins_parser.add_argument('--symbol', '-s', required=True, help='Symbol name')
    pins_parser.add_argument('--format', '-f', choices=['table', 'csv', 'json'],
                            default='table', help='Output format')
    pins_parser.set_defaults(func=cmd_pins)

    # Extract command
    extract_parser = subparsers.add_parser('extract',
                                           help='Extract complete symbol definition as JSON')
    extract_parser.add_argument('library', help='Path to .kicad_sym library file')
    extract_parser.add_argument('--symbol', '-s', required=True, help='Symbol name')
    extract_parser.add_argument('--output', '-o', help='Output JSON file')
    extract_parser.set_defaults(func=cmd_extract)

    # Generate command
    generate_parser = subparsers.add_parser('generate',
                                            help='Generate a symbol from JSON definition')
    generate_parser.add_argument('definition', help='Path to JSON definition file')
    generate_parser.add_argument('--output', '-o', help='Output .kicad_sym file')
    generate_parser.set_defaults(func=cmd_generate)

    # Validate command
    validate_parser = subparsers.add_parser('validate',
                                            help='Validate symbol against KLC rules')
    validate_parser.add_argument('library', help='Path to .kicad_sym library file')
    validate_parser.add_argument('--symbol', '-s', help='Specific symbol to validate')
    validate_parser.add_argument('--klc-path', help='Path to check_symbol.py')
    validate_parser.set_defaults(func=cmd_validate)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze',
                                           help='Analyze pin positions in existing symbol')
    analyze_parser.add_argument('library', help='Path to .kicad_sym library file')
    analyze_parser.add_argument('--symbol', '-s', required=True, help='Symbol name')
    analyze_parser.set_defaults(func=cmd_analyze)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
