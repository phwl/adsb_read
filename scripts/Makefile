#src_rootdir=$(HOME)/Projects/CruxSEI
ifeq ($(strip $(CRUXSEI_PROJECT_ADSBDATA_ROOTDIR)),)
	src_rootdir= ~/Projects/CruxSEI/adsb-data
else
	src_rootdir= $(CRUXSEI_PROJECT_ADSBDATA_ROOTDIR)
endif

ifeq ($(strip $(CRUXSEI_PROJECT_ADSBDATA_ROOTDIR)),)
	rootdir=$(HOME)/Projects/CruxSEI
else
	rootdir= $(CRUXSEI_PROJECT)
endif

ifeq ($(strip $(CRUXSEI_PROJECT_DATA_ROOTDIR)),)
	data_dst_dir=$(rootdir)/data
else
	data_dst_dir= $(CRUXSEI_PROJECT_DATA_ROOTDIR)
endif

P1PL1=~phwl/data/adsb-data/pluto1-PL1
P1PL2=~phwl/data/adsb-data/pluto1-PL2
P2BF1=$(src_rootdir)/pluto2-BF1

p3=python3
otype=h5
ifeq ($(shell hostname), mako)
	all_data_src_dir=$(src_rootdir)/pluto2-BF*
else
	all_data_src_dir=$(src_rootdir)/pluto1-PL*
endif
date_str=20210917
data_src_dir=$(all_data_src_dir)/$(date_str)
data_dst_file=tdata_$(date_str).$(otype)
data_dst_file_trunc=tdata_trunc.$(otype)

topN=40

$(eval now_date=$(shell date +%Y%m%d))

t1:
	@printf "hostname: $(shell hostname)\n"
	@printf "all_data_src_dir: $(all_data_src_dir)\n"
	@printf "date: $(now_date)\n"
	
run: run_preproc_agg

now: run_preproc_agg_now

now_all: run_preproc_agg_now_all

run_orig:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file)

run_trunc:
	$(p3) ./gentset.py -d $(data_src_dir) --write --oname $(data_dst_dir)/$(data_dst_file_trunc) --trunc 1000

run_save_by_dir:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)/tdata --save_by_dir --otype $(otype)

run_save_by_dir_preproc:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)/tdata_top$(topN)_ --save_by_dir --preproc --class_sample_thresh $(topN) --otype $(otype) --logfile gentset.log

run_preproc_agg:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)/tdata_agg_top$(topN)_$(date_str).$(otype) --preproc --agg --class_sample_thresh $(topN) --logfile gentset_agg.log

run_preproc_agg_now:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)/tdata_agg_top$(topN)_$(now_date).$(otype) --preproc --agg --class_sample_thresh $(topN) --logfile gentset_agg.log

run_preproc_agg_now_all:
	$(p3) ./gentset.py -d $(all_data_src_dir) --write --oname $(data_dst_dir)/tdata_agg_all_$(now_date).$(otype) --preproc --agg --logfile gentset_agg.log

test: run_preproc_agg run_save_by_dir_preproc

P1PL1_gen:
	$(p3) ./gentset.py -d $(P1PL1) --write --oname $(data_dst_dir)/P1PL1.$(otype) --preproc --agg --logfile gentset_P1PL1.log

P1PL2_gen:
	$(p3) ./gentset.py -d $(P1PL2) --write --oname $(data_dst_dir)/P1PL2.$(otype) --preproc --agg --logfile gentset_P1PL2.log

P2BF1_gen:
	$(p3) ./gentset.py -d $(P2BF1) --write --oname $(data_dst_dir)/P2BF1.$(otype) --preproc --agg --logfile gentset_P2BF1.log
