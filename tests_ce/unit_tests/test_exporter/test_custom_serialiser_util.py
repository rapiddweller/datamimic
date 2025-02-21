import base64
import unittest
import uuid
from datetime import date, datetime
from decimal import Decimal

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

# Import the custom_serializer function from the module
from datamimic_ce.exporters.exporter_util import custom_serializer


class DummyAsPy:
    """
    Dummy class that simulates a pyarrow-like object by providing an as_py method.
    """
    def as_py(self):
        return {"key": "value"}


class BrokenStr:
    """
    Dummy class that simulates a broken __str__ method.
    """
    def __str__(self):
        raise Exception("Cannot convert object to string")


class TestCustomSerializer(unittest.TestCase):
    def test_datetime_and_date(self):
        """Test serialization for datetime and date objects."""
        dt = datetime(2023, 10, 5, 12, 34, 56)
        d = date(2023, 10, 5)
        self.assertEqual(custom_serializer(dt), dt.isoformat())
        self.assertEqual(custom_serializer(d), d.isoformat())

    def test_pyarrow_like_object(self):
        """Test object with as_py method is correctly serialized using its as_py output."""
        dummy = DummyAsPy()
        self.assertEqual(custom_serializer(dummy), {"key": "value"})

    def test_uuid_object(self):
        """Test serialization for UUID objects."""
        uid = uuid.uuid4()
        self.assertEqual(custom_serializer(uid), str(uid))

    @unittest.skipUnless(ObjectId is not None, "bson module is not available")
    def test_mongodb_objectid(self):
        """Test that a MongoDB ObjectId is serialized to its string representation."""
        oid = ObjectId("507f191e810c19729de860ea")
        self.assertEqual(custom_serializer(oid), str(oid))

    @unittest.skipUnless(pd is not None, "pandas is not available")
    def test_pandas_timestamp(self):
        """Test serialization for pandas Timestamp objects."""
        ts = pd.Timestamp("2023-10-05T12:34:56")
        self.assertEqual(custom_serializer(ts), ts.isoformat())

    def test_decimal_object(self):
        """Test serialization for Decimal objects."""
        dec = Decimal("123.456")
        self.assertEqual(custom_serializer(dec), str(dec))

    @unittest.skipUnless(np is not None, "numpy is not available")
    def test_numpy_scalar(self):
        """Test serialization for NumPy scalar types."""
        np_int = np.int64(42)
        np_float = np.float64(3.14)
        self.assertEqual(custom_serializer(np_int), np_int.item())
        self.assertEqual(custom_serializer(np_float), np_float.item())

    def test_sets_and_frozensets(self):
        """Test that sets and frozensets are converted to lists."""
        s = {1, 2, 3}
        fs = frozenset({4, 5, 6})
        # Compare as sets because the order of list conversion is not guaranteed.
        self.assertEqual(set(custom_serializer(s)), s)
        self.assertEqual(set(custom_serializer(fs)), set(fs))

    def test_bytes_utf8(self):
        """Test that bytes decodable as UTF-8 are properly converted to strings."""
        b_string = b"hello world"
        self.assertEqual(custom_serializer(b_string), "hello world")

    def test_bytes_non_utf8(self):
        """Test that bytes not decodable as UTF-8 are encoded in base64."""
        # b'\xff' is typically invalid in UTF-8.
        non_utf8 = b'\xff'
        expected = base64.b64encode(non_utf8).decode("ascii")
        self.assertEqual(custom_serializer(non_utf8), expected)

    def test_fallback_to_str(self):
        """Test that simple types fallback to str conversion."""
        num = 123
        self.assertEqual(custom_serializer(num), str(num))

    def test_broken_str(self):
        """
        Test that an object which fails __str__ conversion raises a TypeError with the proper message.
        """
        broken = BrokenStr()
        with self.assertRaises(TypeError) as ctx:
            custom_serializer(broken)
        self.assertIn("Failed when serializing exporting data", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()