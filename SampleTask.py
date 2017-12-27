#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 00:11:09 EST 2017

@author: Aman
"""
"""
PROBLEM PROMPT

Here is the link to the dataset: https://www.dropbox.com/s/2uc3allkr58zkzh/test_data_2009.zip?dl=0

The data are some patent applications from 2009. Once you unpack it, you'll see that each patent application is in a 
separate folder, and that the full sets of documents are in zip archives in each folder; the description of the documents 
is in the TSV file. You only need the PDF files that are already extracted from the zips (if there were any). But the zips 
are there for your reference.

Task 2 (Better performed with python, but can be R, too; use MySQL for data management or just a flat CSV file)

Research question: is examiner name part of the scanned document?

Extract all available text from search notes (files ending with “SRFW”) using free API of ocr.space website 
(https://ocr.space/ocrapi). Put extracted strings into an organized table that includes fields for application 
number and document number (include strings from different lines of the same document as separate records).

Look up the examiner name using application number and USPTO API (https://ped.uspto.gov/peds/#/apiDocumentation). 
Find the name in the extracted text.

Note: All file management (i.e. finding the PDFs in folders etc.) should be done programmatically, without changing 
the directory structure (i.e., do not move files around except for sending them to the API; but keep the results 
files or tables however you want).

Also, if you want to extract additional files from zips, it is better if your script does not unpack entire zips, 
but just extracts the file you need.
"""

import requests
from pprint import pprint
import os, fnmatch
from fuzzywuzzy import fuzz

import logging
logger = logging.getLogger("SampleTask")
logger.setLevel(logging.INFO)
logger.disabled = True    # Toggle to enable/disable logging
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

OCR_API_KEY = "f9ef23655e88957"
BASE_DIR = "/Users/aman/Documents/Programming/RGRA/"

def ocr_file(filename, api_key=OCR_API_KEY, language='eng', overlay=False,):
    """
    Args:
        filename (str): filename of the file you want to parse.
        api_key (str): OCR API key.
        language (str): language the text of file is in.
    Returns:
        JSON of response from OCR API.
    """
    try:
        payload = {
            'isOverlayRequired': overlay,
            'apikey': api_key,
            'language': language,
        }

        with open(filename, 'rb') as f:
            r = requests.post(
                'https://api.ocr.space/parse/image',
                files={filename: f},
                data=payload,
            )
        return r.json()
    except Exception as e:
        #logger.error("Something went wrong in ocr_file: " + e)
        return "NA"

def get_examiner_ocr(filename):
    """
    Args:
        filename (str): filename of the file you want to parse.
    Returns:
        examiner name in the file.
    """
    try:
        ocrData = ocr_file(filename)
        parsedResults = ocrData.get('ParsedResults', '')
        if parsedResults:
            parsedText = parsedResults[0].get('ParsedText', '')
            if parsedText:
                parsedTextList= [text.strip() for text in parsedText.split("\r\n")]
                logger.debug(parsedTextList)
                examinerIndex = parsedTextList.index("Examiner") + 1
                examiner = parsedTextList[examinerIndex]
                return examiner
    except Exception as e:
        #logger.error("Something went wrong in get_examiner_ocr: " + e)
        return "NA"

def get_examiner_uspto(application_no):
    """
    Args:
        application_no (str): application no of patent.
    Returns:
        examiner name in the USPTO API.
    """
    try:
        payload = {
            "searchText": "applId:" + application_no,
            "df": "patentTitle"
        }

        r = requests.post(
            'http://ped.uspto.gov/api/queries',
            json=payload)
        responseJson = r.json()
        #responseJson.get('queryResults', '').get('searchResponse', '').get('response', '').get('docs', '')[0].get('appExamName', '')
        examiner = responseJson['queryResults']['searchResponse']['response']['docs'][0]['appExamName']

        if examiner:
            return examiner
        else:
            return "NA"

    except Exception as e:
        #logger.error("Something went wrong in get_examiner_uspto: " + e)
        return "NA"

def file_parser(root_dir):
    """
    Args:
        root_dir (str): Root directory of the file structure.
    Returns:
        result string of all the parsed files in the root directory.
    """
    try:
        resultString = ""
        for root, subdirs, files in os.walk(root_dir):
            application_no = os.path.relpath(root, root_dir)
            resultString = resultString + ("Parsed application: " + application_no + "\n\n")
            for f in files:
                if fnmatch.fnmatch(f, '*SRFW*'):
                    ocrExaminer = get_examiner_ocr(root + "/"+ f)
                    usptoExaminer = get_examiner_uspto(application_no)
                    matchRatio = fuzz.ratio(ocrExaminer, usptoExaminer)
                    resultString = resultString + ("Parsed file: " + f + "\n" +
                          "Examiner name from OCR API: " + ocrExaminer + "\n" +
                          "Examiner name from USPTO API: " + usptoExaminer + "\n" +
                          "Fuzzy match ratio: " + str(matchRatio) + "\n\n")
        return resultString

    except Exception as e:
        #logger.error("Something went wrong in file_parser: " + e)
        return "NA"

if __name__ == "__main__":
    output = file_parser(BASE_DIR + "test_data_2009/")
    print (output)