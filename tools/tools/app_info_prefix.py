#!/usr/bin/python3
import os
from zlib import crc32
from struct import pack, unpack  
from os import popen, path, chdir
from datetime import datetime
from time import time
from sys import argv 
from intelhex import IntelHex

BOARD_ID = 0x10
HW_MAJOR = 1
HW_MINOR = 0
HW_PATCH = 0

FW_MAJOR = 1 
FW_MINOR = 0
FW_PATCH = 0

MAGIC_NUM = 0xA0A0A0A0
START_ADDRESS = 0x08010200

def create_app(path):
    app_info = {"name": None,
                "size": None,
                "crc": None,
                "start_address": None,
                "fw_version": None,
                "hw_version": None}

    file_name, file_ext = os.path.splitext(path)
    fin = open(path, "rb")
    img = fin.read()

    magic_num = MAGIC_NUM
    start_address = START_ADDRESS
    app_info["start_address"] = start_address

    app_len = len(img)
    if app_len % 4 != 0:
        pad_size = 4 - (app_len % 4)
        img = img + (b'\xff' * pad_size)
        app_len += pad_size
    app_info["size"] = app_len

    crc = crc32(img)
    app_info["crc"] = "{:08x}".format(crc)

    build_timestamp = int(time())

    hardware = {"major": HW_MAJOR, "minor": HW_MINOR, "patch": HW_PATCH}
    hw_version = (hardware["major"] << (8 * 3)) | (hardware["minor"] << 8 * 2) | (hardware["patch"] << 8) | (0)

    firmware = {"major": FW_MAJOR, "minor": FW_MINOR, "patch": FW_PATCH}
    fw_version = (firmware["major"] << (8 * 3)) | (firmware["minor"] << 8 * 2) | (firmware["patch"] << 8) | (0)

    build_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode("ASCII")

    result = popen("git rev-parse HEAD")
    git_commit_hash = result.read()[0:40].encode("ASCII")

    app_path = file_name + "-" + git_commit_hash[0:7].decode('ASCII') + ".hx"
    fout = open(app_path, "wb")

    app_name = os.path.split(app_path)[-1]
    app_info["name"] = app_name
    app_name = bytearray(app_name.encode("utf-8"))
    if len(app_name) < 50:
        app_name = app_name + bytearray([0] * (50 - len(app_name)))

    app_info["fw_version"] = "{}.{}.{}".format((fw_version >> (8 * 3)) & 0xff, (fw_version >> (8 * 2)) & 0xff,
                                               (fw_version >> (8)) & 0xff)
    app_info["hw_version"] = "{}.{}.{}".format((hw_version >> (8 * 3)) & 0xff, (hw_version >> (8 * 2)) & 0xff,
                                               (hw_version >> (8)) & 0xff)
    n = fout.write(pack("<IIIIIIII19s40s50s",
                               magic_num,
                               BOARD_ID,
                               start_address,
                               app_len,
                               crc,
                               build_timestamp,
                               hw_version,
                               fw_version,
                               build_datetime,
                               git_commit_hash,
                               app_name[0:50]))
    fout.write(bytes([0x0] * (512 - n)))
    fout.write(img)
    fout.write(pack("<I", crc))
    return app_info

if __name__ == "__main__":
    create_app(argv[1])