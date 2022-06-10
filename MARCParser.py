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


class MARCParser(): 
    def __init__(self): 
        self.namespace = "{http://www.loc.gov/MARC21/slim}"

    def get_composer(self, root): 
        composer = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="100"]')
        if tag_in_xml: 
            composer_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'subfield[@code="a"]')
            for t in composer_tag_in_xml: 
                for node in t.iter(): 
                    composer = node.text.strip(',')
                    composer = composer.split(',')
                    composer.reverse()
                    composer = ' '.join(composer).strip()                     
        return composer

    def get_size(self, root): 
        size = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="300"]')
        if tag_in_xml: 
            size_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'subfield[@code="c"]')
            for t in size_tag_in_xml: 
                for node in t.iter(): 
                    size = node.text
                    
        return size

    def get_publisher_info(self, root): 
        publisher = ''
        issue_num = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="264"]')
        if tag_in_xml: 
            publisher_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'subfield[@code="b"]')
            for t in publisher_tag_in_xml: 
                for node in t.iter(): 
                    publisher = node.text.strip(',')
                
        return publisher


    def get_catalog_number(self, root): 
        catalog_num = ''
        
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="028"]')
        
        if tag_in_xml:         
            catalog_number_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'subfield[@code="a"]')
            for t in catalog_number_tag_in_xml: 
                for node in t.iter(): 
                    catalog_num = node.text
                
        return catalog_num

    def get_identifier(self, root, filename): 
        name = filename.split('.xml')[0]
        match = re.findall('[0-9]{8}', name)[0]
        return match

    def should_use_composer(self, root, role_of_interest): 
        alt = ''
        tag_needed = None
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="100"]')
        if tag_in_xml: 
            alt_tag_in_xml = tag_in_xml[0].findall(self.namespace + 'subfield[@code="e"]')
            for t in alt_tag_in_xml: 
                for node in t.iter(): 
                    if 'instrumentalist' in node.text.lower() and role_of_interest.lower() == 'instrumentalist': 
                        return True
                    if 'arranger' in node.text.lower() and role_of_interest.lower() == 'arranger': 
                        return True
        return False

    def get_arranger_or_instrumentalist(self, root, role_of_interest): 
        role = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="700"]')
        for t in tag_in_xml:
            name = ''
            for i, node in enumerate(t.iter()): 
                if i == 1: 
                    name = node.text
                if node.text and role_of_interest.lower() in node.text.lower(): 
                    role = name
                    role = role.strip(',')
                    role = role.split(',')
                    role.reverse()
                    role = ' '.join(role).strip()
                    break
        if role == '' and self.should_use_composer(root, role_of_interest): 
            role = self.get_composer(root)

        return role

    def get_collection(self, root): 
        collection = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="690"]')
        if tag_in_xml: 
            collection_tag = tag_in_xml[0].findall(self.namespace + 'subfield[@code="a"]')
            for t in collection_tag: 
                for node in t.iter(): 
                    collection = node.text
        return collection.strip()

    def get_roll_type(self, root): 
        roll_type = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="500"]')
        if tag_in_xml and len(tag_in_xml) >= 2: 
            roll_type_tag = tag_in_xml[1].findall(self.namespace + 'subfield[@code="a"]')
            for t in roll_type_tag: 
                for node in t.iter(): 
                    roll_type = node.text
        return roll_type

    def get_citation_a(self, root): 
        citation = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="510"]')
        if tag_in_xml: 
            citation_tag = tag_in_xml[0].findall(self.namespace + 'subfield[@code="a"]')
            for t in citation_tag: 
                for node in t.iter(): 
                    citation = node.text
        return citation

    def get_citation_c(self, root): 
        citation = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="510"]')
        if tag_in_xml: 
            citation_tag = tag_in_xml[0].findall(self.namespace + 'subfield[@code="c"]')
            for t in citation_tag: 
                for node in t.iter(): 
                    citation = node.text
        return citation
        

    def get_date(self, root): 
        date = ''
        tag_in_xml = root.findall(self.namespace + 'controlfield[@tag="008"]')
        if tag_in_xml: 
            for node in tag_in_xml[0].iter(): 
                if len(node.text) >= 11: 
                    date += node.text[7:11]
                
                if len(node.text) >= 15 and node.text[11:15].isdigit(): 
                    date += ', ' + node.text[11:15]
        return date
        
    def get_title(self, root): 
        title = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="245"]')
        if tag_in_xml: 
            title_tag = tag_in_xml[0].findall(self.namespace + 'subfield[@code="a"]')
            for t in title_tag: 
                for node in t.iter(): 
                    title = node.text
        return title

    def get_subtitle(self, root): 
    #     245!
        subtitle = ''
        tag_in_xml = root.findall(self.namespace + 'datafield[@tag="245"]')
        if tag_in_xml: 
            subtitle_tag = tag_in_xml[0].findall(self.namespace + 'subfield[@code="b"]')
            for t in subtitle_tag: 
                for node in t.iter(): 
                    subtitle = node.text
        return subtitle
    
    def parse_xml(self, file): 
        xmlTree = ET.parse(file)
        root = xmlTree.getroot()
        
        title = self.get_title(root)
        subtitle = self.get_subtitle(root)
        
        composer = self.get_composer(root)
        arranger = self.get_arranger_or_instrumentalist(root, 'arranger')
        instrumentalist = self.get_arranger_or_instrumentalist(root, 'instrumentalist')
        publisher = self.get_publisher_info(root)
        
        size = self.get_size(root)
        catalog_number = self.get_catalog_number(root)
        date = self.get_date(root)

        identifier = self.get_identifier(root, file.name)
        
        collection = self.get_collection(root)
        citation_a = self.get_citation_a(root)
        citation_c = self.get_citation_c(root)
        roll_type = self.get_roll_type(root)

        return {'title': title, 
                'subtitle': subtitle,
                'composer': composer, 
                'arranger': arranger, 
                'instrumentalist': instrumentalist, 
                'publisher': publisher, 
                'size': size, 
                'catalog_number': catalog_number, 
                'date': date,
                'identifier': identifier,
                'collection': collection, 
                'citation_a': citation_a, 
                'citation_c': citation_c, 
                'roll_type': roll_type}
            
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
        marc_info = self.combine_parsed_files(parsed)
        return marc_info                

    def combine_parsed_files(self, parsed): 
        final_dict = defaultdict(list)
        for item in parsed:
            for k, v in item.items(): 
                final_dict[k].append(v)
        return final_dict