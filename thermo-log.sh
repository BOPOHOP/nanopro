#! /bin/sh

id=${1:-AU03ZZ6F}

prefix=thermo
dir="$HOME/nanopro/temp-tests"


port=NONE

if [ -e /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0 ] ; then
	port=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0
fi
if [ -e /dev/cu.usbserial-$id ] ; then
	port=/dev/cu.usbserial-$id
fi




while /bin/true
do
	stamp_now=`date '+%Y-%m-%d_%H:%M:%S'`
	echo $stamp_now
	fname_spec="${prefix}-${stamp_now}-spec"
	fname_noise_log="${prefix}-${stamp_now}-noise"
	( sleep 10 ; echo noise_check ; sleep 55 ; echo spec_sta    ) | \
		python3 main.py -s -v -a -ci -T -E  -d ${port} "${fname_spec}" | \
		tee $dir/${fname_noise_log}.log
	sleep 3
done

