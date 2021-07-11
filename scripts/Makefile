
rootdir=$(HOME)/Projects/CruxSEI

p3=python3
data_src_dir=~phwl/data/adsb-data
data_dst_dir=$(rootdir)/data/
data_dst_file=tdata.bin
data_dst_file_trunc=tdata_trunc.bin

run:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000
