import threading
import time

import shproto
import shproto.port

NANO_WAIT_TIMEOUT = 0.001  # Timeout for waiting new data from device

stopflag = 0
stopflag_lock = threading.Lock()
spec_stopflag = 0
spec_stopflag_lock = threading.Lock()

histogram = [0] * 8192
histogram_lock = threading.Lock()

command = ""
command_lock = threading.Lock()

pkts01 = 0
pkts03 = 0
pkts04 = 0
total_pkts = 0
dropped = 0

total_time = 0
cpu_load = 0
cps = 0
cps_lock = threading.Lock()
lost_impulses = 0


def start(sn=None):
    shproto.dispatcher.clear()
    with shproto.dispatcher.stopflag_lock:
        shproto.dispatcher.stopflag = 0
    nano = shproto.port.connectdevice(sn)
    response = shproto.packet()
    while not shproto.dispatcher.stopflag:
        if len(shproto.dispatcher.command) > 1:
            print("Send command: {}".format(command))
            if command == "-rst":
                shproto.dispatcher.histogram = [0] * 8192
            tx_packet = shproto.packet()
            tx_packet.cmd = shproto.MODE_TEXT
            tx_packet.start()
            for i in range(len(command)):
                tx_packet.add(ord(command[i]))
            tx_packet.stop()
            nano.write(tx_packet.payload)
            nano.flushInput()
            with shproto.dispatcher.command_lock:
                shproto.dispatcher.command = ""
            time.sleep(NANO_WAIT_TIMEOUT)
        while nano.in_waiting > 0:
            rx_byte = nano.read()
            rx_int = int.from_bytes(rx_byte, byteorder='little')
            response.read(rx_int)
            if response.dropped:
                shproto.dispatcher.dropped += 1
            if not response.ready:
                continue
            shproto.dispatcher.total_pkts += 1
            if response.cmd == shproto.MODE_TEXT:
                shproto.dispatcher.pkts03 += 1
                resp_decoded = bytes(response.payload[:len(response.payload) - 2])
                try:
                    resp_decoded = resp_decoded.decode("ascii")
                except UnicodeDecodeError:
                    print("Unknown non-text response.")
                print("<< {}".format(resp_decoded))
                response.clear()
            elif response.cmd == shproto.MODE_HISTOGRAM:
                shproto.dispatcher.pkts01 += 1
                offset = response.payload[0] & 0xFF | ((response.payload[1] & 0xFF) << 8)
                count = int((response.len - 2) / 4)
                with shproto.dispatcher.histogram_lock:
                    for i in range(0, count):
                        index = offset + i
                        if index < len(shproto.dispatcher.histogram):
                            value = (response.payload[i * 4 + 2]) | \
                                    ((response.payload[i * 4 + 3]) << 8) | \
                                    ((response.payload[i * 4 + 4]) << 16) | \
                                    ((response.payload[i * 4 + 5]) << 24)
                            shproto.dispatcher.histogram[index] = value & 0x7FFFFFF
                response.clear()
            elif response.cmd == shproto.MODE_STAT:
                shproto.dispatcher.pkts04 += 1
                shproto.dispatcher.total_time = (response.payload[0] & 0xFF) | \
                                                ((response.payload[1] & 0xFF) << 8) | \
                                                ((response.payload[2] & 0xFF) << 16) | \
                                                ((response.payload[3] & 0xFF) << 24)
                shproto.dispatcher.cpu_load = (response.payload[4] & 0xFF) | ((response.payload[5] & 0xFF) << 8)
                shproto.dispatcher.cps = (response.payload[6] & 0xFF) | \
                                         ((response.payload[7] & 0xFF) << 8) | \
                                         ((response.payload[8] & 0xFF) << 16) | \
                                         ((response.payload[9] & 0xFF) << 24)
                if response.len >= (15 + 2):
                    shproto.dispatcher.lost_impulses = (response.payload[10] & 0xFF) | \
                                                       ((response.payload[11] & 0xFF) << 8) | \
                                                       ((response.payload[12] & 0xFF) << 16) | \
                                                       ((response.payload[13] & 0xFF) << 24)
                response.clear()
            else:
                print("Wtf received: cmd:{}\r\npayload: {}".format(response.cmd, response.payload))
                response.clear()
        time.sleep(NANO_WAIT_TIMEOUT)
    nano.close()


def process_01(filename):
    timer = 0
    print("Start writing spectrum to file: {}".format(filename))
    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 0
    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag):
        timer += 1
        time.sleep(1)
        if timer == 5:
            timer = 0
            with open(filename, "w") as fd:
                fd.seek(0)
                for i in range(0, 8192):
                    fd.writelines("{}, {}\n".format(i + 1, shproto.dispatcher.histogram[i]))
                fd.flush()
                fd.truncate()
    print("Stop collecting spectrum")


def stop():
    with shproto.dispatcher.stopflag_lock:
        shproto.dispatcher.stopflag = 1


def spec_stop():
    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 1


def process_03(_command):
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = _command


def clear():
    with shproto.dispatcher.histogram_lock:
        shproto.dispatcher.histogram = [0] * 8192
        shproto.dispatcher.pkts01 = 0
        shproto.dispatcher.pkts03 = 0
        shproto.dispatcher.pkts04 = 0
        shproto.dispatcher.total_pkts = 0
        shproto.dispatcher.cpu_load = 0
        shproto.dispatcher.cps = 0
        shproto.dispatcher.total_time = 0
        shproto.dispatcher.lost_impulses = 0
        shproto.dispatcher.dropped = 0
