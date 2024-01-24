import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from struct import unpack
import binascii
import re
import xml.etree.ElementTree as ET

import shproto
import shproto.port

stopflag = 0
stopflag_lock = threading.Lock()
spec_stopflag = 0
spec_stopflag_lock = threading.Lock()

histogram = [0] * 8192
histogram_lock = threading.Lock()

histogram2 = [0] * 8192
histogram2_start = datetime.now(timezone.utc)
detector_ris  = -999
detector_fall = -999
detector_max  = -999
detector_temp = -999.99

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
total_pulse_width = 0
serial_number = ""
calibration = [0., 1., 0., 0., 0.]
inf_str = ''

max_pulses_buf = 10000
pulses_buf = []
pulse_file_opened = 0
pulses_debug_count = 0

start_timestamp = datetime.now(timezone.utc)

xml_out = 1
csv_out = 1

interspec_csv = 1
verbose = 0
verbose_prev = 0
hide_next_responce = False
hide_next_responce_lock  = threading.Lock()

pulse_avg_mode   = 0
pulse_avg_wanted = 1000
pileup_skip      = 8
pulse_avg_min     = 150	# DAC value
pulse_avg_max     = 1800	# DAC value
noise_threshold   = 14
noise_level       = 0
noise_sum_count   = 0

def start(sn=None):
    shproto.dispatcher.pulse_file_opened = 2
    # READ_BUFFER = 1
    READ_BUFFER = 4096
    # READ_BUFFER = 2048
    # READ_BUFFER = 8192
    # READ_BUFFER = 65536
    shproto.dispatcher.clear()
    with shproto.dispatcher.stopflag_lock:
        shproto.dispatcher.stopflag = 0
    nano = shproto.port.connectdevice(sn)
    response = shproto.packet()
    while not shproto.dispatcher.stopflag:
        if len(shproto.dispatcher.command) > 1:
            print("Send command: {}".format(command))
            if command == "-rst":
                shproto.dispatcher.clear()
            tx_packet = shproto.packet()
            tx_packet.cmd = shproto.MODE_TEXT
            tx_packet.start()
            for i in range(len(command)):
                tx_packet.add(ord(command[i]))
            tx_packet.stop()
            nano.write(tx_packet.payload)
            with shproto.dispatcher.command_lock:
                shproto.dispatcher.command = ""
        #        if nano.in_waiting == 0:
        #            time.sleep(0.05)
        #            continue
        READ_BUFFER = max(nano.in_waiting, READ_BUFFER)
        rx_byte_arr = nano.read(size=READ_BUFFER)
        # print("rx_byte_arr len = {}/{}".format(len(rx_byte_arr),READ_BUFFER))
        for rx_byte in rx_byte_arr:
            response.read(rx_byte)
            if response.dropped:
                shproto.dispatcher.dropped += 1
                shproto.dispatcher.total_pkts += 1
            if not response.ready:
                continue
            shproto.dispatcher.total_pkts += 1
            if response.cmd == shproto.MODE_TEXT:
                shproto.dispatcher.pkts03 += 1
                resp_decoded = bytes(response.payload[:len(response.payload) - 2])
                resp_lines = []
                try:
                    resp_decoded = resp_decoded.decode("ascii")
                    resp_lines = resp_decoded.splitlines()
                    if re.search('^VERSION', resp_decoded):
                        shproto.dispatcher.inf_str = resp_decoded
                        shproto.dispatcher.inf_str = shproto.dispatcher.inf_str.rstrip()
                        # shproto.dispatcher.inf_str = re.sub(r'\[[^]]*\]', '...', shproto.dispatcher.inf_str, count = 2)
                        # VERSION 13 RISE 7 FALL 8 NOISE 14 F 1000000.00 MAX 17118 HYST 1 MODE 0 STEP 1 t 156 POT 173 POT2 42 T1 28.5 T2 OFF T3 OFF Prise 40 Srise 8 OUT 0..0/1 Pfall 0 Sfall 0 TC ON TCpot ON Tco [-40 13128 -1 15530 2 15572 6 15920 10 16007 14 16404 18 16573 21 16783 25 16891 28 17107 32 17202 36 17348 40 17609 44 17755 48 17865 51 18001 56 18093 58 17422 0 0 0 0] TP 20000 PileUp [0.019 0.018 0.020 0.024 0.027 0.029 0.030 0.030 0.030 0.029 0.028 0.027 0.025 0.024 0.023 0.022 0.021 0.020 0.019 0.019 0.018 0.017 0.016 0.016 0.015 0.015 0.014 0.014 0.013 0.013 0.012 0.012 0.012 0.011 0.011 0.011 0.010 0.010 0.010 0.009 0.009 0.009 0.009 0.009 0.008 0.008 0.008 0.008 0.008 0.008 0.007 0.007 0.007 0.007 0.007 0.007 0.007 0.006 0.006 0.006 0.006 0.006 0.006 0.006 0.006 0.006 0.006 0.006 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.005 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.004 0.000] PileUpThr 1
                        # if (m := re.search('.*RISE\s+(\d+)\s+.*FALL\s+(\d+)\s+.*NOISE\s+(\d+)\s+.*\sMAX\s+(\d+)\s+.*\s+T1\s+([^ ]+)\s+.*',
                        if (m := re.search('.*RISE\s+(\d+)\s+.*FALL\s+(\d+)\s+.*NOISE\s+(\d+)\s+.*\sMAX\s+(\d+)\s+.*\sT1\s+(\S+).*',
                                resp_decoded)):
                            shproto.dispatcher.detector_ris  = int(m.group(1))
                            shproto.dispatcher.detector_fall = int(m.group(2))
                            shproto.dispatcher.detector_nos  = int(m.group(3))
                            shproto.dispatcher.detector_max  = int(m.group(4))
                            shproto.dispatcher.detector_temp = float(m.group(5))
                            print("detector ris: {} fall: {} max: {} tempereature: {}".format(
                                    shproto.dispatcher.detector_ris,
                                    shproto.dispatcher.detector_fall,
                                    shproto.dispatcher.detector_max,
                                    shproto.dispatcher.detector_temp))
                except UnicodeDecodeError:
                    print("Unknown non-text response.")
                if (not shproto.dispatcher.hide_next_responce and not re.search('^mi.*index.*', resp_decoded)):
                    # mi 5423 s 2 index 1388 integ 2900 mx 457 th 14 count 16 proc_case 3 from 5416 to 5432 pm 1 ):
                    print("<< got text")
                    print("<< {}".format(resp_decoded))
                    # print("pulse: {}".format(resp_decoded))
                with shproto.dispatcher.hide_next_responce_lock:
                    shproto.dispatcher.hide_next_responce = False
                if len(resp_lines) == 40:
                    shproto.dispatcher.serial_number = resp_lines[39]
                    print("got detector serial num: {}".format(shproto.dispatcher.serial_number))
                    b_str = ''
                    for b in resp_lines[0:10]:
                        b_str += b
                    # crc = hex(binascii.crc32(bytearray(b_str, 'ascii')) % 2**32)
                    crc = binascii.crc32(bytearray(b_str, 'ascii')) % 2 ** 32

                    if crc == int(resp_lines[10], 16):
                        shproto.dispatcher.calibration[0] = \
                            unpack('d', int((resp_lines[0] + resp_lines[1]), 16).to_bytes(8, 'little'))[0]
                        shproto.dispatcher.calibration[1] = \
                            unpack('d', int((resp_lines[2] + resp_lines[3]), 16).to_bytes(8, 'little'))[0]
                        shproto.dispatcher.calibration[2] = \
                            unpack('d', int((resp_lines[4] + resp_lines[5]), 16).to_bytes(8, 'little'))[0]
                        shproto.dispatcher.calibration[3] = \
                            unpack('d', int((resp_lines[6] + resp_lines[7]), 16).to_bytes(8, 'little'))[0]
                        shproto.dispatcher.calibration[4] = \
                            unpack('d', int((resp_lines[8] + resp_lines[9]), 16).to_bytes(8, 'little'))[0]
                        print("got calibration: {}".format(shproto.dispatcher.calibration))
                    else:
                        print("wrong crc for calibration values got: {:08x} expected: {:08x}".format(
                            int(resp_lines[10], 16), crc))

                response.clear()
            elif response.cmd == shproto.MODE_HISTOGRAM:
                # print("<< got histogram")
                shproto.dispatcher.pkts01 += 1
                # offset = response.payload[0] & 0xFF | ((response.payload[1] & 0xFF) << 8)
                offset = unpack("<H", bytes(response.payload[0:2]))[0]
                count = int((response.len - 2) / 4)
                # print("histogram count: {} offset: {}".format(count, offset))
                with shproto.dispatcher.histogram_lock:
                    if offset <= 8192 and offset + count <= 8192:
                        format_unpack_str = "<{}I".format(count)

                        shproto.dispatcher.histogram[offset:offset + count] = list(
                            unpack(format_unpack_str, bytes(response.payload[2:count * 4 + 2])))
                    else:
                        print("histogram index is out of range: {} - {} c:{}".format(offset, offset + count,
                                                                                     offset + count))
                response.clear()
            elif response.cmd == shproto.MODE_PULSE:
                # print("<< got pulse")
                shproto.dispatcher.pkts01 += 1
                count = int((response.len - 2) / 2)
                format_unpack_str = "<{}H".format(count)
                # format_print_str = "{}{:d}:d{}".format("{", count, "}")
                pulse = list(unpack(format_unpack_str, bytes(response.payload[2:count * 2 + 2])))
                # str3 = ' '.join("{:d}".format(p) for p in  pulse1)
                # print("format: {} {} pulse unpack: {}".format(format_unpack_str, format_print_str, str3))
                # for i in range(0, count):
                #     index = offset + i
                #     if index < len(shproto.dispatcher.histogram):
                #         value = (response.payload[i * 2 + 2]) | \
                #                 ((response.payload[i * 2 + 3]) << 8)
                #         pulse = pulse + [(value & 0x7FFFFFF)]
                #     fd_pulses.writelines("{:d} ".format(value & 0x7FFFFFF))
                if len(shproto.dispatcher.pulses_buf) < max_pulses_buf:
                    with shproto.dispatcher.histogram_lock:
                        shproto.dispatcher.pulses_buf.append(pulse)
                # print("len: ", count, "shape: ", pulse)
                response.clear()
            elif response.cmd == shproto.MODE_STAT:
                # print("<< got stat")
                shproto.dispatcher.pkts04 += 1
                shproto.dispatcher.total_time = unpack("<I", bytes(response.payload[0:4]))[0]
                shproto.dispatcher.cpu_load = unpack("<H", bytes(response.payload[4:6]))[0]
                shproto.dispatcher.cps = unpack("<I", bytes(response.payload[6:10]))[0]
                if response.len >= (11 + 2):
                    shproto.dispatcher.lost_impulses = unpack("<I", bytes(response.payload[10:14]))[0]
                if response.len >= (15 + 2):
                    shproto.dispatcher.total_pulse_width = unpack("<I", bytes(response.payload[14:18]))[0]
                # print("stat elapsed: {} cps: {} total: {} lost: {} cpu: {} total_pulse_width: {}".format(
                #  shproto.dispatcher.total_time, shproto.dispatcher.cps, shproto.dispatcher.total_pkts,
                #  shproto.dispatcher.lost_impulses, shproto.dispatcher.cpu_load, shproto.dispatcher.total_pulse_width))
                response.clear()
            else:
                print("Wtf received: cmd:{}\r\npayload: {}".format(response.cmd, response.payload))
                response.clear()
    nano.close()


def process_01(filename):
    filename_pulses = re.sub(r'\.csv$', '', filename, flags=re.IGNORECASE)
    filename_pulses += "_pulses.dat"
    filename_xml = re.sub(r'\.csv$', '', filename, flags=re.IGNORECASE)
    filename_xml += ".xml"
    timer = 0

    pulse_avg_center  = 100
    pulse_avg_size    = 301
    pulse_avg         = [0] * pulse_avg_size
    pulse_avg_count   = 0
    pulse_avg_printed = 0

    noise_sum         = 0
    shproto.dispatcher.noise_sum_count   = 0
    noise_sum_count_prev = 0
    noise_sum_prev       = 0
    shproto.dispatcher.histogram2_start = datetime.now(timezone.utc)
    shproto.dispatcher.histogram2 = [0] * 8192
    timer2 = 1

    print("Start writing spectrum to file: {}".format(filename))
    print("avg mode: {}".format(shproto.dispatcher.pulse_avg_mode))
    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 0
    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag):
        timer += 1
        timer2 += 1
        time.sleep(1)
        if timer2 == 180:
            timer2 = 0
            shproto.dispatcher.process_03("-inf")
        if timer == 5:
            timer = 0
            with shproto.dispatcher.histogram_lock:
                histogram = shproto.dispatcher.histogram
            spec_pulses_total = sum(histogram)
            spec_pulses_total_cps = 0
            spec_timestamp = datetime.now(timezone.utc) - timedelta(seconds=shproto.dispatcher.total_time)
            if shproto.dispatcher.total_time > 0 or len(shproto.dispatcher.pulses_buf) > 0:
                if shproto.dispatcher.total_time == 0:
                    spec_pulses_total_cps = 0
                else: 
                    spec_pulses_total_cps = float(spec_pulses_total) / float(shproto.dispatcher.total_time)
                if shproto.dispatcher.csv_out:
    
                    with shproto.dispatcher.histogram_lock:
                        # print("{} pulses in buf".format(len(shproto.dispatcher.pulses_buf)))
                        pulses = shproto.dispatcher.pulses_buf
                        shproto.dispatcher.pulses_debug_count += len(shproto.dispatcher.pulses_buf)
                        shproto.dispatcher.pulses_buf = []

                    shproto.dispatcher.pulse_avg_mode = 22
                    if shproto.dispatcher.pulse_avg_mode == 22:
                        if (shproto.dispatcher.detector_fall < 0) or (shproto.dispatcher.detector_max < 0) or (shproto.dispatcher.detector_nos < 0):
                            continue
                        pulse_ris  = 5
                        pulse_preamb  = 4
                        for pulse in pulses:
                            if (len(pulse) < (
                                        pulse_preamb + max(pulse_ris, 9) 
                                        + shproto.dispatcher.detector_fall)): # 4(avg)+8(ris)+fall
                                continue
                            pulse_base = sum(pulse[0:pulse_preamb])/pulse_preamb
                            pulse_max  = max(pulse)
                            pulse_len  = pulse_ris + shproto.dispatcher.detector_fall
                            pulse_sum  = sum(pulse[len(pulse) - pulse_len:])
                            # pulse_bin  = int((pulse_sum - pulse_base*pulse_len) / shproto.dispatcher.detector_max * 8192)
                            pulse_bin  = int((pulse_sum) / shproto.dispatcher.detector_max * 8192)
                            if (pulse_max < shproto.dispatcher.detector_nos):
                                print("pulse preambula too low: {}".format(pulse))
                            pulse_preamb_len = len(pulse) - shproto.dispatcher.detector_fall - max(9, pulse_ris)
                            pulse_preamb_max = max(pulse[0:pulse_preamb_len])
                            if (pulse_preamb_max > shproto.dispatcher.detector_nos) or (pulse_preamb_max > pulse_max * 0.1):
                                print("pulse preambula too HI: {}".format(pulse))
                            if (pulse_bin >= 8192 or pulse_bin < 0):
                                pulse_bin = 8191
                            # print("pulse base: {} max: {} sum: {} bin: {} p: {}".format( pulse_base, pulse_max, pulse_sum, pulse_bin, pulse))
                            shproto.dispatcher.histogram2[pulse_bin] += 1
                        histogram = shproto.dispatcher.histogram2
###
                        spec_pulses_total = sum(histogram)
                        spec_pulses_total_cps = 0
                        spec_timestamp = shproto.dispatcher.histogram2_start
                        shproto.dispatcher.total_time = int((datetime.now(timezone.utc)-spec_timestamp).total_seconds())
                        if shproto.dispatcher.total_time > 0 or len(shproto.dispatcher.pulses_buf) > 0:
                            if shproto.dispatcher.total_time == 0:
                                spec_pulses_total_cps = 0
                            else: 
                                spec_pulses_total_cps = float(spec_pulses_total) / float(shproto.dispatcher.total_time)
###
                        

                    with open(filename, "w") as fd:
                        if shproto.dispatcher.interspec_csv:
                            fd.writelines("calibcoeff : a={} b={} c={} d={}\n".format(
                                shproto.dispatcher.calibration[3],
                                shproto.dispatcher.calibration[2],
                                shproto.dispatcher.calibration[1],
                                shproto.dispatcher.calibration[0]))
                            fd.writelines(
                                "remark, elapsed: {:d}H:{:02d}m/{:d}s/{:.2f}m cps: {:7.2f} total_pulses: {} total_pkts: {} drop_pkts: {} lostImp: {}\n".format(
                                    int(shproto.dispatcher.total_time/3600), int((shproto.dispatcher.total_time%3600)/60),
                                    shproto.dispatcher.total_time, 
                                    shproto.dispatcher.total_time/60.,
                                    spec_pulses_total_cps, spec_pulses_total, shproto.dispatcher.total_pkts,
                                    shproto.dispatcher.dropped, shproto.dispatcher.lost_impulses
                                    ))
                            if shproto.dispatcher.inf_str != "":
                                fd.writelines("remark, inf: {}\n".format(shproto.dispatcher.inf_str))
                            fd.writelines("livetime, {}\n".format(shproto.dispatcher.total_time))
                            fd.writelines("realtime, {}\n".format(shproto.dispatcher.total_time))
                            detectorname_str = 'n15'
                            if (shproto.dispatcher.detector_ris > 0 and shproto.dispatcher.detector_fall > 0
                                    and shproto.dispatcher.detector_nos > 0):
                                detectorname_str = "n15-{}-n{}-r{}-f{}".format(
                                        shproto.dispatcher.serial_number,
                                        shproto.dispatcher.detector_nos,
                                        shproto.dispatcher.detector_ris,
                                        shproto.dispatcher.detector_fall
                                        )
                            fd.writelines("detectorname,{}\nSerialNumber,{}\n".format(
                                    detectorname_str, detectorname_str))
                            fd.writelines("starttime, {}\n".format(spec_timestamp.strftime("%Y-%m-%dT%H:%M:%S+00:00")))
                            fd.writelines("ch,data\n")
                        if len(histogram) > 8192:
                            print("histogram len too long {}".format(len(histogram)))
                        for i in range(0, len(histogram)):
                            fd.writelines("{}, {}\n".format(i + 1, histogram[i]))

                    if shproto.dispatcher.pulse_avg_mode == 1:
                        if shproto.dispatcher.pulse_avg_wanted > pulse_avg_count:
                            for pulse in pulses:
                                v_max = max(pulse)
                                if (v_max < shproto.dispatcher.pulse_avg_min or v_max > shproto.dispatcher.pulse_avg_max):
                                    continue
                                for i, v in enumerate(pulse):
                                    if v == v_max:
                                        break
                                center_idx = i
                                if (center_idx + shproto.dispatcher.pileup_skip + 100 >= len(pulse)) or (center_idx == 0): # overlaping
                                    continue
                                # print("pulse max {} at {} {}".format(v_max, center_idx, pulse))
                                # print("pulse max {} at {}".format(v_max, center_idx))
                                if (max(pulse[center_idx + shproto.dispatcher.pileup_skip:]) < v_max * 0.1): # no big pulses at tail
                                    # print("pulse is good")
                                    # print("pulse max {} at {} {}".format(v_max, center_idx, pulse))
                                    pulse_avg_count += 1
                                    # print("from {} to {}".format(max(0, center_idx-pulse_avg_center), min(pulse_avg_size-pulse_avg_center, len(pulse))))
                                    range_start = max(0,center_idx - pulse_avg_center) + pulse_avg_center - center_idx
                                    range_end   = min(pulse_avg_size - pulse_avg_center, len(pulse)) + pulse_avg_center - center_idx
                                    for i in range(range_start, range_end):
                                        #  print("agv[{}] += pulse[{}]".format(pulse_avg_center - center_idx + i, i))
                                        pulse_avg[i] += pulse[i - pulse_avg_center + center_idx]
                            print("pulse averaging collected in range: {} pulses total: {}".format(
                                    pulse_avg_count, shproto.dispatcher.pulses_debug_count))
                        # print("ranges0: {} - {} : {} {}".format(range_start,range_end, pulse_avg_center, center_idx))
                        if shproto.dispatcher.pulse_avg_wanted <= pulse_avg_count:
                            if not pulse_avg_printed and pulse_avg_count > 0:
                                pulse_avg_printed = 1
                                avg_max = max(pulse_avg)
                                pulse_avg_normal = [(v/avg_max)  for v in pulse_avg]
                                for idx_start in range(0, pulse_avg_center+1):
                                    if pulse_avg[idx_start] != 0:
                                        break
                                for idx_stop in range(pulse_avg_size-1, pulse_avg_center+1, -1):
                                    if pulse_avg[idx_stop] != 0:
                                        break
                                # print("data buf from {} to {}".format(idx_start, idx_stop))
                                print("{} pulses collected in range from {} to {}".format(pulse_avg_count,
                                        shproto.dispatcher.pulse_avg_min, shproto.dispatcher.pulse_avg_max))
                                print("pulse rise: {}".format(','.join("{:.3f}".format(p) 
                                        for p in pulse_avg_normal[idx_start:pulse_avg_center+1])))
                                print("pulse fall: {}".format(','.join("{:.3f}".format(p) 
                                        for p in pulse_avg_normal[pulse_avg_center+1:idx_stop+1])))
                                print("pileup skip {}".format(shproto.dispatcher.pileup_skip))
                                print("setup command w   noise: -pileup {}".format(' '.join("{:.3f}".format(p) 
                                        for p in pulse_avg_normal[pulse_avg_center + shproto.dispatcher.pileup_skip + 1
                                                :min(100 + pulse_avg_center + shproto.dispatcher.pileup_skip, pulse_avg_size)])))
                                print("setup command w/o noise: -pileup {}".format(' '.join("{:.3f}"
                                                .format(p - shproto.dispatcher.noise_level * pulse_avg_count / avg_max) 
                                        for p in pulse_avg_normal[pulse_avg_center + shproto.dispatcher.pileup_skip + 1
                                                :min(100 + pulse_avg_center + shproto.dispatcher.pileup_skip, pulse_avg_size)])))
                                # print("ranges: {} - {} : {} {}".format(range_start,range_end, pulse_avg_center, center_idx))
                                print("shape_f: {}".format(','.join("{:.3f}".format(p) 
                                        for p in pulse_avg_normal[range_start:range_end])))
                                print("shape_i: {}".format(','.join("{:d}".format(int(p/pulse_avg_count)) 
                                        for p in pulse_avg[range_start:range_end])))
                            shproto.dispatcher.process_03("-sto")
                            time.sleep(2)
                            shproto.dispatcher.process_03("-fall {:d}".format(shproto.dispatcher.pileup_skip))
                            time.sleep(2)
                            shproto.dispatcher.process_03("-pthr 1")
                            time.sleep(2)
                            shproto.dispatcher.process_03("-mode 0")
                            time.sleep(2)
                            shproto.dispatcher.verbose = shproto.dispatcher.verbose_prev
                            shproto.dispatcher.spec_stop()
                            shproto.dispatcher.pulse_avg_mode = False
    
                    if shproto.dispatcher.pulse_avg_mode == 2:
                            for pulse in pulses:
                                pulse[len(pulse) - 2] = 4095
                                v_max = 0
                                no_pulse_idx_start = 0
                                for i, v in enumerate(pulse):
                                    if i <= no_pulse_idx_start:
                                        continue
                                    if v < shproto.dispatcher.noise_threshold:
                                        continue
                                    else:
                                        if i - no_pulse_idx_start >= 100:
                                            noise_sum += sum(pulse[no_pulse_idx_start:i])
                                            shproto.dispatcher.noise_sum_count += i - no_pulse_idx_start
                                            shproto.dispatcher.noise_level = noise_sum/shproto.dispatcher.noise_sum_count
                                            # print("no pulse: {:d}-{:d} total count: {:d} avg_noise: {:.2f}"
                                            #         .format(no_pulse_idx_start, i-1, shproto.dispatcher.noise_sum_count,
                                            #                 shproto.dispatcher.noise_level))
                                        no_pulse_idx_start = i + 100
                            if (shproto.dispatcher.noise_sum_count - noise_sum_count_prev) > 0:
                                noise_level_delta = ((noise_sum - noise_sum_prev)
                                        / (shproto.dispatcher.noise_sum_count - noise_sum_count_prev))
                            noise_sum_count_prev = shproto.dispatcher.noise_sum_count
                            noise_sum_prev       = noise_sum
                            print("noise collector: total count: {:d} avg_noise: {:.2f} last: {:.2f}"
                                    .format(shproto.dispatcher.noise_sum_count,
                                            shproto.dispatcher.noise_level, noise_level_delta))

                    if shproto.dispatcher.pulse_avg_mode == 0:
                        if len(pulses) > 0 and shproto.dispatcher.pulse_file_opened != 1 and (fd_pulses := open(filename_pulses, "w+")):
                            shproto.dispatcher.pulse_file_opened = 1
                        if shproto.dispatcher.pulse_file_opened == 1:
                            for pulse in pulses:
                                fd_pulses.writelines("{}\n".format(' '.join("{:d}".format(p) for p in  pulse )))
                            fd_pulses.flush()

                if shproto.dispatcher.xml_out:
                    xml = build_xml(histogram, shproto.dispatcher.calibration, shproto.dispatcher.total_time,
                                    spec_timestamp, datetime.now(timezone.utc), shproto.dispatcher.serial_number,
                                    shproto.dispatcher.inf_str)
                    ET.indent(xml, space=' ')
                    xml_str = ET.tostring(xml, encoding="utf-8", method="xml", xml_declaration=True)
                    with open(filename_xml, "w") as fd:
                        fd.write(xml_str.decode(encoding="utf-8"))

            print(
                "elapsed: {}/{:.0f} cps: {}/{:.2f} total_pkts: {} drop_pkts: {} "
                "lostImp: {} cpu: {} dbg_pulses: {}".format(
                    shproto.dispatcher.total_time,
                    (datetime.now(timezone.utc) - shproto.dispatcher.start_timestamp).total_seconds(),
                    shproto.dispatcher.cps, spec_pulses_total_cps,
                    shproto.dispatcher.total_pkts, shproto.dispatcher.dropped,
                    shproto.dispatcher.lost_impulses, shproto.dispatcher.cpu_load,
                    shproto.dispatcher.pulses_debug_count))
    if shproto.dispatcher.pulse_file_opened == 1:
        fd_pulses.close()
        shproto.dispatcher.pulse_file_opened = 0

    print("Stop collecting spectrum")

def build_xml(histogram, calibration, elapsed, start, end, dev_serialno, comment):
    for i in range(len(calibration), 0, -1):
        if calibration[i - 1] != 0:
            break
    calibration = calibration[0:i]
    # et = xml.etree.ElementTree('ResultDataFile')
    ns = {"xmlns:xsd": "http://www.w3.org/2001/XMLSchema", "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"}
    xmlroot = ET.Element("ResultDataFile", ns)
    FormatVersion = ET.SubElement(xmlroot, "FormatVersion")
    FormatVersion.text = "test"
    ResultDataList = ET.SubElement(xmlroot, "ResultDataList")
    ResultData = ET.SubElement(ResultDataList, "ResultData")
    SampleInfo = ET.SubElement(ResultData, "SampleInfo")
    SampleName = ET.SubElement(SampleInfo, "Name")
    SampleNote = ET.SubElement(SampleInfo, "Note")
    SampleNote.text = comment
    DeviceConfigReference = ET.SubElement(ResultData, "DeviceConfigReference")
    DeviceConfigReferenceName = ET.SubElement(DeviceConfigReference, "Name")
    DeviceConfigReferenceName.text = "nanopro-{}".format(dev_serialno)
    BackgroundSpectrumFile = ET.SubElement(ResultData, "BackgroundSpectrumFile")
    StartTime = ET.SubElement(ResultData, "StartTime")
    StartTime.text = "{}".format(start.strftime("%Y-%m-%dT%H:%M:%S+00:00"))
    EndTime = ET.SubElement(ResultData, "EndTime")
    EndTime.text = "{}".format(end.strftime("%Y-%m-%dT%H:%M:%S+00:00"))

    EnergySpectrum = ET.SubElement(ResultData, "EnergySpectrum")

    EnergySpectrum_NumberOfChannels = ET.SubElement(EnergySpectrum, "NumberOfChannels")
    EnergySpectrum_NumberOfChannels.text = "{:d}".format(len(histogram))
    EnergySpectrum_ChannelPitch = ET.SubElement(EnergySpectrum, "ChannelPitch")
    EnergySpectrum_ChannelPitch.text = "1"
    EnergySpectrum_SpectrumName = ET.SubElement(EnergySpectrum, "SpectrumName")
    EnergySpectrum_SpectrumName.text = "spectrum {} {:d}".format(end.strftime("%Y-%m-%dT%H:%M:%S+00:00"), elapsed)
    EnergySpectrum_Comment = ET.SubElement(EnergySpectrum, "Comment")
    EnergySpectrum_Comment.text = comment

    EnergySpectrum_EnergyCalibration = ET.SubElement(EnergySpectrum, "EnergyCalibration")
    PolynomialOrder = ET.SubElement(EnergySpectrum_EnergyCalibration, "PolynomialOrder")
    PolynomialOrder.text = "{}".format(len(calibration) - 1)
    Coefficients = ET.SubElement(EnergySpectrum_EnergyCalibration, "Coefficients")
    for val in calibration:
        Coefficient = ET.SubElement(Coefficients, "Coefficient")
        Coefficient.text = "{}".format(val)
    EnergySpectrum_MeasurementTime = ET.SubElement(EnergySpectrum, "MeasurementTime")
    EnergySpectrum_MeasurementTime.text = "{}".format(elapsed)
    EnergySpectrum_ValidPulseCount = ET.SubElement(EnergySpectrum, "ValidPulseCount")
    EnergySpectrum_ValidPulseCount.text = "{}".format(sum(histogram))

    Spectrum = ET.SubElement(EnergySpectrum, "Spectrum")
    for val in histogram:
        DataPoint = ET.SubElement(Spectrum, "DataPoint")
        DataPoint.text = "{}".format(val)

    ResultData_Visible = ET.SubElement(ResultData, "Visible")
    ResultData_Visible.text = "true"
    ResultData_PulseCollection = ET.SubElement(ResultData, "PulseCollection")
    ResultData_PulseCollection_Format = ET.SubElement(ResultData_PulseCollection, "Format")
    ResultData_PulseCollection_Format.text = "Base64 encoded binary"
    ResultData_PulseCollection_Pulses = ET.SubElement(ResultData_PulseCollection, "Pulses")

    return xmlroot


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
        shproto.dispatcher.total_pulse_width = 0
        shproto.dispatcher.dropped = 0

