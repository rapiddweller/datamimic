# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import json
import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPageProcess:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_page_process_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_simple_page_process_sp.xml")
        engine.test_with_timer()

    def test_simple_page_process_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_simple_page_process_mp.xml")
        engine.test_with_timer()

    def test_consumer_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_csv.xml")
        engine.test_with_timer()

    def test_consumer_json(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_json.xml")
        engine.test_with_timer()

    def test_consumer_xml(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_xml.xml")
        engine.test_with_timer()

    def test_consumer_txt(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_txt.xml")
        engine.test_with_timer()

    def test_consumer_sqlite(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_sqlite.xml")
        engine.test_with_timer()

    def test_multipage_distribution(self):
        """random/unique select disjoint windows of ONE global order across pages:
        together a permutation of the source - no duplicates, no gaps."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_page_process_distribution.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        src_ids = sorted(r["id"] for r in result["src"])
        assert src_ids == list(range(1, 13))
        assert sorted(r["id"] for r in result["rand_pages"]) == src_ids
        assert sorted(r["id"] for r in result["uniq_pages"]) == src_ids
        # cumulated samples WITH replacement: full count, every pick from the source
        cum_ids = [r["id"] for r in result["cum_pages"]]
        assert len(cum_ids) == 12
        assert set(cum_ids) <= set(src_ids)

    def test_memstore_survives_pagination_without_test_mode(self):
        """Production mode (no test capture) prunes per-page accumulation to
        memstore-needed products only - the memstore must still see ALL pages."""
        out_dir = self._test_dir / "output" / "memstore_prod_out"
        shutil.rmtree(out_dir, ignore_errors=True)
        try:
            engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_memstore_prod.xml")
            engine.test_with_timer()

            files = list(out_dir.rglob("*.json"))
            assert files, f"no JSON exported to {out_dir}"
            rows = [row for f in files for row in json.loads(f.read_text())]
            assert sorted(r["id"] for r in rows) == list(range(1, 26))
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)
