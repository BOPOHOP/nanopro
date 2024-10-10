#! /usr/bin/python3.11

from struct import *
import binascii



#coeff = [ -8.5, 0.3827, 2.127e-06, 0, 0 ]
# coeff = [ -3.22721, 0.365377, 1.15403E-05, -1.13138E-09, 0 ]
# coeff = [ -3.10327, 0.368445, 9.2457E-06, -8.52471E-10, 0 ]
# coeff = [ -3.50753, 0.369576, 8.31747E-06, -7.33575E-10, 0 ]
#coeff =   [ -5.81279, 0.37369,  6.0335E-06, -4.51995E-10, 0 ] # nos14 rise7 fall8 srise3 prise8 pfall0 sfall0 stdTHR
#coeff =   [-7.80666, 0.37386, 6.23949E-06, -4.57829E-10, 0 ]   # nos14 rise7 fall8 srise30 prise8 pfall0 sfall0 MyTHR2
#coeff =   [-6.62242, 0.372515, 6.62352E-06, -4.8421E-10, 0]   # nos14 rise7 fall8 prise40 srise8 pfall0 sfall0 StdTHR

#coeff =   [-5.47761, 0.373181, 6.15434E-06, -4.64364E-10, 0]   # nos14 rise5 fall8 prise40 srise8 pfall0 sfall0 StdTHR+
#coeff =   [-5.5677,  0.372833, 6.2539E-06,  -4.71869E-10, 0]   # nos14 rise5 fall8 prise40 srise8 pfall0 sfall0 StdTHR+

# coeff =   [-6.62242, 0.372515, 6.62352E-06, -4.8421E-10, 0]   # 2M nos14 rise7 fall8 prise40 srise8 pfall0 sfall0 StdTHR

#coeff =   [-8.29109, 0.369356, 6.67704E-06, -5.31864E-10, 0]   # nos14 rise5 fall8 prise40 srise8 pfall0 sfall0 StdTHR+ Fix-0.99

#coeff =   [-5.565360, 3.71104e-01, 5.86174e-06, -4.26725e-10, 0]   # nos14 rise5 fall8 prise40 srise8 pfall0 sfall0 MyTHR5

coeff =   [-9.95037, 0.377817, 4.70725e-06, -3.1341e-10, 0.0 ]   # nos14 rise5 fall8 prise40 srise8 pfall10 sfall15 MyTHR5

echo = 'echo '

str = ''
r_n = 0
i = 0
c_b = [ pack('d', 0.) ] * 12
s = ''
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

