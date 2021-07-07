PLDATALOC=	/srv/breamdisk/adsb-data
J03DATALOC=	.

test:
	python adsb_read.py -v -i data/rxa6982-long.raw
	python adsb_read.py -u16 -r16 -i data/rxa6982-long.raw

gentset:
	python scripts/gentset.py $(PLDATALOC)

run: run_pluto

run_pluto:
	python adsb_read.py -v --osr 4 -t $(PLDATALOC)/pluto-PLsplace/x1

run_uhd:
	# uhd dies after a few hours (maybe because machine is too slow), run in infinite loop
	./doloop ./adsb_read-uhd.py -v --osr 4 -t $(J03DATALOC)/adsb-data/b210-j03/a1

run_rx_sdr:
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 -g 40.2 - |python adsb_read.py -i - -o x

run_rtl_sdr:
	rtl_sdr -f 1090000000 -s 2000000 -g 0 -|python adsb_read.py - -o x

clean:
	-rm -f *.iq *-iqindex.txt
