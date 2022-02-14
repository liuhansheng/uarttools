#!/usr/bin/python3

from os import popen, system

status = system("cmake --version")
if 0 != status:
    popen("sudo snap install cmake")

status = system("ninja --version")
if 0 != status:
    popen("sudo apt install ninja-build")

status = system("arm-none-eabi-gcc --version")
if 0!= status:
    popen("wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/10-2020q4/gcc-arm-none-eabi-10-2020-q4-major-x86_64-linux.tar.bz2 && sudo tar -jxf gcc-arm-none-eabi-10-2020-q4-major-x86_64-linux.tar.bz2 -C /opt")
    popen("echo 'export PATH=/opt/gcc-arm-none-eabi-10-2020-q4-major/bin:$PATH' >> ~/.bashrc")
    popen("source ~/.bashrc")