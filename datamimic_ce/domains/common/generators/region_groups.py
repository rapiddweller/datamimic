# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Dataset region-group aliases: a single ``dataset=`` value that expands to a pool of concrete
ISO country codes, each of which already has its own city/country/street data file in this repo.
No new locale data - purely a grouping over what already exists."""

# European countries with an existing city_{CC}.csv (and matching country/street files) in this
# repo - geographic Europe, EU/EFTA/UK plus the Balkans and microstates. Deliberately excludes
# transcontinental/ambiguous cases (e.g. Turkey) to keep the grouping unsurprising.
REGION_GROUPS: dict[str, tuple[str, ...]] = {
    "EUROPE": (
        "AD",
        "AL",
        "AT",
        "BA",
        "BE",
        "BG",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LI",
        "LT",
        "LU",
        "LV",
        "MC",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "RU",
        "SE",
        "SI",
        "SK",
        "SM",
        "UA",
        "VA",
    ),
    # Sub-regions and other groupings, each code having an existing city_{CC}.csv in this repo.
    "WESTERN_EUROPE": ("FR", "DE", "NL", "BE", "LU", "AT", "CH", "LI", "MC", "IE", "GB"),
    "CENTRAL_EUROPE": ("DE", "PL", "CZ", "SK", "HU", "AT", "CH", "SI"),
    "SOUTHERN_EUROPE": ("IT", "ES", "PT", "GR", "SM", "VA", "AD", "CY"),
    "EASTERN_EUROPE": ("PL", "CZ", "SK", "HU", "RO", "BG", "UA", "RU", "HR", "SI", "BA", "AL", "EE", "LT", "LV"),
    "NORTH_AMERICA": ("US", "CA"),
    "OCEANIA": ("AU", "NZ"),
    "FRENCH": ("FR", "BE", "CH", "LU", "MC", "CA"),
    "IBERIA": ("ES", "PT", "AD"),
}

