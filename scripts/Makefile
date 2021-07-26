
rootdir=$(HOME)/Projects/CruxSEI

p3=python3
data_src_dir=~phwl/data/adsb-data
data_dst_dir=$(rootdir)/data/
data_dst_file=tdata_20210726.bin
data_dst_file_trunc=tdata_trunc.bin
date_str=20210726

run:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000

run_save_by_dir:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)tdata_$(date_str) --save_by_dir
