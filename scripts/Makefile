
rootdir=$(HOME)/Projects/CruxSEI

p3=python3
otype=h5
raw_data_src_dir=~phwl/data/adsb-data
data_src_dir=$(rootdir)/raw_data
data_dst_dir=$(rootdir)/data/
data_dst_file=tdata_20210726.$(otype)
data_dst_file_trunc=tdata_trunc.$(otype)
date_str=20210809

run:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000

run_save_by_dir:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)tdata_$(date_str) --save_by_dir --otype $(otype)

run_save_by_dir_preproc:
	$(p3) ./gentset.py -d $(raw_data_src_dir) --write --oname $(data_dst_dir)tdata_$(date_str) --save_by_dir --preproc --class_sample_thresh 40 --otype $(otype)

run_preproc_agg:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)tdata_agg_$(date_str).$(otype) --preproc --agg --class_sample_thresh 40
