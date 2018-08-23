SHELL := /bin/bash

test:
	python ../create_tar2bids_test_data.py Khan_DiffModelling_7T_20180402_2018_04_02_DiffModel_1.059E696B.tar ~/test -p 1800_01_01_subject_01 -s 'PI^project'

test_3:
	python ../create_tar2bids_test_data.py Khan_DiffModelling_7T_20180402_2018_04_02_DiffModel_1.059E696B.tar ~/test -p 1800_01_01_subject_01 -s 'PI^project'
	python ../create_tar2bids_test_data.py Khan_NeuroAnalytics_20180615_2018_06_15_snSx_P029_2.06BD71CB.tar ~/test -p 1800_01_01_subject_02 -s 'PI^project'
	python ../create_tar2bids_test_data.py Kohler_PS_PRC_20171019_2017_10_19_MO11_1.541FBBA2.tar ~/test -p 1800_01_01_subject_03 -s 'PI^project'

test_autobids:
    #note: tar filename might change: due to anonymize new studyUID, and dicom2tar's hash
	singularity run -B /mnt:/mnt -B /home:/home -B /tmp:/tmp ~/singularities//khanlab-tar2bids-master-0.0.2d.simg -h cfmm_base.py ~/test/PI_project_18000101_1800_01_01_subject_01_1.C38406CB.tar

	#should see:
	#This dataset appears to be BIDS compatible.
	#