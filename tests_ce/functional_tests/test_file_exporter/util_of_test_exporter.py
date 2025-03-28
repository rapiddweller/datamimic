import json
import os
from pathlib import Path
from typing import Literal


def read_csv_txt_folder(folder_path: Path, file_extension: Literal["csv", "txt"], have_header: bool = True):
    if not folder_path.exists():
        return None, None

    file_names = sorted(os.listdir(folder_path))

    header = None
    data = []
    for name in file_names:
        if name.endswith(f".{file_extension}"):
            with open(folder_path.joinpath(name)) as file:
                is_header = True if have_header is True else False
                for line in file:
                    if is_header:
                        header = line.strip()
                        is_header = False
                    else:
                        data.append(line.strip())
    return header, data


def read_csv_txt_file(file_path: Path, have_header: bool = True):
    if not file_path.exists():
        return None, None

    header = None
    data = []
    with open(file_path) as file:
        is_header = True if have_header is True else False
        for line in file:
            if is_header:
                header = line.strip()
                is_header = False
            else:
                data.append(line.strip())

    return header, data


def read_json_folder(folder_path: Path):
    if not folder_path.exists():
        return None

    file_names = sorted(os.listdir(folder_path))

    data = []
    for name in file_names:
        if name.endswith(".json"):
            with open(folder_path.joinpath(name)) as file:
                data.extend(json.load(file))
    return data


def read_xml_folder(folder_path: Path):
    if not folder_path.exists():
        return None

    file_names = sorted(os.listdir(folder_path))

    files = []
    for name in file_names:
        if name.endswith(".xml"):
            with open(folder_path.joinpath(name)) as file:
                datas = []
                for line in file:
                    datas.append(line.strip())
                if datas:
                    files.append(datas)
    return files


def read_json_file(file_path: Path):
    if not file_path.exists():
        return None

    with open(file_path) as file:
        return json.load(file)


def read_xml_file(file_path: Path):
    if not file_path.exists():
        return None

    files = []
    with open(file_path) as file:
        datas = []
        for line in file:
            datas.append(line.strip())
        if datas:
            files.append(datas)
    return files
