from FindingAidParser import * 
from MODSParser import *
from MARCParser import *
from Parser import *
import streamlit as st

parser = Parser()
st.title('Parse XML Files')
menu = ["Parse File(s)"]
xml_files = None
st.subheader("Parse file(s)")
multiple_files = st.file_uploader("Select a single file or multiple files. Refresh the page to clear all files.", accept_multiple_files=True)

if multiple_files is None:
    st.text("No files selected. Please select at least one file.") 
else:
    uploaded_files = [file for file in multiple_files]
    xml_files = [file for file in uploaded_files if os.path.splitext(file.name)[1] == ".xml"]
    non_xml_files = [file.name for file in uploaded_files if os.path.splitext(file.name)[1] != ".xml"]

    if len(non_xml_files) > 0: 
        invalid_file_warning = "Found non xml files. The following files will be ignored: " + ", ".join(non_xml_files)
        st.warning(invalid_file_warning)

        # print(multiple_files)
    if st.button("Parse Files"):
        if len(xml_files) > 0:  
            parser.parse(xml_files)

        else: 
            st.warning("No .xml files detected. Please double check selected file(s) and ensure the extension on each file is .xml.")