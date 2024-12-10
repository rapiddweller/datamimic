# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import json
import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import tests_ce.functional_tests.test_file_exporter.util_of_test_exporter as util


class TestExporter:
    _test_dir = Path(__file__).resolve().parent

    def test_csv_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_csv_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_csv_product_customer"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        inner_user_folder_name = f"exporter_result_{task_id}_exporter_csv_product_inner_user"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)

        try:
            # test customer csv
            header, data = util.read_csv_txt_folder(customer_folder_path)
            if not header or not data:
                assert False
            else:
                assert len(data) == 10
                assert data == [str(tens) for tens in range(1, 11)]

            # test inner_user csv
            header, data = util.read_csv_txt_folder(inner_user_folder_path)
            if not header or not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append(f"{tens}{units}")
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_json_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_json_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_json_product_customer"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        inner_user_folder_name = f"exporter_result_{task_id}_exporter_json_product_inner_user"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)

        try:
            # test customer csv
            data = util.read_json_folder(customer_folder_path)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len-1]["cid"] == customer_data_len

            # test inner_user csv
            data = util.read_json_folder(inner_user_folder_path)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append({"uid": tens * 10 + units})
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_txt_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_txt_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_txt_product_customer"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        inner_user_folder_name = f"exporter_result_{task_id}_exporter_txt_product_inner_user"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)

        try:
            # test customer csv
            _, data = util.read_csv_txt_folder(customer_folder_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len-1] == "customer: {'cid': " + str(customer_data_len) + "}"

            # test inner_user csv
            _, data = util.read_csv_txt_folder(inner_user_folder_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append(f"inner_user: {{'uid': {tens}{units}}}")
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_xml_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_xml_product_customer"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        inner_user_folder_name = f"exporter_result_{task_id}_exporter_xml_product_inner_user"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)

        try:
            # test customer csv
            files = util.read_xml_folder(customer_folder_path)
            if not files:
                assert False
            else:
                assert len(files) == 3
                index = 0
                for datas in files:
                    for data in datas:
                        if data == datas[0]:
                            assert data == "<list>"
                        elif data == datas[-1]:
                            assert data == "</list>"
                        else:
                            index += 1
                            assert data == f"<item><cid>{index}</cid></item>"

                assert index == 10

            # test inner_user csv
            files = util.read_xml_folder(inner_user_folder_path)
            if not files:
                assert False
            else:
                assert len(files) == 3
                index = 0
                for datas in files:
                    for data in datas:
                        if data == datas[0]:
                            assert data == "<list>"
                        elif data == datas[-1]:
                            assert data == "</list>"
                        else:
                            tens = int(index / 3) + 1
                            units = int(index % 3) + 1
                            index += 1
                            assert data == f"<item><uid>{tens}{units}</uid></item>"

                assert index == 30
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_csv_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_csv_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_csv_product_customer"
        customer_file_name = "product_customer_chunk_0.csv"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        customer_file_path = customer_folder_path.joinpath(customer_file_name)

        inner_user_folder_name = f"exporter_result_{task_id}_exporter_csv_product_inner_user"
        inner_user_file_name = "product_inner_user_chunk_0.csv"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)
        inner_user_file_path = inner_user_folder_path.joinpath(inner_user_file_name)

        try:
            # test customer csv
            header, data = util.read_csv_txt_file(customer_file_path)
            if not header or not data:
                assert False
            else:
                assert len(data) == 10
                assert data == [str(tens) for tens in range(1, 11)]

            # test inner_user csv
            header, data = util.read_csv_txt_file(inner_user_file_path)
            if not header or not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append(f"{tens}{units}")
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_json_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_json_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_json_product_customer"
        customer_file_name = "product_customer_chunk_0.json"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        customer_file_path = customer_folder_path.joinpath(customer_file_name)

        inner_user_folder_name = f"exporter_result_{task_id}_exporter_json_product_inner_user"
        inner_user_file_name = "product_inner_user_chunk_0.json"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)
        inner_user_file_path = inner_user_folder_path.joinpath(inner_user_file_name)

        try:
            # test customer csv
            data = util.read_json_file(customer_file_path)

            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len-1]["cid"] == customer_data_len

            # test inner_user csv
            data = util.read_json_file(inner_user_file_path)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append({"uid": tens * 10 + units})
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_txt_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_txt_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_txt_product_customer"
        customer_file_name = "product_customer_chunk_0.txt"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        customer_file_path = customer_folder_path.joinpath(customer_file_name)

        inner_user_folder_name = f"exporter_result_{task_id}_exporter_txt_product_inner_user"
        inner_user_file_name = "product_inner_user_chunk_0.txt"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)
        inner_user_file_path = inner_user_folder_path.joinpath(inner_user_file_name)

        try:
            # test customer csv
            _, data = util.read_csv_txt_file(customer_file_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len-1] == "customer: {'cid': " + str(customer_data_len) + "}"

            # test inner_user csv
            _, data = util.read_csv_txt_file(inner_user_file_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):  # Tens place: 1-10
                    for units in range(1, 4):  # Units place: 1-3
                        inner_user_temp_list.append(f"inner_user: {{'uid': {tens}{units}}}")
                assert data == inner_user_temp_list
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)

    def test_xml_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_name = f"exporter_result_{task_id}_exporter_xml_product_customer"
        customer_file_name = "product_customer_chunk_0.xml"
        customer_folder_path = self._test_dir.joinpath(customer_folder_name)
        customer_file_path = customer_folder_path.joinpath(customer_file_name)

        inner_user_folder_name = f"exporter_result_{task_id}_exporter_xml_product_inner_user"
        inner_user_file_name = "product_inner_user_chunk_0.xml"
        inner_user_folder_path = self._test_dir.joinpath(inner_user_folder_name)
        inner_user_file_path = inner_user_folder_path.joinpath(inner_user_file_name)

        try:
            # test customer csv
            files = util.read_xml_file(customer_file_path)
            if not files:
                assert False
            else:
                assert len(files) == 1
                index = 0
                for datas in files:
                    for data in datas:
                        if data == datas[0]:
                            assert data == "<list>"
                        elif data == datas[-1]:
                            assert data == "</list>"
                        else:
                            index += 1
                            assert data == f"<item><cid>{index}</cid></item>"

                assert index == 10

            # test inner_user csv
            files = util.read_xml_file(inner_user_file_path)
            if not files:
                assert False
            else:
                assert len(files) == 1
                index = 0
                for datas in files:
                    for data in datas:
                        if data == datas[0]:
                            assert data == "<list>"
                        elif data == datas[-1]:
                            assert data == "</list>"
                        else:
                            tens = int(index / 3) + 1
                            units = int(index % 3) + 1
                            index += 1
                            assert data == f"<item><uid>{tens}{units}</uid></item>"

                assert index == 30
        finally:
            # Ensure the file is deleted after testing
            if inner_user_folder_path.exists():
                shutil.rmtree(inner_user_folder_path)
            if customer_folder_path.exists():
                shutil.rmtree(customer_folder_path)
