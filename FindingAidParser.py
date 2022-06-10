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


class FindingAidParser:

    def __init__(self):
        self.wikidata_xml_mapping = {}
        self.namespace = "{urn:isbn:1-931666-22-9}"
        self.nlp = spacy_streamlit.load_model("./models/en/")

    def clear_dict(self):
        self.wikidata_xml_mapping = {k : '' for k in self.wikidata_xml_mapping}

    def __get_namespace(self, element):
        m = re.match(r'\{.*\}', element.tag)
        return m.group(0) if m else ''

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
        finding_aid_info = self.combine_parsed_files(parsed)
        return finding_aid_info     
    
    def parse_xml(self, file): 
        if file:
            self.clear_dict()
            xmlTree = ET.parse(file)
            root = xmlTree.getroot()
            # self.namespace = self.__get_namespace(root)
            self.get_description(root)
            self.get_title_and_label(root)
            self.get_inventory_number(root, file)
            self.get_collection_creator()
            self.get_collection_size(root)
            self.get_url(file)
            res = self.wikidata_xml_mapping
        return res

    def parse_xml_local(self, filepath):
        res = {}
        ext = os.path.splitext(filepath )[-1].lower()
        if ext == '.xml': 
            self.clear_dict()
            xmlTree = ET.parse(filepath)
            root = xmlTree.getroot()
            # self.namespace = self.__get_namespace(root)

            self.get_description(root)
            self.get_title_and_label(root)
            self.get_inventory_number(root, filepath)
            self.get_collection_creator()
            self.get_collection_size(root)
            self.get_url(filepath)
            res = self.wikidata_xml_mapping
        return res      

    def get_alt_description(self, root):
        alt_desc = ".//%sscopecontent" % (self.namespace)
        alt_desc_tag = root.find(alt_desc)
        if (alt_desc_tag is not None and len(alt_desc_tag) > 0):
            alt_desc_tag = root.findall(alt_desc)
            description = []
            for t in alt_desc_tag:
                for node in t.iter():
                    description.append(node.text)
            return description[2]
        return ''

    def get_description(self, root):
        abstract = './/%sabstract' % (self.namespace)
        abstract_tag = root.findall(abstract)
        description = ""
        for t in abstract_tag:
            for node in t.iter():
                description += node.text
        description = description.strip()
        description = description.replace('\n', '').replace('\r', '')
        if description == "":
            description = self.get_alt_description(root)
        self.wikidata_xml_mapping['full_description'] = description
        first_sentence = ''
        doc = self.nlp(description)
        for sent in doc.sents:
            first_sentence = sent
            break
        self.wikidata_xml_mapping['description'] = first_sentence
        return (description, first_sentence)

    def get_title_and_label(self, root):
        unittitle = './/%sunittitle' % (self.namespace)
        title_tag = root.findall(unittitle)
        res = []
        for t in title_tag:
            for i, node in enumerate(list(t.iter())):
                res.append(node.text)
        title = res[0].translate(str.maketrans('','', string.punctuation))
        self.wikidata_xml_mapping['title'] = title
        self.wikidata_xml_mapping['label'] = title
        return title

    def get_alt_inventory_number(self, filepath):
        path = filepath.upper()
        pattern = 'ARS-?.?\d+'
        match = re.findall(pattern, path)
        match = match[0].replace('-', '')
        match = match.replace('.', '')
        return match

    def get_inventory_number(self, root, filepath):
        unitid = './/%sunitid' % (self.namespace)
        inventory_tag = root.findall(unitid)
        res = []
        for t in inventory_tag:
            for node in t.iter():
                res.append(node.text)
        if len(res) > 0:
            inventory_number = res[0].replace('-', '')
            inventory_number = inventory_number.replace(".", "")
            self.wikidata_xml_mapping["inventory_number"] = inventory_number
        else:
            self.wikidata_xml_mapping['inventory_number'] = self.get_alt_inventory_number(filepath)
        return self.wikidata_xml_mapping['inventory_number']

    def get_date_retrieved(self):
        date = datetime.datetime.now()
        self.wikidata_xml_mapping['date_retrieved'] = date.strftime('%d %B %Y')
        return self.wikidata_xml_mapping['date_retrieved']

    def get_alt_collection_creator(self):
        title = str(self.wikidata_xml_mapping['description'])
        doc = self.nlp(title)
        possible_creator = ''
        nameFound = False
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG']:
                # prioritize people over orgs, choose first person found
                if nameFound and ent.label_ == 'ORG': continue
                if ent.label_ == 'PERSON' and nameFound == False:
                    possible_creator = ent.text.title()
                    nameFound = True
                    return possible_creator
                possible_creator = ent.text
        return possible_creator

    def get_collection_creator(self):
        self.wikidata_xml_mapping['collection_creator'] = ''
        title = self.wikidata_xml_mapping['title']
        title = title.replace('Collection', '')
        title = title.replace('The', '')
        title = title.replace('Sheet', '')
        title = title.replace('Music', '')
        andInTitle = 'and' in title
        doc = self.nlp(title.strip())
        possible_creators = []
        nameFound = False
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG']:
                # prioritize names over orgs for collection creators
                if nameFound and ent.label_ == 'ORG': continue
                if ent.label_ == 'PERSON': nameFound = True
                possible_creators.append(ent.text.title())
        if len(possible_creators) == 1:
            self.wikidata_xml_mapping['collection_creator'] = possible_creators[0]
        else:
            if andInTitle and len(possible_creators) > 0:
                self.wikidata_xml_mapping['collection_creator'] = ' and '.join(possible_creators)
            elif len(possible_creators) > 0:
                self.wikidata_xml_mapping['collection_creator'] = possible_creators[0]

        if self.wikidata_xml_mapping['collection_creator'] == '':
            self.wikidata_xml_mapping['collection_creator'] = self.get_alt_collection_creator()
        return self.wikidata_xml_mapping['collection_creator']

    def get_collection_size(self, root):
        physdesc =  './/%sphysdesc' % (self.namespace)
        physdesc_tag = root.findall(physdesc)
        pattern = '\\n\s*'
        outer_res = []
        for t in physdesc_tag:
            inner_res = []
            for node in t.iter():
                inner_res.append(node.text)
            outer_res.append(inner_res)

        collection_size = ' '.join(outer_res[0])
        collection_size = re.sub('\\n\s*', '', collection_size)
        self.wikidata_xml_mapping['collection_size'] = collection_size
        return collection_size

    def get_url(self, filepath):
        finding_aid_url = ''
        name = self.wikidata_xml_mapping['label']
        querified = name.replace(" ", "%20")
        url = "https://searchworks.stanford.edu/?q=" + querified + "&format=json"
        try:
            response = requests.get(url=url)
            data = response.json()
        except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
            pass

        if len(data['response']['docs']) > 0:
            try:
                finding_aid_url = data['response']['docs'][0]['url_suppl'][0]
            except KeyError:
                pass

        self.wikidata_xml_mapping['url'] = finding_aid_url
        return finding_aid_url
  
    def combine_parsed_files(self, parsed): 
        final_dict = defaultdict(list)
        for item in parsed:
            for k, v in item.items(): 
                final_dict[k].append(v)
        return final_dict