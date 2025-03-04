# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from abc import ABC, abstractmethod
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.common.utils.class_util import (
    create_dynamic_class,
    create_instance,
    create_instance_by_name,
    create_registered_instance,
    get_class,
    get_class_by_attribute,
    get_registered_classes,
    get_subclasses,
    register_class_factory,
)


# Test classes for our tests
class TestBaseClass(ABC):
    """Base class for testing."""

    @abstractmethod
    def abstract_method(self) -> str:
        """Abstract method that must be implemented by subclasses."""
        pass


class TestConcreteClass1(TestBaseClass):
    """First concrete implementation of TestBaseClass."""

    type_name = "type1"

    def __init__(self, value: str = "default"):
        self.value = value

    def abstract_method(self) -> str:
        return f"Concrete1: {self.value}"


class TestConcreteClass2(TestBaseClass):
    """Second concrete implementation of TestBaseClass."""

    type_name = "type2"

    def __init__(self, value: str = "default", extra: int = 0):
        self.value = value
        self.extra = extra

    def abstract_method(self) -> str:
        return f"Concrete2: {self.value} ({self.extra})"


class TestAbstractSubclass(TestBaseClass):
    """Abstract subclass of TestBaseClass."""

    @abstractmethod
    def another_abstract_method(self) -> str:
        """Another abstract method."""
        pass

    def abstract_method(self) -> str:
        return "Abstract implementation"


class TestClassFactoryUtil(unittest.TestCase):
    """Test cases for the class_factory_util module."""

    def test_create_instance(self):
        """Test create_instance function."""
        # Mock the importlib.import_module and getattr
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_instance = MagicMock()

        mock_module.__name__ = "mock_module"
        mock_class.__name__ = "MockClass"
        mock_class.return_value = mock_instance

        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            # Set up the mock to return our mock_class
            mock_module.MockClass = mock_class

            # Call the function
            result = create_instance("mock_module.MockClass", arg1="value1", arg2=42)

            # Verify the results
            mock_import.assert_called_once_with("mock_module")
            mock_class.assert_called_once_with(arg1="value1", arg2=42)
            self.assertEqual(result, mock_instance)

    def test_get_class(self):
        """Test get_class function."""
        # Mock the importlib.import_module
        mock_module = MagicMock()
        mock_class = MagicMock()

        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            # Set up the mock to return our mock_class
            mock_module.MockClass = mock_class

            # Call the function
            result = get_class("mock_module.MockClass")

            # Verify the results
            mock_import.assert_called_once_with("mock_module")
            self.assertEqual(result, mock_class)

    def test_get_subclasses(self):
        """Test get_subclasses function."""
        # Get subclasses of TestBaseClass
        subclasses = get_subclasses(TestBaseClass)

        # Should include concrete classes but not abstract classes
        self.assertIn(TestConcreteClass1, subclasses)
        self.assertIn(TestConcreteClass2, subclasses)
        self.assertNotIn(TestAbstractSubclass, subclasses)

        # Test with include_abstract=True
        all_subclasses = get_subclasses(TestBaseClass, include_abstract=True)
        self.assertIn(TestConcreteClass1, all_subclasses)
        self.assertIn(TestConcreteClass2, all_subclasses)
        self.assertIn(TestAbstractSubclass, all_subclasses)

    def test_create_instance_by_name(self):
        """Test create_instance_by_name function."""
        # Create a class dictionary
        class_dict = {"class1": TestConcreteClass1, "class2": TestConcreteClass2}

        # Create instances
        instance1 = create_instance_by_name(class_dict, "class1", value="test1")
        instance2 = create_instance_by_name(class_dict, "class2", value="test2", extra=10)

        # Verify the instances
        self.assertIsInstance(instance1, TestConcreteClass1)
        self.assertEqual(instance1.value, "test1")

        self.assertIsInstance(instance2, TestConcreteClass2)
        self.assertEqual(instance2.value, "test2")
        self.assertEqual(instance2.extra, 10)

        # Test with non-existent class name
        with self.assertRaises(KeyError):
            create_instance_by_name(class_dict, "non_existent")

    def test_register_class_factory(self):
        """Test register_class_factory function."""

        # Create a new base class for testing
        class TestFactoryBase:
            pass

        # Create a decorator
        decorator = register_class_factory(TestFactoryBase)

        # Create and register a class
        @decorator
        class TestFactoryClass1:
            pass

        @decorator
        class TestFactoryClass2:
            pass

        # Check if the classes are registered
        self.assertTrue(hasattr(TestFactoryBase, "_registered_classes"))
        self.assertIn("TestFactoryClass1", TestFactoryBase._registered_classes)
        self.assertIn("TestFactoryClass2", TestFactoryBase._registered_classes)
        self.assertEqual(TestFactoryBase._registered_classes["TestFactoryClass1"], TestFactoryClass1)
        self.assertEqual(TestFactoryBase._registered_classes["TestFactoryClass2"], TestFactoryClass2)

    def test_get_registered_classes(self):
        """Test get_registered_classes function."""

        # Create a new base class for testing
        class TestFactoryBase:
            pass

        # Initially, there should be no registered classes
        registered_classes = get_registered_classes(TestFactoryBase)
        self.assertEqual(registered_classes, {})

        # Register some classes
        decorator = register_class_factory(TestFactoryBase)

        @decorator
        class TestFactoryClass1:
            pass

        @decorator
        class TestFactoryClass2:
            pass

        # Get registered classes again
        registered_classes = get_registered_classes(TestFactoryBase)
        self.assertEqual(len(registered_classes), 2)
        self.assertIn("TestFactoryClass1", registered_classes)
        self.assertIn("TestFactoryClass2", registered_classes)

    def test_create_registered_instance(self):
        """Test create_registered_instance function."""

        # Create a new base class for testing
        class TestFactoryBase:
            pass

        # Register some classes
        decorator = register_class_factory(TestFactoryBase)

        @decorator
        class TestFactoryClass1:
            def __init__(self, value=None):
                self.value = value

        # Create an instance
        instance = create_registered_instance(TestFactoryBase, "TestFactoryClass1", value="test")

        # Verify the instance
        self.assertIsInstance(instance, TestFactoryClass1)
        self.assertEqual(instance.value, "test")

        # Test with non-existent class name
        with self.assertRaises(KeyError):
            create_registered_instance(TestFactoryBase, "NonExistentClass")

    def test_get_class_by_attribute(self):
        """Test get_class_by_attribute function."""
        # Create a list of classes
        classes = [TestConcreteClass1, TestConcreteClass2]

        # Find a class by attribute
        result = get_class_by_attribute(classes, "type_name", "type1")
        self.assertEqual(result, TestConcreteClass1)

        result = get_class_by_attribute(classes, "type_name", "type2")
        self.assertEqual(result, TestConcreteClass2)

        # Test with non-existent attribute value
        result = get_class_by_attribute(classes, "type_name", "non_existent")
        self.assertIsNone(result)

        # Test with non-existent attribute
        result = get_class_by_attribute(classes, "non_existent_attr", "value")
        self.assertIsNone(result)

    def test_create_dynamic_class(self):
        """Test create_dynamic_class function."""
        # Create a dynamic class
        DynamicClass = create_dynamic_class(
            "DynamicClass",
            bases=(object,),
            attributes={"attr1": "value1", "attr2": 42, "method": lambda self: "method_result"},
        )

        # Verify the class
        self.assertEqual(DynamicClass.__name__, "DynamicClass")
        self.assertEqual(DynamicClass.attr1, "value1")
        self.assertEqual(DynamicClass.attr2, 42)

        # Create an instance
        instance = DynamicClass()

        # Verify the instance
        self.assertEqual(instance.attr1, "value1")
        self.assertEqual(instance.attr2, 42)
        self.assertEqual(instance.method(), "method_result")

        # Create a class with a base class
        class BaseForDynamic:
            base_attr = "base_value"

            def base_method(self):
                return "base_method_result"

        DynamicWithBase = create_dynamic_class(
            "DynamicWithBase", bases=(BaseForDynamic,), attributes={"dynamic_attr": "dynamic_value"}
        )

        # Create an instance
        instance = DynamicWithBase()

        # Verify inheritance
        self.assertEqual(instance.base_attr, "base_value")
        self.assertEqual(instance.base_method(), "base_method_result")
        self.assertEqual(instance.dynamic_attr, "dynamic_value")


if __name__ == "__main__":
    unittest.main()
