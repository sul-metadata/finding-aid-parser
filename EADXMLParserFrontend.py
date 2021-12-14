import streamlit as st
import pandas as pd 
import base64

from EADXMLParser import * 
import os
import xml.etree.ElementTree as ET

from random import randint

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="ParsedFindingAids.csv">Download csv file</a>'
    # f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'
    return href

def main():
    parser = EADParser()   
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
            invalid_file_warning = "Found non xml files! The following files will be ignored): " + ", ".join(non_xml_files)
            st.warning(invalid_file_warning)

        if st.button("Parse Files"): 
            if len(xml_files) > 0: 
                parsed = []
                progress_bar = st.progress(0)
                step = 1/len(xml_files)
                amount_done = 0
                
                for file in xml_files:
                    amount_done += step
                    parsed_file = parser.parse_xml_by_reference(file)
                    parsed.append(parsed_file)
                    progress_bar.progress(round(amount_done, 1))
                
                combined_files = parser.combine_parsed_files(parsed)
                df = pd.DataFrame.from_dict(combined_files)
                st.markdown(get_table_download_link(df), unsafe_allow_html=True)

            else: 
                st.warning("No .xml files detected! Please double check selected file(s) and ensure the extension on each file is .xml.")
        
if __name__ == '__main__': 
    main()