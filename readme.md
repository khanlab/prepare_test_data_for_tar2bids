setup:  
```bash
pip install -r requirements.txt  
```

usage:  
```bash
usage: create_tar2bids_test_data.py [-h] [-p ] [-s [STUDY_DESCRIPTION]]
                                    tar_file output_dir

positional arguments:
  tar_file              tar file
  output_dir            save anonymized dicom files to

optional arguments:
  -h, --help            show this help message and exit
  -p [], --patient_name []
                        anonymize dicom PatientName tag to this, note: 
                        according to CFMM rule and tar2bids parsing, 
                        use date_sub patten: 1800_01_01_sub_01
  -s [STUDY_DESCRIPTION], --study_description [STUDY_DESCRIPTION]
                        anonymize dicom StudyDescription tag to this, note:
                        according to CFMM rule, use ^ to separate PI^project
```

example:  
```bash
python create_tar2bids_test_data.py test.tar ~/test -p 1800_01_01_subject_01 -s 'PI^project'
```