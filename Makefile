#DATALOC=	/srv/breamdisk/adsb-data
ifeq ($(strip $(CRUXSEI_PROJECT_ADSBDATA_ROOTDIR)),)
	DATALOC= ~/Projects/CruxSEI/adsb-data
else
	DATALOC= $(CRUXSEI_PROJECT_ADSBDATA_ROOTDIR)
endif
#DATALOC= ~phwl/data/adsb_data
J03DATALOC=	.

ifeq ($(shell hostname), mako)
	topdir= $(DATALOC)/pluto2-BF1
else
	topdir= $(DATALOC)/pluto1-PL1
endif

datadir= $(topdir)/20210917/x1

$(eval now_date="$(shell date +%Y%m%d)")
now_datadir=  $(topdir)/$(now_date)/x1
run_log= $(topdir)/adsb_read_$(now_date).log
$(eval user=$(shell whoami))

$(eval most_recent_data_dir=$(shell ls -d $(topdir)/*/ | tail -1))

p= python3

t1:
	@printf "DATALOC: $(DATALOC)\n"
	@printf "date: $(now_date)\n"
	@printf "topdir: $(topdir)\n"
	@printf "now_datadir: $(now_datadir)\n"
	@printf "run_log: $(run_log)\n"

status:
	@printf "PID of running adsb_read.py process: "
	@pgrep -a python3 | grep adsb_read | sed "s/ python3.*$$//"
	@if [ -d $(topdir)/$(now_date) ]; then \
		printf "Files in current capture $(topdir)/$(now_date) = "; \
		ls $(topdir)/$(now_date) | wc -w; \
	else \
		printf "Files in most recent capture $(most_recent_data_dir) = "; \
		ls $(most_recent_data_dir) | wc -w; \
	fi \
	
test:
	$(p) adsb_read.py -v -i data/rxa6982-long.raw
	$(p) adsb_read.py -u16 -r16 -i data/rxa6982-long.raw

gentset:
#	$(p) scripts/gentset.py $(DATALOC)
	@cd scripts; make now; cd ..

gentset_all:
#	$(p) scripts/gentset.py $(DATALOC)
	@cd scripts; make now_all; cd ..
	
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

xfer_data_to_amberjack:
	printf "Please remember to establish VPN to Amberjack using:\n\n> sudo openconnect -b -u <unikey> --passwd-on-stdin --protocol anyconnect vpn.sydney.edu.au\n\n<type your password here there is no prompt>\n\n"	
	scp -r $(topdir) $(user)@amberjack.staff.sydney.edu.au:/home/cruxml/Projects/CruxSEI/adsb-data	

rsync_data_to_amberjack:
	printf "Please remember to establish VPN to Amberjack using:\n\n> sudo openconnect -b -u <unikey> --passwd-on-stdin --protocol anyconnect vpn.sydney.edu.au\n\n<type your password here there is no prompt>\n\n"	
	rsync -av $(topdir) $(user)@amberjack.staff.sydney.edu.au:/home/cruxml/Projects/CruxSEI/adsb-data