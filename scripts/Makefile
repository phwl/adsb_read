
rootdir=$(HOME)/CruxML/Projects

p3=python3
otype=h5
raw_data_src_dir=~phwl/data/adsb-data
all_data_src_dir=$(rootdir)/raw_data/pluto-BFsplace
date_str=20210917
data_src_dir=$(all_data_src_dir)/$(date_str)
data_dst_dir=$(rootdir)/data/
data_dst_file=tdata_$(date_str).$(otype)
data_dst_file_trunc=tdata_trunc.$(otype)

run: run_preproc_agg

run_orig:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000

run_save_by_dir:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata --save_by_dir --otype $(otype)

run_save_by_dir_preproc:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata --save_by_dir --preproc --class_sample_thresh 40 --otype $(otype) --logfile gentset.log

run_preproc_agg:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata_agg_$(date_str).$(otype) --preproc --agg --class_sample_thresh 40 --logfile gentset_agg.log

test: run_preproc_agg run_save_by_dir_preproc