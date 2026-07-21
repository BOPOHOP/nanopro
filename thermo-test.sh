#! /bin/sh

id=${1:-AU03ZZ6F}

prefix=thermo-nt5
dir="$HOME/nanopro/temp-tests"


port=NONE

while /bin/true
do
	if [ -e /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0 ] ; then
		port=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0
	fi
	if [ -e /dev/cu.usbserial-$id ] ; then
		port=/dev/cu.usbserial-$id
	fi

	stamp_now=`date '+%Y-%m-%d_%H:%M:%S'`
	echo $stamp_now
	fname_spec="${prefix}-${stamp_now}-spec"
	fname_noise_log="${prefix}-${stamp_now}-noise"
	if [ -e "${port}" ] ; then
		python3 main.py -s -v -a -ci -TNB  -d ${port} "${fname_spec}"  | \
			tee $dir/${fname_noise_log}.log
	fi
	sleep 3
done

