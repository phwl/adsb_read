test: test_short

run:
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |python iqreader.py -

test_long:
	python iqreader.py rxa6982-long.raw

test_short:
	python iqreader.py rxa6982-short.raw

run_dump1090:
	# ../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |~/bin/dump1090 --ifile - --interactive --metric --aggressive --net
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |~/bin/dump1090 --ifile - --metric --aggressive --net

clean:
	-rm -f *.iq *-iqindex.txt
