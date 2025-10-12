from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestGlobalIncrementGenerator:
    _test_dir = Path(__file__).resolve().parent

    def test_global_increment_generator(self):
        """
        Ensure GlobalIncrementGenerator yields globally unique, contiguous IDs
        across nested generate blocks.

        Descriptor: global_increment_generator_test.xml
        - customers: count=10, numProcess=1
        - orders per customer: 3
        - line_items per order: 3
        Expectation:
        - customers.cId: 1..10
        - orders.oId: 1..30
        - line_items.lId: 1..90
        """
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="global_increment_generator_test.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        cap = engine.capture_result()

        # Outermost
        customers = cap["customers"]
        c_ids = [int(r["cId"]) for r in customers]
        assert c_ids == list(range(1, 11))

        # Nested level 1
        orders = cap["orders"]
        o_ids = [int(r["oId"]) for r in orders]
        assert o_ids == list(range(1, 31))

        # Nested level 2 (note: key becomes 'orders|line_items' after trimming the first segment)
        line_items = cap["orders|line_items"]
        l_ids = [int(r["lId"]) for r in line_items]
        assert l_ids == list(range(1, 91))

        # Additional safety: uniqueness
        assert len(set(c_ids)) == len(c_ids)
        assert len(set(o_ids)) == len(o_ids)
        assert len(set(l_ids)) == len(l_ids)

