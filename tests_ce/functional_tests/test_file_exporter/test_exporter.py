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

    def _get_export_paths(self, task_id: str, export_type: str, product_name: str):
        """Centralized method to generate export paths"""
        base_folder = self._test_dir / "output"
        folder_name = f"{task_id}_{export_type}_{product_name}"
        folder_path = base_folder / folder_name
        file_name = f"product_{product_name}_chunk_0.{export_type}"
        file_path = folder_path / file_name
        return folder_path, file_path

    def _cleanup_folders(self, *folders):
        """Helper method to clean up test folders"""
        for folder in folders:
            if folder.exists():
                shutil.rmtree(folder)

    def test_csv_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_csv_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, _ = self._get_export_paths(task_id, "csv", "customer")
        inner_user_folder_path, _ = self._get_export_paths(task_id, "csv", "inner_user")

        try:
            # test customer csv
            header, data = util.read_csv_txt_folder(customer_folder_path, "csv")
            if not header or not data:
                assert False
            else:
                assert len(data) == 10
                assert data == [str(tens) for tens in range(1, 11)]

            # test inner_user csv
            header, data = util.read_csv_txt_folder(inner_user_folder_path, "csv")
            if not header or not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append(f"{tens}{units}")
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_json_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_json_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, _ = self._get_export_paths(task_id, "json", "customer")
        inner_user_folder_path, _ = self._get_export_paths(task_id, "json", "inner_user")

        try:
            # test customer json
            data = util.read_json_folder(customer_folder_path)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len - 1]["cid"] == customer_data_len

            # test inner_user json
            data = util.read_json_folder(inner_user_folder_path)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append({"uid": tens * 10 + units})
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_txt_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_txt_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, _ = self._get_export_paths(task_id, "txt", "customer")
        inner_user_folder_path, _ = self._get_export_paths(task_id, "txt", "inner_user")

        try:
            # test customer txt
            _, data = util.read_csv_txt_folder(customer_folder_path, "txt", have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len - 1] == f"customer: {{'cid': {customer_data_len}}}"

            # test inner_user txt
            _, data = util.read_csv_txt_folder(inner_user_folder_path, "txt", have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append(f"inner_user: {{'uid': {tens}{units}}}")
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_xml_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, _ = self._get_export_paths(task_id, "xml", "customer")
        inner_user_folder_path, _ = self._get_export_paths(task_id, "xml", "inner_user")

        try:
            # test customer xml
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

            # test inner_user xml
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
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_csv_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_csv_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, customer_file_path = self._get_export_paths(task_id, "csv", "customer")
        inner_user_folder_path, inner_user_file_path = self._get_export_paths(task_id, "csv", "inner_user")

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
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append(f"{tens}{units}")
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_json_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_json_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, customer_file_path = self._get_export_paths(task_id, "json", "customer")
        inner_user_folder_path, inner_user_file_path = self._get_export_paths(task_id, "json", "inner_user")

        try:
            # test customer json
            data = util.read_json_file(customer_file_path)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len - 1]["cid"] == customer_data_len

            # test inner_user json
            data = util.read_json_file(inner_user_file_path)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append({"uid": tens * 10 + units})
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_txt_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_txt_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, customer_file_path = self._get_export_paths(task_id, "txt", "customer")
        inner_user_folder_path, inner_user_file_path = self._get_export_paths(task_id, "txt", "inner_user")

        try:
            # test customer txt
            _, data = util.read_csv_txt_file(customer_file_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 10
                for customer_data_len in range(1, 11):
                    assert data[customer_data_len - 1] == f"customer: {{'cid': {customer_data_len}}}"

            # test inner_user txt
            _, data = util.read_csv_txt_file(inner_user_file_path, have_header=False)
            if not data:
                assert False
            else:
                assert len(data) == 30
                inner_user_temp_list = []
                for tens in range(1, 11):
                    for units in range(1, 4):
                        inner_user_temp_list.append(f"inner_user: {{'uid': {tens}{units}}}")
                assert data == inner_user_temp_list
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_xml_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, customer_file_path = self._get_export_paths(task_id, "xml", "customer")
        inner_user_folder_path, inner_user_file_path = self._get_export_paths(task_id, "xml", "inner_user")

        try:
            # test customer xml
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

            # test inner_user xml
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
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_one_record_xml_exporter_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_one_record_xml_exporter_mp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, _ = self._get_export_paths(task_id, "xml", "customer")
        inner_user_folder_path, _ = self._get_export_paths(task_id, "xml", "inner_user")

        try:
            # test customer xml
            files = util.read_xml_folder(customer_folder_path)
            if not files:
                assert False
            else:
                assert len(files) == 1
                for datas in files:
                    assert datas[0] == "<cid>1</cid>"

            # test inner_user xml
            files = util.read_xml_folder(inner_user_folder_path)
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
                assert index == 3
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)

    def test_one_record_xml_exporter_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_one_record_xml_exporter_sp.xml")
        engine.test_with_timer()
        task_id = engine.task_id

        customer_folder_path, customer_file_path = self._get_export_paths(task_id, "xml", "customer")
        inner_user_folder_path, inner_user_file_path = self._get_export_paths(task_id, "xml", "inner_user")

        try:
            # test customer xml
            files = util.read_xml_file(customer_file_path)
            if not files:
                assert False
            else:
                assert len(files) == 1
                for datas in files:
                    assert datas[0] == "<cid>1</cid>"

            # test inner_user xml
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
                assert index == 3
        finally:
            self._cleanup_folders(customer_folder_path, inner_user_folder_path)
