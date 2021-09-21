rootdir=$(HOME)/Projects/CruxSEI
#rootdir=~pwhl/data/adsb_data

p3=python3
otype=h5
#all_data_src_dir=$(rootdir)/pluto1-PL*
all_data_src_dir=$(rootdir)/raw_data/pluto2-BF*
date_str=20210917
data_src_dir=$(all_data_src_dir)/$(date_str)
data_dst_dir=$(rootdir)/data/
data_dst_file=tdata_$(date_str).$(otype)
data_dst_file_trunc=tdata_trunc.$(otype)

topN=40

$(eval now_date=$(shell date +%Y%m%d))

t1:
	@printf "$(now_date)\n"
	
run: run_preproc_agg

now: run_preproc_agg_now

now_all: run_preproc_agg_now_all

run_orig:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000

run_save_by_dir:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata --save_by_dir --otype $(otype)

run_save_by_dir_preproc:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata_top$(topN)_ --save_by_dir --preproc --class_sample_thresh $(topN) --otype $(otype) --logfile gentset.log

run_preproc_agg:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata_agg_top$(topN)_$(date_str).$(otype) --preproc --agg --class_sample_thresh $(topN) --logfile gentset_agg.log

run_preproc_agg_now:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata_agg_top$(topN)_$(now_date).$(otype) --preproc --agg --class_sample_thresh $(topN) --logfile gentset_agg.log

run_preproc_agg_now_all:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)tdata_agg_all_$(now_date).$(otype) --preproc --agg --logfile gentset_agg.log

test: run_preproc_agg run_save_by_dir_preproc