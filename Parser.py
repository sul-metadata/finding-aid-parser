from FindingAidParser import * 
from MODSParser import *
from MARCParser import *
import base64

import os
import xml.etree.ElementTree as ET

from random import randint

import copy
import re
import pandas as pd

"""
Wrapper class for FindingAidParser, ModsParser, and any other type of parser
"""
class Parser: 
    def __init__(self, show_progress=True): 
        self.finding_aid_parser = FindingAidParser()
        self.mods_parser = MODSParser()
        self.marc_parser = MARCParser()
        self.show_progress = show_progress
    
    def __get_namespace(self, root):
        m = re.match(r'\{.*\}', root.tag)
        return m.group(0) if m else ''

    def parse(self, files: list): 
        finding_aids = []        
        mods = []
        marcs = []

        for file in files: 
            xmlTree = ET.parse(copy.deepcopy(file))
            
            root = xmlTree.getroot()
            namespace = self.__get_namespace(root) 

            if namespace == self.finding_aid_parser.namespace: 
                finding_aids.append(file)
            elif namespace == self.mods_parser.namespace: 
                mods.append(file)
            elif namespace == self.marc_parser.namespace: 
                marcs.append(file)
    
        finding_aid_res = []
        mods_res = []
        marcs_res = []

        res = []
        size = len(finding_aids) + len(marcs) + len(mods)
        amount_done=0
        progress_bar = None
        if self.show_progress: progress_bar = st.progress(0)

        if finding_aids: 
            finding_aid_res = self.finding_aid_parser.batch_parse_xml(
                finding_aids, 
                progress_bar=progress_bar,
                amount_done=amount_done,
                size=size
            )
            res.append(
                ('Finding aids', finding_aid_res)
            )
            amount_done += round(len(finding_aids)/size, 3)

        if marcs: 
            marcs_res = self.marc_parser.batch_parse_xml(
                marcs,
                progress_bar=progress_bar,
                amount_done=amount_done,
                size=size)
            res.append(
                ('MARCS', marcs_res)
            )
            amount_done += round(len(marcs)/size, 3)

        if mods: 
            mods_res = self.mods_parser.batch_parse_xml(
                mods,
                progress_bar=progress_bar,
                amount_done=amount_done,
                size=size
            )
            res.append(
                ('MODS', mods_res)
            )
            amount_done += round(len(mods)/size, 3)
        

        for r in res: 
            df = pd.DataFrame(r[1])
            st.markdown(self.get_table_download_link(df, r[0]+'.csv', r[0]), unsafe_allow_html=True)

    
    def get_table_download_link(self, df, filename, xml_type):
        """Generates a link allowing the data in a given panda dataframe to be downloaded
        in:  dataframe
        out: href string
        """
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
        # href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {xml_type} csv files</a>'
        # f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'
        return href
