test_short:
	python iqreader.py -i data/rxa6982-short.raw
	python iqreader.py -u16 -r16 -i data/rxa6982-short.raw

test: test_short test_long

run:
	rtl_sdr -f 1090000000 -s 2000000 -g 0 -|python iqreader.py - -o x

run_rx_sdr:
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 -g 40.2 - |python iqreader.py -i - -o x

test_long:
	python iqreader.py -i data/rxa6982-long.raw

run_dump1090:
	# ../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 40.2 |~/bin/dump1090 --ifile - --interactive --metric --aggressive --net
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - |~/bin/dump1090 --ifile - --metric --aggressive --net

clean:
	-rm -f *.iq *-iqindex.txt
