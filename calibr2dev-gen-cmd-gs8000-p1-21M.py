#! /usr/bin/python3.11

from struct import *
import binascii



# coeff = [5.15, 0.3298, 1.044E-05, 0, 0] # p1c1-21M gs8000-00000210-n12-r10-f10-U17 20.5C cs+am+lu+K/Th
# coeff = [-1.6, 0.3415, 1.377E-05, 0, 0] # p1c1-21M gs8000-00000210-n12-r7-f7-U18 20.5C ra
# coeff = [-1.5, 0.3401, 1.458E-05, 0, 0] # p1c1-21M gs8000-00000210-n12-r7-f7-U18 21.0C ra cs am K
# coeff = [-1.1, 0.3433, 1.401E-05, 0, 0] # p1c1-21M gs8000-00000210-n12-r7-f7-U18 21.0C ra cs am K
coeff = [-1.8, 0.33700, 1.347E-05, 0, 0 ]# p1c1s2-21M gs8000-00000210-n12-r7-f7-U18 2024.10.29 22.0C ra th am lu cs

coeff = coeff + [0, 0, 0, 0, 0]
coeff = coeff[0:5]

echo = 'echo '

str = ''
r_n = 0
i = 0
c_b = [ pack('d', 0.) ] * 12
s = ''
print("sleep 10\n")
for  v in coeff:
	c_b[i] = pack('d', coeff[i])
	vv = unpack('II', c_b[i])
	s += "%08X" % (vv[1])
	# print(coeff[i], vv)
	print("{}-cal {} {:08X}".format(echo, r_n, vv[1]))
	print("sleep 2\n")
	s += "%08X" % (vv[0])
	r_n += 1
	print("{}-cal {} {:08X}".format(echo, r_n, vv[0]))
	r_n += 1
	i += 1
	print("sleep 2\n")

# print(s)
crc = binascii.crc32(bytearray(s, "ascii")) % 2**32


# print(s, crc)
print("{}-cal {} {:08X}".format(echo, r_n, crc))
print("sleep 2\n")
print("{}quit\n".format(echo))

