#!/usr/bin/env python3

"""
Test script to debug import issues.
"""

print("Importing from utils.class_factory_util...")
from datamimic_ce.utils.class_factory_util import ClassFactoryUtil

print(f"ClassFactoryUtil from utils: {ClassFactoryUtil}")

# Skip the problematic import
# print("\nImporting from core.class_factory_util...")
# from datamimic_ce.utils.class_factory_util import ClassFactoryUtil
# print(f"ClassFactoryUtil from core: {ClassFactoryUtil}")

print("\nImporting from core...")
from datamimic_ce.core import ClassFactoryUtil

print(f"ClassFactoryUtil from core package: {ClassFactoryUtil}")

print("\nDone!")
