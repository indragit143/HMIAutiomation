'''
Created on 21-Mar-2021

@author: Ganesh Prasad
'''
import os
from Library.Globals import base_path
from Library.Globals import REPORT_STRINGS
import Library.common_utils as common_utils

from Library import template

import pandas as pd
import glob
import warnings
from bs4 import BeautifulSoup
import numpy as np

class Reporter():
    def __init__(self):
        report_folder_name = "HMI_Report_"+common_utils.get_datetime_for_report_folder()
        if not os.path.isdir(os.path.join(base_path, "../", "Report")):
            os.mkdir(os.path.join(base_path, "../", "Report"))
        self.reports_main_folder = os.path.join(base_path, "../", "Report", report_folder_name)
        if not os.path.isdir(self.reports_main_folder):
            os.mkdir(self.reports_main_folder)
            if os.path.isdir(self.reports_main_folder):
                print ("Report will be created at : %s"%self.reports_main_folder)
            else:
                print ("Failed to create the report at : %s"%self.reports_main_folder)
        self.html_report_path = os.path.join(self.reports_main_folder, "HMI_Test_Report.html")
        self.all_case = ""
        self.PASS = 0
        self.FAIL = 0
        self.NA = 0
        self.BLOCK = 0
        
    def get_report_folder_name(self):
        return self.reports_main_folder
        
        
    def get_template_data(self):
        return template.report_template
    
    def get_test_case_data(self):
        return template.test_case_row
    
    def write_report(self, data):
        f = open(self.html_report_path, 'w')
        f.write(data)
        f.close()

    def write_to_excel(self,excel_1):
        # print("this is test for config.ini", excel_1)
        if str(excel_1) == "True":
            # Ignore Warnings
            warnings.filterwarnings('ignore', '', )
            # File path
            fPath = os.path.join(self.reports_main_folder)

            fNames = glob.glob(r'{0}\**\*.html'.format(fPath), recursive=True)

            path = fNames

            # empty list
            data = []

            # for getting the header from
            # the HTML file
            for paths in path:

                list_header = []
                soup = BeautifulSoup(open(paths), 'html.parser')
                header = soup.find_all("table")[0].find("tr")

                for items in header:
                    try:
                        list_header.append(items.get_text())
                    except:
                        continue

                # for getting the data
                HTML_data = soup.find_all("table")[0].find_all("tr")[1:]
                for element in HTML_data:
                    sub_data = []
                    for sub_element in element:
                        try:
                            sub_data.append(sub_element.get_text())

                        except:
                            continue
                    data.append(sub_data)

            # Storing the data into Pandas
            # DataFrame
            dataFrame = pd.DataFrame(data=data, columns=list_header)
            dataFrame.drop(dataFrame.columns[[-1]], axis=1, inplace=True)
            dataFrame.drop(dataFrame.columns[[-1]], axis=1, inplace=True)

            # Removing the &emsp;&emsp;&emsp;
            dataFrame['Summary/Steps'] = dataFrame['Summary/Steps'].str.replace(r'\W', " ", regex=True)

            file_name = 'HMI_EXCEL_REPORT'

            # filling the empty rows:
            dataFrame['Suite Name'].replace('', np.nan, inplace=True)
            dataFrame.fillna(method='ffill', inplace=True)

            # Folder creation locations
            folder_loc = os.path.join(self.reports_main_folder, file_name)

            # Spliting the values:
            split_values = dataFrame['Suite Name'].unique()

            # Writing to Excel:
            writer = pd.ExcelWriter(folder_loc + ".xlsx", engine="xlsxwriter")

            for value in split_values:
                if len(value) >= 31:
                    new_value = value[:30]
                    df1 = dataFrame[dataFrame['Suite Name'] == value]

                    df1.drop(df1.columns[[2]], axis=1, inplace=True)
                    # print(df1)
                    df1.to_excel(writer, sheet_name=new_value, index=False)

                else:
                    df1 = dataFrame[dataFrame['Suite Name'] == value]

                    df1.drop(df1.columns[[2]], axis=1, inplace=True)
                    # print(df1)
                    df1.to_excel(writer, sheet_name=value, index=False)
            writer.save()
        else:
            print("Excel Report is not enabled to Generate.")

    def update_report(self, test_case_results):
        self.excel_report = test_case_results[0]['excel_report']
        xx = 1
        data = self.get_template_data()
        for test_case_result in test_case_results:
            if test_case_result['final_verification']: 
                
                each_test_case = self.get_test_case_data()
                each_test_case = each_test_case.replace("{disp}", "''")
                each_test_case = each_test_case.replace("{si_no}", test_case_result['si_no'])
                each_test_case = each_test_case.replace("{test_id}", test_case_result['test_id'])
                each_test_case = each_test_case.replace("{sheet_data}", test_case_result['sheet_data'])
                each_test_case = each_test_case.replace("{test_case_name}", test_case_result['test_name'])

                each_test_case = each_test_case.replace("{summary1}", test_case_result['summary'])
                each_test_case = each_test_case.replace("{exp_result}", test_case_result['exp_res'])
                
                each_test_case = each_test_case.replace("{result}", test_case_result['status'])
                
                if test_case_result['status'] == "FAIL":
                    each_test_case = each_test_case.replace("{result_color}", "w3-red")
                    each_test_case = each_test_case.replace("{screenshot}", test_case_result['link'])
                    self.FAIL+=1
                else:
                    each_test_case = each_test_case.replace("{result_color}", "w3-green")
                    each_test_case = each_test_case.replace("{font_color}", "white")
                    each_test_case = each_test_case.replace("{screenshot}", "")
                    self.PASS+=1
                each_test_case = each_test_case.replace("{srn_path}", test_case_result['screenshot_path'])
        
                self.all_case = self.all_case + each_test_case
                
            else:
                test_case_result['status']="PASS" if test_case_result['status']==True else "FAIL"
                test_case_result['si_no'] = test_case_result['si_no'] +"_"+str(xx)
                xx+=1
                data = self.get_template_data()
                each_test_case = self.get_test_case_data()
                each_test_case = each_test_case.replace("{disp}", "none")
                each_test_case = each_test_case.replace("{si_no}", "")
                each_test_case = each_test_case.replace("{si_no_id}", test_case_result['si_no'])
                each_test_case = each_test_case.replace("{test_id}", test_case_result['test_id'])
                each_test_case = each_test_case.replace("{sheet_data}", "")
                each_test_case = each_test_case.replace("{test_case_name}", test_case_result['test_name'])
                
                if test_case_result['status']=="PASS":
                    each_test_case = each_test_case.replace("{font_color}", "green")
                    each_test_case = each_test_case.replace("{screenshot}", "")
                else:
                    each_test_case = each_test_case.replace("{font_color}", "red")
                    each_test_case = each_test_case.replace("{screenshot}", test_case_result['link'])

                each_test_case = each_test_case.replace("{summary1}", "&emsp;&emsp;&emsp;"+test_case_result['step_description'])

                if test_case_result['action'].startswith('api.'):
                    if test_case_result['status'] == "PASS":
                        act_msg = "Functional API Executed Successfully."
                    else:
                        act_msg = "Functional API failed to Execute."
                else:
                    act_msg = REPORT_STRINGS[test_case_result['action']][test_case_result['status']].format(test_case_result['control'])

                each_test_case = each_test_case.replace("{exp_result}", act_msg)
                
                each_test_case = each_test_case.replace("{result}", test_case_result['status'])
                self.all_case = self.all_case + each_test_case
                
                data = data.replace("{test_case}", self.all_case)
                
                
        data = data.replace("{PASS}", str(self.PASS))
        data = data.replace("{FAIL}", str(self.FAIL))
        data = data.replace("{NA}", str(self.NA))
        data = data.replace("{BLOCK}", str(self.BLOCK))
        execution_time_str = test_case_results[0]['execution_time']['hour']+" hr "+ test_case_results[0]['execution_time']['minutes'] +" min "
        execution_time_str = execution_time_str + test_case_results[0]['execution_time']['seconds']+" sec "
        data = data.replace("{execution_time}", execution_time_str)
        data = data.replace("{total_cases}", test_case_results[0]['si_no'])
        data = data.replace("{suite_name}", test_case_results[0]['suite_name'])
        data = data.replace("{language}", test_case_results[0]['language'])
        data = data.replace("{build}", test_case_results[0]['build'])
        data = data.replace("{device_type}", test_case_results[0]['device_type'])
        data = data.replace("{test_case}", self.all_case)
        self.write_report(data)
        self.write_to_excel(self.excel_report)
        
                
        
