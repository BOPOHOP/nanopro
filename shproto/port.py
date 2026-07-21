import serial
import serial.tools.list_ports
import shproto
import re
import os

port_speed = 600000

def getallports():
    allports = serial.tools.list_ports.comports()
    nanoports = []
    for port in allports:
        if port.manufacturer == "FTDI" or re.search("^/dev/ttyUSB.*", port.device):
            # print("getallports: {}".format(port.device))
            nanoports.append(port)
    return nanoports


def getallportssn():
    allports = getallports()
    portssn = []
    for port in allports:
        portssn.append(port.serial_number)
    return portssn


def getallportsastext():
    allports = getallports()
    portsastext = []
    for port in allports:
        portsastext.append([port.serial_number, port.device])
        # print("getallportsastext: port: {} {} {}".format(port, port.serial_number, port.device));
    return portsastext


def getportbyserialnumber(sn):
    allports = getallports()
    for port in allports:
        if port.serial_number == sn:
            return port
    return None


def getdevicebyserialnumber(sn):
    port = getportbyserialnumber(sn)
    if port is None:
        if re.match("^/", sn) and os.path.exists(sn):
            return sn
        return None
    else:
        return getportbyserialnumber(sn).device

import socket
def connectdevice(sn=None):
    m = re.search("^tcp://(.+):(\d+)", sn, flags=re.IGNORECASE)
    if m is not None and len(m.groups()) == 2:
        TCP_HOST = m.group(1)
        TCP_PORT = int(m.group(2))
        print("connect info: tcp_host: {} tcp_port: {}".format(TCP_HOST, TCP_PORT))
        client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        print("socket", client_socket)
        try:
            client_socket.connect((TCP_HOST, TCP_PORT))
        except Exception as e:
            print(f"connect to {TCP_HOST} {TCP_PORT} error: {e}")
            exit (1)

        print("socket connected", client_socket)
        #/ with sock.makefile(mode='rw', encoding='utf-8') as sock_file:
        sock_file=client_socket.makefile(mode='rwb', buffering=0)
        print("socket -> file", sock_file)
        return sock_file


    if sn is None and len(getallports()) > 0:
        nanoport = getallports()[0].device
    else:
        nanoport = getdevicebyserialnumber(sn)
    if nanoport is None:
        print("!!! Error. Could not found nano connected.")
        exit(0)
    print("port {} speed {}".format(nanoport, shproto.port.port_speed))
    # tty = serial.Serial(nanoport, baudrate=600000, bytesize=8, parity='N', stopbits=1, timeout=1)
    # tty = serial.Serial(nanoport, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1)
    tty = serial.Serial(nanoport, baudrate=shproto.port.port_speed, bytesize=8, parity='N', stopbits=1, timeout=0.1)
    # tty = serial.Serial(nanoport, baudrate=38400, bytesize=8, parity='N', stopbits=1, timeout=0.05)
    return tty
