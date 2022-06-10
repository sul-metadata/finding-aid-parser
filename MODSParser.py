import xml.etree.ElementTree as ET
import datetime
import re
import csv
import glob
import math
import os
from collections import defaultdict
import spacy_streamlit
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
import string
import streamlit as st


class MODSParser: 
    def __init__(self): 
        self.namespace = "{http://www.loc.gov/mods/v3}"
        self.wikidata_xml_mapping = {}

    def get_title(self, root): 
        title = []
        tag_in_xml = root.findall(self.namespace + 'titleInfo')[0]

        for t in tag_in_xml: 
            for node in t.iter(): 
                title.append(node.text)
        return ' '.join(title)

    def get_subtitle(self, root): 
        subtitle = ''
        tag_in_xml = root.findall(self.namespace + 'titleInfo')[0]
        subtitle_tag_in_xml = tag_in_xml.findall(self.namespace + 'subTitle')
        
        for t in subtitle_tag_in_xml: 
            for node in t.iter():
                subtitle = node.text           
        return subtitle

    def get_uniform_title(self, root): 
        uniform_title = ''
        tag_in_xml = root.findall(self.namespace + 'titleInfo[@type="uniform"]')
        
        for t in tag_in_xml: 
            for node in t.iter(): 
                uniform_title = node.text
        return uniform_title

    def get_composer(self, root): 
        composer_info = []
        tag_in_xml = root.findall(self.namespace + 'name[@usage="primary"]')
        
        if len(tag_in_xml) == 0: 
            return ''
        
        for t in tag_in_xml[0]: 
            for node in t.iter(): 
                composer_info.append(node.text)
                
        composer = composer_info[0].split(', ')
        composer.reverse()
        composer = ' '.join(composer)
        return composer

    def get_role(self, root, role_of_interest): 
        arranger_info = []    
        parent_node = None
        res = ''
        names = root.findall(self.namespace + 'name')

        for name in names: 
            roles = name.findall(self.namespace + 'role')
            for role in roles: 
                for r in role.iter(): 
                    if r.text.lower() == role_of_interest.lower(): 
                        parent_node = name
                        break
        
        if parent_node: 
            name_of_interest = parent_node.findall(self.namespace + 'namePart')[0]
            for n in name_of_interest.iter(): 
                res = n.text.split(',')
                res.reverse()
                res = ' '.join(res).strip()
        return res

    def get_publisher(self, root): 
        publisher_info = ''
        tag_in_xml = root.findall(self.namespace + 'originInfo[@eventType="publication"]')
        if len(tag_in_xml) == 0: 
            return publisher_info

        publisher_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'publisher')
        
        for t in publisher_tag_in_xml: 
            for node in t.iter(): 
                publisher_info = node.text
                
        return publisher_info

    def get_genre(self, root): 
        genres = []
        tag_in_xml = root.findall(self.namespace + 'genre')

        for t in tag_in_xml: 
            for node in t.iter(): 
                genres.append(node.text)
        return genres

    def get_note_tag(self, root): 
        third_note = ''
        tag_in_xml = root.findall(self.namespace + 'note')

        if len(tag_in_xml) >= 3: 
            for t in [tag_in_xml[2]]: 
                for node in t.iter(): 
                    third_note = node.text
        return third_note

    def get_performer(self, root): 
        performer = ''
        tag_in_xml = root.findall(self.namespace + 'note[@type="performers"]')

        for t in tag_in_xml: 
            for node in t.iter(): 
                performer = node.text
        return performer

    def get_alt_date_issued(self, root): 
        date_issued = []
        tag_in_xml = root.findall(self.namespace + 'originInfo[@eventType="publication"]')
        date_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'dateIssued')

        for t in date_tag_in_xml: 
            for node in t.iter(): 
                date_issued = node.text
        return date_issued

    def get_date_issued(self, root): 
        date_issued = []
        tag_in_xml = root.findall(self.namespace + 'originInfo')

        if len(tag_in_xml) > 0: 
            date_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'dateIssued')
            for t in date_tag_in_xml: 
                for node in t.iter(): 
                    date_issued.append(node.text)
        return ', '.join(date_issued)

    def get_issue_number(self, root): 
        issue_number = ''
        tag_in_xml = root.findall(self.namespace + 'identifier[@type="issue number"]')
        
        for t in tag_in_xml: 
            for node in t.iter(): 
                issue_number = node.text
        return issue_number

    def get_record_identifier(self, root): 
        record_identifier = ''
        tag_in_xml = root.findall(self.namespace + 'recordInfo')
        record_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'recordIdentifier[@source="SIRSI"]')
        
        for t in record_tag_in_xml: 
            for node in t.iter(): 
                record_identifier = node.text
        return record_identifier

    def get_physical_description(self, root): 
        extent = ''
        tag_in_xml = root.findall(self.namespace + 'physicalDescription')
        extent_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'extent')

        for t in extent_tag_in_xml: 
            for node in t.iter(): 
                extent = node.text
        return extent

    def get_identifier(self, filename): 
        name = filename.split('.xml')[0]
        return name.split('druid_')[1]

    def parse_xml(self, file): 
        xmlTree = ET.parse(file)
        root = xmlTree.getroot()
        title = self.get_title(root)
        uniform_title = self.get_uniform_title(root)
        subtitle = self.get_subtitle(root)
        composer = self.get_composer(root)
        arranger = self.get_role(root, 'arranger')
        instrumentalist = self.get_role(root, 'instrumentalist')
        performer = self.get_performer(root)

        publisher = self.get_publisher(root)
        extent = self.get_physical_description(root)
        date_issued = self.get_date_issued(root)
        identifier = self.get_identifier(file.name)

        return {'title': title, 
                'uniform_title': uniform_title, 
                'subtitle': subtitle,
                'composer': composer, 
                'arranger': arranger, 
                'instrumentalist': instrumentalist, 
                'performer': performer, 
                'publisher': publisher, 
                'extent': extent, 
                'date_issued': date_issued,
                'identifier': identifier}
    
    def batch_parse_xml(
        self, 
        files, 
        show_progress=True,
        progress_bar=None, 
        amount_done=0,
        size=0): 

        parsed  = []

        step = 1/size if size > 0 else 0

        for i, file in enumerate(files):
            amount_done += step 
            parsed_file = self.parse_xml(file)
            parsed.append(parsed_file)
            if show_progress and progress_bar: progress_bar.progress(round(amount_done, 1))
        mods_info = self.combine_parsed_files(parsed)
        return mods_info        

    def combine_parsed_files(self, parsed): 
        final_dict = defaultdict(list)
        for item in parsed:
            for k, v in item.items(): 
                final_dict[k].append(v)
        return final_dict