#! /bin/sh

id=B0028ROO
port=NONE

if [ -e /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0 ] ; then
	port=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_$id-if00-port0
fi
if [ -e /dev/cu.usbserial-$id ] ; then
	port=/dev/cu.usbserial-$id
fi

filename=${1:-gs-tmp.csv}
base_dir=${HOME}/nanopro/gs

[ -d $base_dir ] || mkdir -p $base_dir


python3 main.py -s -v -a -ci -x -b ${base_dir} -d ${port} ${filename}

