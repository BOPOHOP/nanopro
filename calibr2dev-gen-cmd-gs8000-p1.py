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

#coeff =   [-9.95037, 0.377817, 4.70725e-06, -3.1341e-10, 0.0 ]   # nos14 rise5 fall8 prise40 srise8 pfall10 sfall15 MyTHR5
#coeff =   [3.55577, 0.346779, 1.54428E-05, -9.30348E-10, 0 ]   # p2 gs8000-00000210-n24-r5-f10
#coeff =   [2.186, 0.378226, 1.53344E-05, -4.79623E-10, 0]   # p2 gs8000-00000210-n24-r5-f10

#coeff = [2.21642, 0.336554, 1.24378E-05, -1.58528E-10, 0]  # p1 gs8000-00000210-n19-r5-f10 cs
#coeff = [-1.56037, 0.346996, 1.71523E-06, 1.37559E-09, 0 ] # p1 gs8000-00000210-n19-r5-f10 ra
#coeff = [-0.259624, 0.339005, 9.37288E-06, 8.72741E-11, 0] # p1 gs8000-00000210-n19-r5-f10 ra cs
#coeff = [0.564611, 0.338627, 1.04519E-05, 1.17122E-10, 0] # p1 gs8000-00000210-n19-r5-f10 ra cs am lu th 22.0C ? ok?
#coeff = [-4.06459, 0.358415, 6.87158E-07, 1.19903E-09, 0] # p1 gs8000-00000210-n22-r5-f10 ra cs am lu th 22.0C step2 prise99 srise7
#coeff = [-0.599348, 0.341377, 1.31414E-05, -3.39304E-10, 0] # p1 gs-cs-br-p1-02-s2-prise0 cs  th 23.0C step2 prise0 srise0
# coeff = [-3.14034, 0.345291, 1.18361E-05, -2.20407E-10, 0] # p1 gs-cs-br-p1-02-s2-prise0 cs th am 23.0C
# coeff = [-3.20652, 0.34745, 1.03018E-05, -3.01319E-11, 0] # p1 gs-cs-br-p1-02-s2-prise0 cs th am lu ra 23.0C
#coeff = [-5.93646, 0.359836, 6.28683E-06, 5.18059E-10, 0]  # p1 gs8000-00000210-n23-r5-f10 th 21.5C +1/4оборота
#coeff = [-6.95485, 0.361911, 6.0965E-06, 4.80042E-10, 0]  # p1 gs8000-00000210-n23-r5-f10 th 21.5C +1/4оборота
#coeff = [-6.24467, 0.359538, 5.60859E-06, 6.45875E-10, 0]  # p1 gs8000-00000210-n23-r5-f10 th,cs,lu,am 21.5C +1/4оборота
#coeff = [-5.90599, 0.356927, 7.08263E-06, 4.81285E-10, 0]  # p1 gs8000-00000210-n23-r5-f10 th,cs,lu,am,ra 21.5C +1/4оборота 32768
# coeff = [-5.40781, 0.355777, 8.24993E-06, 0, 0] # p1 +1/4обор gs8000-00000210-n17-r5-f10 prise99 srise7 22C ra
# coeff = [-5.76, 0.3571, 8.2561E-06, 0, 0]  # p1 +1/4обор gs8000-00000210-n17-r5-f10 prise99 srise7 22C ra th cs am
# coeff = [2.30743, 0.393586, 5.05085E-06, 0, 0] # p1 gs8000-00000210-n9-r5-f10 prise99 srise5 20C cs am lu th
# coeff = [0.283, 0.4019, -1.673E-06, 8.851E-10, 0] # p1 gs8000-00000210-n9-r5-f10 prise99 srise5 20C cs am lu th ra
# coeff = [-2.77107, 0.379849, 7.3119E-06, 0, 0] # p1 gs8000-00000210-n12-r7-f10 
# coeff = [-2.893, 0.3842, 5.417E-06, 2.308E-10, 0] # p1 gs8000-00000210-n11-r5-f10 20C cs am lu th ra
#coeff = [-5.39373, 0.38548, 7.7255E-06, 0, 0] # p1c gs8000-00000210-n13-r5-f10 th 21.5C
#coeff = [ 0.142569, 0.379582, 8.16306E-06, 0, 0] # p1c gs8000-00000210-n13-r5-f10 cs am lu th 19.5C
#coeff = [ -0.456544, 0.338339, 9.56628E-06, 0, 0] # p1c gs8000-00000210-n14-r5-f10 cs am lu th 19.5C
#coeff = [-2.19351, 0.340152, 8.90024E-06, 0, 0] # p1c gs8000-00000210-n14-r5-f10-U20 cs sm th ra 21
#coeff = [-2.19351, 0.340152, 8.90024E-06, 0, 0] # p1c gs8000-00000210-n14-r5-f10-U20 cs sm th ra 21
# coeff = [-1.52717, 0.338941, 9.64372E-06, 0, 0] # p1c1 8000-00000210-n13-r5-f10-U17 th am cs lu ra 20.5C
#coeff = [-4, 0.3347, 9.65E-06, 0, 0] # p1c1 gs8000-00000210-n14-r5-f10-U17 19C th cs (am+th)
#coeff = [-4, 0.3347, 9.65E-06, 0, 0] # p1c1 gs8000-00000210-n14-r5-f10-U17 19C th cs (am+th)
#coeff = [-4, 0.348, 1.15E-05, 0, 0] # p1c1 gs8000-00000210-n15-r5-f7-U17 подогнано под предыдущий f10
#coeff = [-4, 0.373, 1.25E-05, 0, 0] # p1c1 gs8000-00000210-n15-r5-f5-U17 подогнано под предыдущий f10
#coeff = [-1.4, 0.3261, 1.516E-05, 4.003E-10] # gs8000-00000210-n14-r5-f5-U21 cs am lu ra th
coeff = [0.5, 0.33700, 1.347E-05, 0, 0 ] # gs8000-00000210-n14-r5-f5-U18

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

