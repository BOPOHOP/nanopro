#! /bin/sh

id=AU03ZZ6F
port=NONE

if [ -e /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0 ] ; then
	port=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0
fi
if [ -e /dev/cu.usbserial-$id ] ; then
	port=/dev/cu.usbserial-$id
fi

filename=${1:-spectrum-n15.csv}

while true
do
	( sleep 20 ; echo quit ) | python3 main.py -s -v -a -ci -x -d ${port} ${filename}

	date
	sleep 600
done
