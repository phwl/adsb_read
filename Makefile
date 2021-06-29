test_short:
	python iqreader.py rxa6982-short.raw
	python iqreader.py -u16 -r16 rxa6982-short.raw

test: test_short test_long

run:
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - |python iqreader.py - -o x

test_long:
	python iqreader.py rxa6982-long.raw

run_dump1090:
	# ../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |~/bin/dump1090 --ifile - --interactive --metric --aggressive --net
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - |~/bin/dump1090 --ifile - --metric --aggressive --net

clean:
	-rm -f *.iq *-iqindex.txt
