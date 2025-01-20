# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestAttributeScript:
    _test_dir = Path(__file__).resolve().parent

    def test_attribute_script(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_attribute_script.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        departments = result['departments']
        assert len(departments) == 2
        assert departments[0]['id'] == 102
        assert departments[1]['id'] == 101

    def test_attribute_script_with_condition(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_attribute_script_with_condition.xml",
                               capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert len(result) == 6

        galaxy = result["planets"][0]
        assert galaxy["id"] == 2
        assert galaxy["name"] == "Milky Way"
        assert "counter" in galaxy
        assert isinstance(galaxy["counter"], int)
        assert galaxy["counter"] == 1

        star_systems = galaxy["starSystems"]
        assert len(star_systems) == 1
        assert star_systems[0]["id"] == 201
        assert star_systems[0]["name"] == "Solar System"

        planets = star_systems[0]["planets"]
        assert len(planets) == 2

        # Validate individual planets
        earth = planets[0]
        assert earth["planetId"] == "SS-01"
        assert earth["name"] == "Earth"
        assert earth["type"] == "terrestrial"
        assert len(earth["inhabitants"]) == 1
        assert earth["inhabitants"][0]["species"] == "Humans"
        assert earth["inhabitants"][0]["population"] == 8000000000

        mars = planets[1]
        assert mars["planetId"] == "SS-02"
        assert mars["name"] == "Mars"
        assert mars["type"] == "terrestrial"
        assert len(mars["inhabitants"]) == 0

    def test_attribute_script_with_nestedkey(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_attribute_script_with_nestedkey.xml",
                               capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        assert len(result) == 3
        books = result["books"]
        assert len(books) == 2
        for i, book in enumerate(books):
            assert "year_publisher" in book
            assert "is_toronto" in book["year_publisher"]
            assert "is_after_2022" in book["year_publisher"]

            # if i == 0:
            #     assert book["year_publisher"]["is_toronto"] is True
            #     assert book["year_publisher"]["is_after_2022"] is True
            # elif i == 1:
            #     assert book["year_publisher"]["is_toronto"] is False
            #     assert book["year_publisher"]["is_after_2022"] is False

        genre_book = result["genre_book"]
        assert len(genre_book) == 2
        for genre_sci in genre_book:
            assert "genre_sci" in genre_sci
            assert len(genre_sci['genre_sci']) == 4

        library = result["library"]
        assert len(library) == 1

    def test_attribute_script_with_multiprocessing(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_with_multiprocessing.xml",
                               capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert len(result) == 2
        books = result["users"]
        assert len(books) == 2
        for i in books:
            assert 'membership_type' in i

            if i == 0:
                assert i["membership_type"]["is_premium"] is False
            elif i == 1:
                assert i["membership_type"]["is_premium"] is True
