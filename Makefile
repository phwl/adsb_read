#PLDATALOC=	/srv/breamdisk/adsb-data
PLDATALOC= ~/CruxML/Projects/raw_data
J03DATALOC=	.
#datadir= pluto-PLsplace/x1
topdir= $(PLDATALOC)/pluto-BFsplace
datadir= $(topdir)/20210917/x1

$(eval now_date="$(shell date +%Y%m%d)")
now_datadir=  $(topdir)/$(now_date)/x1
run_log= $(topdir)/adsb_read_$(now_date).log
p= python3

t1:
	@printf "date: $(now_date)\n"
	@printf "topdir: $(topdir)\n"
	@printf "now_datadir: $(now_datadir)\n"
	@printf "run_log: $(run_log)\n"

status:
	@pgrep -a python3

test:
	$(p) adsb_read.py -v -i data/rxa6982-long.raw
	$(p) adsb_read.py -u16 -r16 -i data/rxa6982-long.raw

gentset:
#	$(p) scripts/gentset.py $(PLDATALOC)
	@cd scripts; make now; cd ..
	
run: run_pluto

now: run_pluto_now

run_pluto:
	$(p) adsb_read.py -v --osr 4 -t $(datadir)

run_pluto_now:
	nohup $(p) adsb_read.py -v --osr 4 -t $(now_datadir) > $(run_log) 2>&1 &

run_pluto_v:
	$(p) adsb_read.py -vv --osr 4 -t $(datadir)

run_uhd:
	# uhd dies after a few hours (maybe because machine is too slow), run in infinite loop
	./doloop ./adsb_read-uhd.py -v --osr 4 -t $(J03DATALOC)/adsb-data/b210-j03/a1

run_rx_sdr:
	../rx_tools/rx_sdr -d rtlsdr -f 1090000000 -s 2000000 -g 40.2 - |$(p) adsb_read.py -i - -o x

run_rtl_sdr:
	rtl_sdr -f 1090000000 -s 2000000 -g 0 -|$(p) adsb_read.py - -o x

clean:
	-rm -f *.iq *-iqindex.txt
