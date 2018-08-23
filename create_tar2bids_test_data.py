#!/usr/bin/env python
"""
create test data for tar2bids, steps:

    input a tar file
    keep the first 10 images(by InstanceNumber) from each series
    anonymize dicom files by given PatientName and StudyDescription
    output a new tar(by run dicom2tar)

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-08-22

note:
    Tested on ubuntu 18.04, python 2.7.14

"""
import os
import sys
import subprocess
import logging
import tarfile
import tempfile
import argparse
import shutil

import pydicom


def _get_stdout_stderr_returncode(cmd):
    """
    Execute the external command and get its stdout, stderr and return code
    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    return_code = proc.returncode

    return out, err, return_code


class CreateTestData:
    """
    create tar2bids test data:
    1. extract tar file to /tmp
    2. keep only the first n images for each series(i.e., remove others)
    3. dicom anonymization
    4. dicom2tar:create a new tar file based on the anonymized tags.
    """

    def __init__(self, tar_fullfilename, output_dir, PatientName, StudyDesctiption, keep_first_n_images_each_series=10, result_tar_prefix="test-"):
        self.logger = logging.getLogger(__name__)
        self.tar_fullfilename = tar_fullfilename
        self.output_dir = output_dir
        self.PatientName = PatientName
        self.StudyDescription = StudyDesctiption
        self.keep_first_n_images_each_series = keep_first_n_images_each_series
        self.result_tar_prefix = result_tar_prefix

        # extract tar to this folder
        self._extract_to_dir = os.path.join(
            tempfile.gettempdir(), 'CreateTestData_extract')

        # anonymize dicom files to this folder
        self._anonymize_to_dir = os.path.join(
            tempfile.gettempdir(), 'CreateTestData_anonymize')

        self.StudyInstanceUID_dict = {}
        self.SeriesInstanceUID_dict = {}

    def run(self):
        self._extract_tar(self.tar_fullfilename, self._extract_to_dir)
        self._keep_first_n_images_each_series(
            self.keep_first_n_images_each_series, self._extract_to_dir)
        self._walk_anonymize(self._extract_to_dir, self._anonymize_to_dir,
                             self.PatientName, self.StudyDescription)
        self._dicom2tar(self._anonymize_to_dir, self.output_dir)

    def _dicom2tar(self, anonymize_to_dir, output_dir):
        print('dicom2tar dir:{}'.format(anonymize_to_dir))
        cmd = "dicom2tar {} {}".format(anonymize_to_dir, output_dir)
        out, err, return_code = _get_stdout_stderr_returncode(cmd)
        print(out)

    def _extract_tar(self, tar_fullfilename, dest_dir):
        c_file = tarfile.open(tar_fullfilename, "r:")
        print('extracting {} to {}'.format(tar_fullfilename, dest_dir))
        c_file.extractall(dest_dir)
        c_file.close()

    def _keep_first_n_images_each_series(self, n, dicom_dir):
        """
        keep the first 10 images(by InstanceNumber) from each series, output a new tar file named test-tar_file

        Q:why use the 'first' 10 images of each series?
        A:dcmstack error: The DICOM stack is not valid: Slice spacings are not consistent )
        """
        # extract tar to system's temp directory
        print('picking the first {} images from each series in {}'.format(n, dicom_dir))
        # keep only n images for each series
        for root_dir, sub_dirs, filenames in os.walk(dicom_dir):
            if len(filenames) > n:
                # sort by InstanceNumber(due to the dcmstack error: The DICOM stack is not valid: Slice spacings are not consistent )
                fullfilenames_instancenumbers_list = []
                for filename in filenames:
                    fullfilename = os.path.join(root_dir, filename)
                    ds = pydicom.dcmread(fullfilename, stop_before_pixels=True)

                    fullfilenames_instancenumbers_list.append(
                        [fullfilename, int(ds.InstanceNumber)])

                # sort by instance number
                sorted_list = sorted(
                    fullfilenames_instancenumbers_list, key=lambda x: x[1])

                # keep only the first EASH_SERIES_FILES_NUMBER
                for fullfilename, instancenumber in sorted_list[n:]:
                    os.remove(fullfilename)

        # # remove temp directory
        # shutil.rmtree(extract_to_dir)

    def _walk_anonymize(self, root_dicom_dir, root_output_dir, PatientName, StudyDescription):
        print('anonymizding dir:{} to {}'.format(
            root_dicom_dir, root_output_dir))
        for root_dir, dirs, filenames in os.walk(root_dicom_dir):
            for filename in filenames:
                full_filename = os.path.join(root_dir, filename)
                try:

                    # file-specific output dir
                    output_dir = os.path.dirname(full_filename.replace(
                        root_dicom_dir, root_output_dir))
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    # anonymize and write new dicom file
                    self._anonymize(full_filename, output_dir,
                                    PatientName, StudyDescription)
                except Exception as e:
                    self.logger.error(e)

    def _anonymize(self, dicom_file, output_dir, PatientName='anon', StudyDescription="anon", string_anon='anon', date_anon="18000101", StudyID='1', rename=False):
        """
        why: default: StudyID='1'
        A: CFMM rule: StudyID is a number. Ali's tar2bids parsing follow this rule. 
        """

        #ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
        ds = pydicom.dcmread(dicom_file)

        # modify StudyInstanceUID
        if 'StudyInstanceUID' in ds:
            if ds.StudyInstanceUID in self.StudyInstanceUID_dict:
                ds.StudyInstanceUID = self.StudyInstanceUID_dict[ds.StudyInstanceUID]
            else:
                self.StudyInstanceUID_dict[ds.StudyInstanceUID] = pydicom.uid.generate_uid(
                )
                ds.StudyInstanceUID = self.StudyInstanceUID_dict[ds.StudyInstanceUID]

        # modify SeriesInstanceUID
        if 'SeriesInstanceUID' in ds:
            if ds.SeriesInstanceUID in self.SeriesInstanceUID_dict:
                ds.SeriesInstanceUID = self.SeriesInstanceUID_dict[ds.SeriesInstanceUID]
            else:
                self.SeriesInstanceUID_dict[ds.SeriesInstanceUID] = pydicom.uid.generate_uid(
                )
                ds.SeriesInstanceUID = self.SeriesInstanceUID_dict[ds.SeriesInstanceUID]

        # Patient's Name (0010,0010)
        if 'PatientName' in ds:
            ds.PatientName = PatientName

        # # Patient ID (0010,0020)
        if 'PatientID' in ds:
            ds.PatientID = string_anon

        # Patient's Birth Date (0010,0030)
        if 'StudyDate' in ds:
            ds.StudyDate = date_anon

        if 'SeriesDate' in ds:
            ds.SeriesDate = date_anon
        if 'AcquisitionDate' in ds:
            ds.AcquisitionDate = date_anon
        if 'ContentDate' in ds:
            ds.ContentDate = date_anon

        # Patient's Birth Date (0010,0030)
        if 'PatientBirthDate' in ds:
            ds.PatientBirthDate = date_anon

        # Patient's Sex (0010,0040)
        if 'PatientSex' in ds:
            ds.PatientSex = string_anon

        # Patient's Birth Time (0010,0032)
        if 'PatientBirthTime' in ds:
            ds.PatientBirthTime = string_anon

        # Other Patient IDs (0010,1000)
        if 'OtherPatientIDs' in ds:
            ds.OtherPatientIDs = string_anon

        # Other Patient Names (0010,1001)
        if 'OtherPatientNames' in ds:
            ds.OtherPatientNames = string_anon

        # Ethnic Group (0010,2160)
        if 'EthnicGroup' in ds:
            ds.EthnicGroup = string_anon

        # Patient Comments (0010,4000)
        if 'PatientComments' in ds:
            ds.PatientComments = string_anon

        # Referring Physician's Name (0008,0090)
        if 'ReferringPhysicianName' in ds:
            ds.ReferringPhysicianName = string_anon

        # Study ID (0020,0010)
        if 'StudyID' in ds:
            ds.StudyID = StudyID

        # Accession Number (0008,0050)
        if 'AccessionNumber' in ds:
            ds.AccessionNumber = string_anon

        # cfmm's sort_rule.py need this tag
        # Study Description (0008,1030)
        if 'StudyDescription' in ds:
            ds.StudyDescription = StudyDescription

        # Physician(s) of Record (0008,1048)
        if 'PhysiciansOfRecord' in ds:
            ds.	PhysiciansOfRecord = string_anon

        # Name of Physician(s) Reading Study (0008,1060)
        if 'NameOfPhysiciansReadingStudy' in ds:
            ds.NameOfPhysiciansReadingStudy = string_anon

        # Admitting Diagnoses Description (0008,1080)
        if 'AdmittingDiagnosesDescription' in ds:
            ds.AdmittingDiagnosesDescription = string_anon

        # if set PatientAge to '0', get error:
        # bids-validator:
        # 1: Empty cell in TSV file detected: The proper way of labeling missing values is "n/a". (code: 23 - TSV_EMPTY_CELL)

        # As per section 164.514(C) of "The De-identification Standard" under HIPAA guidelines,
        # participants with age 89 or higher should be tagged as 89+.
        # More information can be found at https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/#standard (code: 56 - Participants age 89 or higher)
        # Patient's Age (0010,1010)
        if 'PatientAge' in ds:
            ds.PatientAge = '88'

        # Patient's Size (0010,1020)
        if 'PatientSize' in ds:
            ds.PatientSize = '88'

        # Patient's Weight (0010,1030)
        if 'PatientWeight' in ds:
            ds.PatientWeight = '88'

        # Occupation (0010,2180)
        if 'Occupation' in ds:
            ds.Occupation = string_anon

        # Additional Patient's History (0010,21B0)
        if 'AdditionalPatientHistory' in ds:
            ds.AdditionalPatientHistory = string_anon

        # Performing Physicians'Name (0008,1050)
        if 'PerformingPhysicianName' in ds:
            ds.PerformingPhysicianName = string_anon

        # # keep it for heudiconv
        # # Protocol Name(0018, 1030)
        # if 'ProtocolName' in ds:
        #     ds.ProtocolName = string_anon

        # # keep it for heudiconv
        # # Series Description (0008,103E)
        # if 'SeriesDescription' in ds:
        #     ds.SeriesDescription = string_anon

        # Operators' Name (0008,1070)
        if 'OperatorsName' in ds:
            ds.OperatorsName = string_anon

        # Institution Name (0008,0080)
        if 'InstitutionName' in ds:
            ds.InstitutionName = string_anon

        # Institution Address (0008,0081)
        if 'InstitutionAddress' in ds:
            ds.InstitutionAddress = string_anon

        # Station Name (0008,1010)
        if 'StationName' in ds:
            ds.StationName = string_anon

        # Institutional Department Name (0008,1040)
        if 'InstitutionalDepartmentName' in ds:
            ds.InstitutionalDepartmentName = string_anon

        # Device Serial Number (0018,1000)
        if 'DeviceSerialNumber' in ds:
            ds.DeviceSerialNumber = string_anon

        # Derivation Description (0008,2111)
        if 'DerivationDescription' in ds:
            ds.DerivationDescription = string_anon

        # Image Comments (0020,4000)
        if 'ImageComments' in ds:
            ds.ImageComments = string_anon

        if (rename and 'InstanceNumber' in ds):
            new_dicom_file = str(ds.InstanceNumber).zfill(4)+'.dcm'
        else:
            new_dicom_file = os.path.basename(dicom_file)

        ds.save_as(os.path.join(output_dir, new_dicom_file))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if os.path.exists(self._extract_to_dir):
            shutil.rmtree(self._extract_to_dir)

        if os.path.exists(self._anonymize_to_dir):
            shutil.rmtree(self._anonymize_to_dir)


if __name__ == "__main__":

    # argument
    parser = argparse.ArgumentParser()
    parser.add_argument('tar_file', help='tar file')
    parser.add_argument('output_dir', help='save anonymized dicom files to')
    parser.add_argument("-p", "--patient_name", metavar='', nargs='?',
                        default='anon', help="anonymize dicom PatientName tag to this, note: according to CFMM rule and Ali's tar2bids parsing, use date_sub patten: 1800_01_01_sub_01")
    parser.add_argument("-s", "--study_description",
                        nargs='?', default='PI^project', help="anonymize dicom StudyDescription tag to this, note: according to CFMM rule, use ^ to separate PI^project")
    args = parser.parse_args()

    # check
    if not (os.path.exists(args.tar_file) and os.path.isfile(args.tar_file)):
        print("{} not exist".format(args.tar_file))
        sys.exit(1)

    if not os.path.exists(args.output_dir):
        os.makedirs(output_dir)

    if '^' not in args.study_description:
        print("--study_description must contain ^, for instance: PI^project")
        sys.exit(1)

    # run
    with CreateTestData(args.tar_file, args.output_dir, args.patient_name, args.study_description) as create_test_data:
        create_test_data.run()
