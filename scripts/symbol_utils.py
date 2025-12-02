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

    def _create_unit(self, definition: SymbolDefinition) -> Symbol:
        """Create a symbol unit with pins and graphics (KLC compliant)."""
        unit = Symbol()
        unit.entryName = definition.name
        unit.unitId = 1
        unit.styleId = 0

        # Calculate dimensions based on pin counts
        left_count = len(definition.left_pins)
        right_count = len(definition.right_pins)
        top_count = len(definition.top_pins)
        bottom_count = len(definition.bottom_pins)

        # Calculate rectangle dimensions - ensure grid alignment
        vertical_pins = max(left_count, right_count)
        horizontal_pins = max(top_count, bottom_count)

        # Calculate minimum dimensions and snap to grid
        # Add padding: 1 grid unit above/below pins, plus space for text
        min_height = snap_to_grid(max(vertical_pins * PIN_SPACING + 2 * PIN_SPACING, 10.16))
        min_width = snap_to_grid(max(horizontal_pins * PIN_SPACING + 2 * PIN_SPACING, 15.24))

        rect_half_height = snap_to_grid(min_height / 2)
        rect_half_width = snap_to_grid(min_width / 2)

        # Create rectangle with KLC-compliant stroke width
        rect = SyRect()
        rect.start = Position(X=-rect_half_width, Y=rect_half_height)
        rect.end = Position(X=rect_half_width, Y=-rect_half_height)
        rect.stroke = Stroke(width=RECT_STROKE_WIDTH, type=RECT_STROKE_TYPE)
        rect.fill = Fill(type="background")
        unit.graphicItems.append(rect)

        # Calculate pin starting positions - ensure grid alignment
        # KLC S4.1: All pins must be on 100mil (2.54mm) grid

        # Left pins (pointing right, angle=0)
        # Pin end position is at rectangle edge, so start_x = -(rect_half_width + PIN_LENGTH)
        left_start_x = snap_to_grid(-rect_half_width - PIN_LENGTH)
        left_start_y = snap_to_grid(rect_half_height - PIN_SPACING)
        self._add_pins_to_unit(unit, definition.left_pins,
                              start_x=left_start_x,
                              start_y=left_start_y,
                              angle=0, direction='vertical')

        # Right pins (pointing left, angle=180)
        right_start_x = snap_to_grid(rect_half_width + PIN_LENGTH)
        right_start_y = snap_to_grid(rect_half_height - PIN_SPACING)
        self._add_pins_to_unit(unit, definition.right_pins,
                              start_x=right_start_x,
                              start_y=right_start_y,
                              angle=180, direction='vertical')

        # Top pins (pointing down, angle=270)
        top_start_x = snap_to_grid(-rect_half_width + PIN_SPACING)
        top_start_y = snap_to_grid(rect_half_height + PIN_LENGTH)
        self._add_pins_to_unit(unit, definition.top_pins,
                              start_x=top_start_x,
                              start_y=top_start_y,
                              angle=270, direction='horizontal')

        # Bottom pins (pointing up, angle=90)
        bottom_start_x = snap_to_grid(-rect_half_width + PIN_SPACING)
        bottom_start_y = snap_to_grid(-rect_half_height - PIN_LENGTH)
        self._add_pins_to_unit(unit, definition.bottom_pins,
                              start_x=bottom_start_x,
                              start_y=bottom_start_y,
                              angle=90, direction='horizontal')

        return unit

    def _add_pins_to_unit(self, unit: Symbol, pins: List[PinDefinition],
                         start_x: float, start_y: float, angle: float,
                         direction: str) -> None:
        """Add a list of pins to a unit (KLC S4.1: grid-aligned)."""
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

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
