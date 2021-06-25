run:
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |python iqreader.py -

run_dump1090:
	# ../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |~/bin/dump1090 --ifile - --interactive --metric --aggressive --net
	../sdr/rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 - -g 100 |~/bin/dump1090 --ifile - --metric --aggressive --net

test_short:
	python iqreader.py -w rxa6982-short.iq

test_long:
	python iqreader.py rxa6982-long.iq

clean:
	-rm -f iqframe-*.iq
