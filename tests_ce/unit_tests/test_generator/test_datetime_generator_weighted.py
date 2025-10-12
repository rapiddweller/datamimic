# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# Test für die neuen Gewichtungsfunktionen im DateTimeGenerator

import pytest
from datetime import datetime
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

class TestDateTimeGeneratorWeighted:
    def test_hour_weights_night_bias(self):
        # 00-05 Uhr: hohe Wahrscheinlichkeit, Rest gering
        hour_weights = [0.2]*6 + [0.02]*18
        gen = DateTimeGenerator(
            min="2024-01-01 00:00:00",
            max="2024-01-31 23:59:59",
            random=True,
            hour_weights=hour_weights
        )
        hours = [gen.generate().hour for _ in range(1000)]
        # Erwartung: Deutlich mehr Werte zwischen 0 und 5 Uhr
        night_count = sum(0 <= h <= 5 for h in hours)
        day_count = sum(6 <= h <= 23 for h in hours)
        assert night_count > day_count  # Nacht dominiert
        assert night_count > 500  # Mindestens die Hälfte

    def test_minute_weights(self):
        # Nur volle Viertelstunden zulassen
        minute_weights = [1 if m in (0, 15, 30, 45) else 0 for m in range(60)]
        gen = DateTimeGenerator(
            min="2024-01-01 00:00:00",
            max="2024-01-02 00:00:00",
            random=True,
            minute_weights=minute_weights
        )
        minutes = [gen.generate().minute for _ in range(200)]
        assert all(m in (0, 15, 30, 45) for m in minutes)

    def test_second_weights(self):
        # Nur Sekunde 0 (volle Minute)
        second_weights = [1] + [0]*59
        gen = DateTimeGenerator(
            min="2024-01-01 00:00:00",
            max="2024-01-01 01:00:00",
            random=True,
            second_weights=second_weights
        )
        seconds = [gen.generate().second for _ in range(100)]
        assert all(s == 0 for s in seconds)

    def test_no_weights_equals_default(self):
        # Ohne Gewichtung: Verhalten wie Standard
        gen = DateTimeGenerator(
            min="2024-01-01 00:00:00",
            max="2024-01-01 01:00:00",
            random=True
        )
        datetimes = [gen.generate() for _ in range(10)]
        assert all(isinstance(dt, datetime) for dt in datetimes)
