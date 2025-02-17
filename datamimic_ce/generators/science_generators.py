# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from enum import Enum

from datamimic_ce.generators.generator import Generator

# Science Generators


class NucleotideType(Enum):
    """Type of nucleotide sequence."""

    DNA = "DNA"
    RNA = "RNA"


class NucleotideSequenceGenerator(Generator):
    """Generate DNA or RNA sequences."""

    def __init__(self, sequence_type: str = "DNA", length: int = 10):
        """
        Initialize NucleotideSequenceGenerator.

        Args:
            sequence_type (str): Type of sequence ('DNA' or 'RNA')
            length (int): Length of the sequence
        """
        self._type = NucleotideType(sequence_type.upper())
        self._length = max(1, length)
        self._dna_nucleotides = "TCGA"
        self._rna_nucleotides = "UCGA"

    def generate(self) -> str:
        """Generate a nucleotide sequence.

        Returns:
            str: DNA or RNA sequence
        """
        nucleotides = self._rna_nucleotides if self._type == NucleotideType.RNA else self._dna_nucleotides
        return "".join(random.choices(nucleotides, k=self._length))


class UnitType(Enum):
    """Scientific unit types."""

    LENGTH = ("meter", "m")
    MASS = ("gram", "g")
    TIME = ("second", "s")
    TEMPERATURE = ("kelvin", "K")
    AMOUNT = ("mole", "mol")
    CURRENT = ("ampere", "A")
    LUMINOSITY = ("candela", "cd")


class MetricPrefix(Enum):
    """Metric prefixes with their symbols and powers."""

    YOTTA = ("yotta", "Y", 24)
    ZETTA = ("zetta", "Z", 21)
    EXA = ("exa", "E", 18)
    PETA = ("peta", "P", 15)
    TERA = ("tera", "T", 12)
    GIGA = ("giga", "G", 9)
    MEGA = ("mega", "M", 6)
    KILO = ("kilo", "k", 3)
    HECTO = ("hecto", "h", 2)
    DECA = ("deca", "da", 1)
    DECI = ("deci", "d", -1)
    CENTI = ("centi", "c", -2)
    MILLI = ("milli", "m", -3)
    MICRO = ("micro", "μ", -6)
    NANO = ("nano", "n", -9)
    PICO = ("pico", "p", -12)
    FEMTO = ("femto", "f", -15)
    ATTO = ("atto", "a", -18)
    ZEPTO = ("zepto", "z", -21)
    YOCTO = ("yocto", "y", -24)


class ScientificUnitGenerator(Generator):
    """Generate scientific units with optional metric prefixes."""

    def __init__(
        self,
        unit_type: str | None = None,
        use_symbol: bool = False,
        include_prefix: bool = True,
        prefix_sign: str | None = None,
    ):
        """
        Initialize ScientificUnitGenerator.

        Args:
            unit_type (str): Type of unit (length, mass, time, etc.)
            use_symbol (bool): Whether to use symbols (m) instead of names (meter)
            include_prefix (bool): Whether to include metric prefixes
            prefix_sign (str): Sign of prefix ('positive', 'negative', or None for both)
        """
        self._use_symbol = use_symbol
        self._include_prefix = include_prefix

        # Set unit type
        if unit_type:
            try:
                self._unit_type = UnitType[unit_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid unit type: {unit_type}")
        else:
            self._unit_type = UnitType.LENGTH  # Set a default value instead of None

        # Set prefix constraints
        if prefix_sign:
            if prefix_sign.lower() == "positive":
                self._prefixes = [p for p in MetricPrefix if p.value[2] > 0]
            elif prefix_sign.lower() == "negative":
                self._prefixes = [p for p in MetricPrefix if p.value[2] < 0]
            else:
                raise ValueError("prefix_sign must be 'positive' or 'negative'")
        else:
            self._prefixes = list(MetricPrefix)

    def generate(self) -> str:
        """Generate a scientific unit.

        Returns:
            str: Scientific unit with optional prefix
        """
        # Select unit type if not specified
        unit = self._unit_type if self._unit_type else random.choice(list(UnitType))

        # Get base unit (name or symbol)
        base_unit = unit.value[1] if self._use_symbol else unit.value[0]

        # Add prefix if requested
        if self._include_prefix:
            prefix = random.choice(self._prefixes)
            prefix_val = prefix.value[1] if self._use_symbol else prefix.value[0]
            return f"{prefix_val}{base_unit}"

        return base_unit


class ChemicalFormulaGenerator(Generator):
    """Generate chemical formulas."""

    def __init__(self, complexity: int = 2):
        """
        Initialize ChemicalFormulaGenerator.

        Args:
            complexity (int): Complexity of the formula (1-3)
        """
        self._complexity = max(1, min(complexity, 3))
        self._elements = [
            ("H", 1),
            ("He", 2),
            ("Li", 3),
            ("Be", 4),
            ("B", 5),
            ("C", 6),
            ("N", 7),
            ("O", 8),
            ("F", 9),
            ("Ne", 10),
            ("Na", 11),
            ("Mg", 12),
            ("Al", 13),
            ("Si", 14),
            ("P", 15),
            ("S", 16),
            ("Cl", 17),
            ("K", 19),
            ("Ca", 20),
            ("Fe", 26),
            ("Cu", 29),
            ("Zn", 30),
            ("Ag", 47),
        ]
        self._common_compounds = {
            1: ["H2O", "CO2", "NH3", "CH4", "NaCl", "HCl", "H2", "O2", "N2", "NO2", "SO2", "CaO", "ZnO", "FeO"],
            2: ["H2SO4", "HNO3", "H3PO4", "Na2CO3", "CaCO3", "Fe2O3", "Cu2O", "Al2O3", "K2SO4", "MgCl2", "NaHCO3"],
            3: ["Ca(OH)2", "NH4NO3", "KAl(SO4)2", "NaHCO3", "Fe(NO3)3", "Cu(OH)2", "Mg(OH)2", "Al2(SO4)3"],
        }

    def generate(self) -> str:
        """Generate a chemical formula.

        Returns:
            str: Chemical formula
        """
        return random.choice(self._common_compounds[self._complexity])


class PhysicalConstantGenerator(Generator):
    """Generate physical constants with their values."""

    def __init__(self, include_value: bool = True, include_unit: bool = True):
        """
        Initialize PhysicalConstantGenerator.

        Args:
            include_value (bool): Whether to include the constant's value
            include_unit (bool): Whether to include the unit
        """
        self._include_value = include_value
        self._include_unit = include_unit
        self._constants = [
            ("c", "speed of light", "2.99792458e8", "m/s"),
            ("h", "Planck constant", "6.62607015e-34", "J⋅s"),
            ("G", "gravitational constant", "6.67430e-11", "m³/(kg⋅s²)"),
            ("e", "elementary charge", "1.602176634e-19", "C"),
            ("k", "Boltzmann constant", "1.380649e-23", "J/K"),
            ("NA", "Avogadro constant", "6.02214076e23", "mol⁻¹"),
            ("R", "gas constant", "8.31446261815324", "J/(mol⋅K)"),
            ("σ", "Stefan-Boltzmann constant", "5.670374419e-8", "W/(m²⋅K⁴)"),
            ("ε₀", "vacuum permittivity", "8.8541878128e-12", "F/m"),
            ("μ₀", "vacuum permeability", "1.25663706212e-6", "N/A²"),
        ]

    def generate(self) -> str:
        """Generate a physical constant.

        Returns:
            str: Physical constant with optional value and unit
        """
        constant = random.choice(self._constants)
        symbol, name = constant[0], constant[1]

        parts = [f"{symbol} ({name})"]

        if self._include_value:
            parts.append(constant[2])

        if self._include_unit:
            parts.append(constant[3])

        return " ".join(parts)
