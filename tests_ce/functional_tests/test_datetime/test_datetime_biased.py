# DATAMIMIC

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDateTimeBiased:
    _test_dir = Path(__file__).resolve().parent

    def test_biased_datetime_example(self) -> None:
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="functional_test_datetime_biased.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()
        rows = result["biased_datetime_test"]
        assert len(rows) == 400

        # Extract values
        values = [r["biased_datetime"] for r in rows]

        # Minute/second constraints from weights
        for dt in values:
            assert dt.second == 0
            assert dt.minute in (0, 15, 30, 45)

        # Hour bias checks (deterministic with seed): more samples in hour 0 than hour 23 and hour 12
        from collections import Counter

        hour_counts = Counter(dt.hour for dt in values)
        assert hour_counts[0] > hour_counts[23]
        assert hour_counts[0] > hour_counts[12]

