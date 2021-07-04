test:
	python iqreader.py -v -i data/rxa6982-long.raw
	python iqreader.py -u16 -r16 -i data/rxa6982-long.raw

run:
	python iqreader.py -v --osr 4 -t /srv/breamdisk/adsb-data/x1

run_rx_sdr:
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 -g 40.2 - |python iqreader.py -i - -o x

run_rtl_sdr:
	rtl_sdr -f 1090000000 -s 2000000 -g 0 -|python iqreader.py - -o x

run_dump1090:
	# ../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 40.2 |~/bin/dump1090 --ifile - --interactive --metric --aggressive --net
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - |~/bin/dump1090 --ifile - --metric --aggressive --net

clean:
	-rm -f *.iq *-iqindex.txt
