test:
	./adsb_read.py -v -i data/rxa6982-long.raw
	./adsb_read.py -u16 -r16 -i data/rxa6982-long.raw

run:
	./adsb_read.py -v --osr 4 -t /srv/breamdisk/adsb-data/x1

run_rx_sdr:
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 -g 40.2 - |python adsb_read.py -i - -o x

run_rtl_sdr:
	rtl_sdr -f 1090000000 -s 2000000 -g 0 -|python adsb_read.py - -o x

clean:
	-rm -f *.iq *-iqindex.txt
