#!/usr/bin/python3
from serial import Serial
from binascii import b2a_hex
from time import time, sleep
from crccheck.crc import Crc8
from struct import unpack
import struct
import crcmod.predefined
from zlib import crc32
import sys

if len(sys.argv) < 2:
    print("not input app firmware")
    exit(0)

ser = Serial('COM4', 115200, timeout=30) # 串口 接收app 之后，得重启 bootloader 

# 发生进入boot的序列
print("try to entry boot mode")
ser.timeout = 0.1


while True:
    boot = (0xFD, 0x08, 0x00, 0x00, 0xE5, 0x01, 0x01, 0x76, 0x03, 0x00, 0x62, 0x6F, 0x6F, 0x74, 0x9D, 0x90, 0x90, 0x8B, 0xC0, 0xDA)
    if(ser.isOpen() == False):
        ser.open()
    ser.write(boot)
    data = ser.read(2)
    print(data)
    ser.close()
    sleep(1)
    if data == b'\x12\x10':
        print("entry boot mode")
        break
    else:
        pass
        # if(ser.isOpen() == False):
        #     ser.open()
        # ser.write(b'\x21\x20')
        # data = ser.read(2)
        # if data == b'\x12\x10':
        #     break
if(ser.isOpen() == False):
    ser.open()
print("try sync")
ack = b'\x00\x00'
while ack != b'\x12\x10':
    get_sync = b'\x21\x20'
    ser.write(get_sync)
    ser.timeout = 0.5
    ack = ser.read(2)

max_len = 0
ser.timeout = 30
# 获取fw允许大小
get_fw_size = b'\x22\x04\x20'
ser.write(get_fw_size)
ack = ser.read(6)
if len(ack) != 6:
    print("get allow max firmware size fail")
    exit(-1)
elif ack[4:6] == b'\x12\x10':
    max_len = unpack("<I", ack[0:4])[0]
    print("max firmware size is {}".format(max_len))
else:
    exit(-1)

get_vec_reserve = b'\x22\x05\x20'
ser.write(get_vec_reserve)
ack = ser.read(18)

ser.timeout = 30
chip_erase = b'\x23\x20'
ser.write(chip_erase)
print("erase chip start\nit may take 17 seconds\n.......")
start = time()
ack = ser.read(2)
end = time()
if ack == b'\x12\x10':
    print("erase finished!\n used {} second".format(end-start))
else:
    print("erase failed")
    exit(-1)

f = open(sys.argv[1], "rb")
fw = f.read()
f.close()
if len(fw) % 4 != 0:
    pad = 4-(len(fw) % 4)
    pad_data = b'\xff'*pad
    fw = fw+pad_data
loop = len(fw)//0xfc
print("len:{} loop:{}".format(len(fw),loop))
last_write = len(fw) % 0xfc
print("last_write:{}".format(last_write))

start = 0
end = 0
start = time()
print("programing:")
for i in range(loop):
    crc8_func = crcmod.predefined.mkCrcFun('crc-8-maxim')

    crc = crc8_func(fw[i*0xfc:0xfc*(i+1)])
    # a = Crc8()
    # crc = a.calc(list(fw[i*0xfc:0xfc*(i+1)])) 
    # print(crc)
    # print(type(crc))

    pack = b'\x27'+b'\xfc'+fw[i*0xfc:0xfc*(i+1)] + struct.pack("<B", crc) + b'\x20'

    ser.write(pack)
    ack = ser.read(2)
    if ack == b'\x12\x10':
        print("\r{}/{}".format(i*0xfc, len(fw)), end="")
    else:
        print("program failed", len(pack) - 4)
        # exit(-1)
if last_write != 0:
    crc8_func = crcmod.predefined.mkCrcFun('crc-8-maxim')

    crc = crc8_func(fw[loop*0xfc:])
    data_len = len(fw[loop*0xfc:])
    pack = b'\x27'+bytes([data_len])+fw[loop*0xfc:] + struct.pack("<B", crc) + b'\x20'
    ser.write(pack)
    ack = ser.read(2)
    if ack == b'\x12\x10':
        print("\r{}/{}".format(loop*0xfc, len(fw)), end="")
        print("\n boodloder load okokok!")
    else:
        print("program failed", len(pack) - 4)
        exit(-1)
end = time()
print("\ndownload time", end-start)

get_fw_size = b'\x22\x04\x20'
ser.write(get_fw_size)
ack = ser.read(6)
print("fw size is {:08x}".format(unpack("<I", ack[0:4])[0]))

get_crc = b'\x29\x20'
ser.write(get_crc)
ack = ser.read(6)

if len(ack) != 6:
    print("crc get failed")
    exit(-1)
if ack[-2:] != b'\x12\x10':
    print("crc get failed")
    exit(-1)
crc_from_mcu = unpack("<I", ack[0:4])[0]
crc_calc = crc32(fw)
if crc_from_mcu != 0:
    print("crc check failed")
    print(" crc upload from mcu:", hex(crc_from_mcu))
    print("      crc calc by pc:", hex(crc_calc))
    exit(-1)

    
print("crc check success !")
print(" crc upload from mcu:", hex(crc_from_mcu))
print("      crc calc by pc:", hex(crc_calc))


print("run application")
boot = b'\x30\x20'
ser.write(boot)
ack = ser.read(2)
if ack != b'\x12\x10':
    print("unknown error")
