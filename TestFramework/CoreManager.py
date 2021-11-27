"""
The 'execute.py' is the entry point to the framework from the execution perspective.
@ Author : Vinayak Rao, <vinayak.rao@applicsolutions.com>
@ Date Created : 20-Mar-2021.
"""

import os, sys
import ini, csv
import datetime

import unittest
import shutil

import termcolor
os.system('color')

sys.path.append(os.path.dirname(os.getcwd()))

from Library import Globals
from Library import DeviceOperation
from Library import common_utils
from Library import DeviceConnect
from Library import Reporter
from Library import parsers

sys.path.remove(os.path.dirname(os.getcwd()))

""" The CoreManager() class implements the methods for the Framework Driver. This implementation is responsible for
    driving of the Test execution.
"""
class CoreManager():
    
    def __init__(self):
        self.globals = Globals.GlobalsObjects()  
        report = Reporter.Reporter()
        

        """ Parse the INI file to get the content of it."""
        configs = {}
        ini_parser = INIParser()    
        tests = ini_parser.parse_test_ini('Tests')
        device_details = ini_parser.parse_config_ini('Device')
        test_settings = ini_parser.parse_config_ini('Test_Settings')
        execution_settings = ini_parser.parse_config_ini('Execution_Settings')        
        
        for device_detail in device_details:
            configs[device_detail] = device_details[device_detail]
        for test_setting in test_settings:
            configs[test_setting] = test_settings[test_setting]
        for execution_setting in execution_settings:
            configs[execution_setting] = execution_settings[execution_setting]
            
        object_repo_headers_from_config = execution_settings['obj_repo_headers'].split(",")
        execution_settings['obj_repo_headers'] = [header.strip() for header in object_repo_headers_from_config]
        test_csv_headers_from_config = execution_settings['test_csv_file_headers'].split(",")
        execution_settings['test_csv_file_headers'] = [header.strip() for header in test_csv_headers_from_config]

        parser_obj = parsers.LangStringParser(os.path.join(Globals.main_base_path, "Config", "Text_out.xml"))

        string_table_with_id = parser_obj.get_string_table_with_id('fr-FR')
        configs['string_table_with_id'] = string_table_with_id

        if test_settings['language'] == 'fr-FR':
            locale = 'fra'
            string_table_with_eng_str = parser_obj.get_strings_with_english('fr-FR')
            configs['string_table_with_eng_str'] = string_table_with_eng_str
        elif test_settings['language'] == 'en-GB':
            locale ='eng'
            string_table_with_eng_str = parser_obj.get_strings_with_english('en-GB')
            configs['string_table_with_eng_str'] = string_table_with_eng_str
        elif test_settings['language'] == 'de-DE':
            locale ='deu'
            string_table_with_eng_str = parser_obj.get_strings_with_english('de-DE')
            configs['string_table_with_eng_str'] = string_table_with_eng_str
        elif test_settings['language'] == 'es-ES':
            locale ='spa'
            string_table_with_eng_str = parser_obj.get_strings_with_english('es-ES')
            configs['string_table_with_eng_str'] = string_table_with_eng_str
        elif test_settings['language'] == 'it-IT':
            locale ='ita'
            string_table_with_eng_str = parser_obj.get_strings_with_english('it-IT')
            configs['string_table_with_eng_str'] = string_table_with_eng_str
        elif test_settings['language'] == 'pt-PT':
            locale ='por'
            string_table_with_eng_str = parser_obj.get_strings_with_english('pt-PT')
            configs['string_table_with_eng_str'] = string_table_with_eng_str

        curr_user = test_settings['user_type']
        self.globals.set_global_cfg(configs)
        
        """ Create the Logger instantiation. """
        self.globals.create_logger(report.get_report_folder_name())        
        self.logger = self.globals.logger
        Globals.global_obj = self.globals
        
        clear = lambda: os.system('cls')
        clear()
        
        self.logger.info("**********************************************************************************************")
        self.logger.info("******************************** STARTING THE SUITE EXECUTION ********************************")
        self.logger.info("**********************************************************************************************")
        
        csv_parser = CSVParser(self.globals)
        
        header_counter = 0
        test_obj_headers_from_csv = (csv_parser.get_obj(True))
        for each_exp_obj_header in execution_settings['obj_repo_headers']:
            header_counter+=1 if each_exp_obj_header in test_obj_headers_from_csv else 0
        if header_counter != len(execution_settings['obj_repo_headers']):
            self.logger.info(termcolor.colored("The Object CSV header is not matching with the expecting header provided in Config file. Hence stopping the execution.", "red"))
            return


        """ Get the supported CSV Test file out of all the given tests """

        test_suites = csv_parser.get_supported_tests(tests)
        self.logger.info("Supported Test Suites : "+str(test_suites))
        
        """ Get all the Tests from the Supported Test CSV. """
        test_objects = csv_parser.get_obj()  
        self.logger.debug("Supported Test Objects : "+str(test_objects))
                
        tc_number = 1   
        
        """ Iterate over each of the test suit to execute the test """
        self.logger.debug("Preparing the Test Suite from the Test Suites.")

        for test_suite in test_suites:
            
            test_csv_header_counter = 0
            test_csv_headers_from_csv = (csv_parser.get_all_tests(test_suite, True))
            for each_exp_obj_header in execution_settings['test_csv_file_headers']:
                test_csv_header_counter+=1 if each_exp_obj_header in test_csv_headers_from_csv else 0
            if test_csv_header_counter != len(execution_settings['test_csv_file_headers']):
                self.logger.info(termcolor.colored("The Test CSV header in [%s] is not matching with the expecting header provided in Config file. Hence stopping the execution."%test_suite, "red"))
                return

            self.logger.debug("Adding the test Suite - [%s]"%test_suite)
            test_cases = csv_parser.get_all_tests(test_suite)
            
            for test_case in test_cases:
                self.logger.debug("Adding the Test Case [%s] from suite [%s]."%(test_case[0]['test_name'], test_suite))
                test_name = 'test_%s_%s' %("{0:0=4d}".format(tc_number), test_case[0]['test_name'])
                #test = test_generator(test_case, test_objects, report, self.globals, device_details,string_table_with_eng_str,locale, curr_user)
                test_suite_names = test_suite
                excel_report = test_settings['excel_report']
                test = test_generator(test_case, test_objects, report, self.globals, device_details, string_table_with_eng_str, locale, curr_user, test_suite_names, excel_report)
                setattr(TestSequense, test_name, test)
                tc_number+=1
                
 
    """ The method execute() triggers the execution via unittest framework.
    """
    def execute(self):
        self.logger.debug("Triggering the Unit Test to Start the execution.")
        unittest.main()
            
""" The class TestSequense() helps to generate the test cases dynamically at run time.
"""
class TestSequense(unittest.TestCase):
    test_si_no = 1
    initial_time = datetime.datetime.now()
    
    
    def setUp(self):
        """ Establish the Connection with Device. """
        # Globals.dev_connection = DeviceConnect.DeviceConnect(Globals.global_cfg['device_ip'],                                               Globals.global_cfg['port'],
        #                                              Globals.global_cfg['password'], Globals.global_obj)
        # Globals.handler = Globals.dev_connection.connect()
        # self.dev_ops = DeviceOperation.DeviceOperation(Globals.global_obj)

        
    def tearDown(self):
        TestSequense.test_si_no+=1
        if not Globals.dev_connection.Is_connection_alive():
            Globals.dev_connection = DeviceConnect.DeviceConnect(Globals.global_cfg['device_ip'],
                                                             Globals.global_cfg['port'],
                                                             Globals.global_cfg['password'], Globals.global_obj)
            Globals.handler = Globals.dev_connection.connect()
            self.dev_ops = DeviceOperation.DeviceOperation(Globals.global_obj)

    @classmethod
    def setUpClass(cls):
        """ Establish the Connection with Device. """
        Globals.dev_connection = DeviceConnect.DeviceConnect(Globals.global_cfg['device_ip'],
                                                             Globals.global_cfg['port'],
                                                             Globals.global_cfg['password'], Globals.global_obj)
        Globals.handler = Globals.dev_connection.connect()
        cls.dev_ops = DeviceOperation.DeviceOperation(Globals.global_obj)

    @classmethod
    def tearDownClass(cls):
        Globals.handler.disconnect()
        Globals.dev_connection = None


def test_generator(test_case, test_objects, report, global_obj, device_details, locale_str, locale, user_type, test_suite_names,excel_report):


    """ Signature for Dynamic Test Generator
    """
    def test(self):
        self.dev_ops.navigate_to_home(test_objects, user_type)
        
        self.device_details = device_details

        self.logger = global_obj.logger
        self.logger.info("")
        self.logger.info("-------------------------------------------------------------------------------------------------------------------------------------------------------------")
        self.logger.info("************************ Starting the Test - [%s] [%s] ************************"%(self._testMethodName,
                                                                                                            test_case[0]['test_id']))
        status = "FAIL"
        exp_text = ""
        screenshot_path = ""

        test_report_data = []
        test_report_data1 = []
        
        final_verification = False
        alll_step_status = []
        
        for step in test_case:   
            
            test_step_result = {}
            
            self.logger.debug(">>>>>>>>>>>>>>>>>> Perform [%s] on Object [%s] with value [%s] <<<<<<<<<<<<<<<<<<<<<<<<"
                             %(step['action'], step['control'], step['value']))        

            if step['action']=='click':
                status = self.dev_ops.click(test_objects, step['control'])
            if step['action']=='longclick':
                status = self.dev_ops.clicklong(test_objects, step['control'])
            if step['action']=='clickxy':
                status = self.dev_ops.clickxy(test_objects, step['control'])
            if step['action']=='clicktext':
                text_value = str(step['value'])
                if locale_str[text_value] is None:
                    step['value'] = step['value']
                else:
                    step['value'] = locale_str[text_value]
                status = self.dev_ops.clicktext(test_objects, step['control'], step['value'],locale)
            if step['action']=='verify_img':
                status = self.dev_ops.verify_img(test_objects, step['control'])
            if step['action']=='verifytext':
                text_value = str(step['value'])
                if locale_str[text_value] is None:
                    step['value'] = step['value']
                else:
                    step['value'] = locale_str[text_value]
                status = self.dev_ops.verify_text(test_objects, step['control'], step['value'], locale)
            if step['action']=='verifystring':
                text_value = str(step['value'])
                if locale_str[text_value] is None:
                    step['value'] = step['value']
                else:
                    step['value'] = locale_str[text_value]
                status = self.dev_ops.verify_string(test_objects, step['control'], step['value'], locale)
            if step['action']=='verifyexptext':
                status = common_utils.verifyexptext()
            if step['action']=='verify_exp_img':
                exp_text = step['value']
                status = self.dev_ops.verify_exp_img(test_objects, step['control'])
            if step['action']=='delay':
                time_in_sec = 1 if step['value']=='' else int(step['value'])                    
                status = common_utils.delay(time_in_sec)
            if step['action']=='GOTO_HOME':
                status = self.dev_ops.goto_home(test_objects, step['control'])
            if step['action'] == 'enter_keypad':
                status = self.dev_ops.enter_keypad(test_objects, step['control'], step['value'])
            if step['action'] == 'verify_status_img':
                status = self.dev_ops.verify_device_status_img(test_objects, step['control'], step['value'])
            if step['action'] == 'verify_status_txt':
                # text_value = str(step['value'])
                # if locale_str[text_value] is None:
                #     step['value'] = step['value']
                # else:
                #     step['value'] = locale_str[text_value]
                status = self.dev_ops.verify_device_status_txt(test_objects, step['control'], step['value'],locale)
            if step['action'] == 'enter_ai_value':
                status = self.dev_ops.enter_ai_value(test_objects, step['control'], step['value'])
            if step['action'] == 'click_di_state':
                status = self.dev_ops.click_di_state(test_objects, step['control'], step['value'])
            if step['action'] == 'verifyvalue':
                status = self.dev_ops.verify_string(test_objects, step['control'], step['value'],locale)
            if step['action'] == 'time_stamp':
                status = self.dev_ops.time_stamp(test_objects, step['control'], step['value'])
            if step['action'] == 'login_user':
                status = self.dev_ops.goto_user(test_objects, step['value'])
            if step['action'] == 'set_initial':
                status = self.dev_ops.set_initial(step['action'])
            if step['action'].startswith('api.'):
                status = self.dev_ops.event(step['action'])

            alll_step_status.append(status)
            
            if not final_verification: 
                step_description = '*'+step['action']+" "+step['control'] if step['imp_step'] else step['action']+" "+step['control']
                self.logger.info(step['action']+" "+step['control']+" "+step['value']+ " : "+(termcolor.colored("PASS", "green") if status else termcolor.colored("FAIL", "red")))
                test_step_result = {'si_no' : str(TestSequense.test_si_no), 'test_id':'', 'test_name':'',
                            'summary':'', 'act_res':'', 'exp_res':'', 'status':status, 'link' : '',
                            'execution_time' : '', 'suite_name':'',
                            'language':'', 'build':'',
                            'device_type':'', 'screenshot_path':screenshot_path,
                            'final_verification' : final_verification, 
                            'step_description':step_description,
                            'control': step['control'], 'action': step['action'], 'value': step['value']}
                test_report_data1.append(test_step_result)
                if not status:
                    if step['imp_step']:
                        final_verification = True
                        break
            if step==test_case[-1]:
                final_verification = True
                
            
        final_time = datetime.datetime.now()        
        execution_time = common_utils.get_time_diff(TestSequense.initial_time, final_time)
        
        status = all(alll_step_status) if len(alll_step_status)!=0 else False
        
        if status==False:
            status = "FAIL"
        else:
            status = "PASS"
        if status=="FAIL":
            fail_case_folder = os.path.join(report.get_report_folder_name(), "FAIL_Cases")
            if not os.path.isdir(fail_case_folder):
                os.mkdir(fail_case_folder)
            screenshot_path = os.path.join(fail_case_folder, test_case[0]['test_id']+".jpg")
            shutil.copyfile(Globals.hmi_live_image_path, screenshot_path)
            self.logger.info("*************************** End of Test - [%s] [%s] ===> %s ***************************"%(
                termcolor.colored(self._testMethodName, "red"), 
                termcolor.colored(test_case[0]['test_id'], "red"), termcolor.colored("FAIL", "red")))
            self.logger.error("The FAILed image is saved at : %s "%screenshot_path)
        else:
            self.logger.info("*************************** End of Test - [%s] [%s] ===> %s ***************************"%(
                termcolor.colored(self._testMethodName, "green"), 
                termcolor.colored(test_case[0]['test_id'], "green"), termcolor.colored("PASS", "green")))
            
        test_case_result = {'si_no' : str(TestSequense.test_si_no), 'test_id':test_case[0]['test_id'], 'test_name':test_case[0]['test_name'],
                            'sheet_data': test_suite_names, 'excel_report': excel_report, 'test_name': test_case[0]['test_name'],
                            'summary':test_case[0]['summary'], 'act_res':"AR", 'exp_res':exp_text, 'status':status, 'link' : test_case[0]['test_id']+'.jpg',
                            'execution_time' : execution_time, 'suite_name':Globals.global_cfg['test_suite_name'],
                            'language':Globals.global_cfg['language'], 'build':Globals.global_cfg['build'],
                            'device_type':Globals.global_cfg['device_type'], 'screenshot_path':screenshot_path,
                            'final_verification' : final_verification, 'step_description':step['description']}
        test_report_data.append(test_case_result)
        test_report_data = test_report_data+test_report_data1
        report.update_report(test_report_data)
        
        
        self.logger.info("************************ End the Test - [%s] ************************"%self._testMethodName)
        self.logger.info("-------------------------------------------------------------------------------------------------------------------------------------------------------------")

        self.logger.info("")
        
        
    return test    


""" Test INI file parser class
"""        
class INIParser():
    
    def __init__(self):
        pass
        
    """ The method parse_test_ini() parses the test.ini file.
        Args    : section     - The section name in test.ini file.
        Returns : config_data - Dictionary containing the confis items of the specified section.
    """
    def parse_test_ini(self, section):
        self.tests_cfg = os.path.join(os.getcwd(), "../", "Config", "tests.ini")
        config_data = ini.parse(open(self.tests_cfg).read())
        return config_data[section]
    
    
    """ The method parse_config_ini() parses the config.ini file.
        Args    : section     - The section name in config.ini file.
        Returns : config_data - Dictionary containing the confis items of the specified section.
    """
    def parse_config_ini(self, section):
        self.tests_cfg = os.path.join(os.getcwd(), "../", "Config", "config.ini")
        config_data = ini.parse(open(self.tests_cfg).read())
        return config_data[section]


""" CSV Parser Class to parse the test cases and steps from the CSV file.
"""
class CSVParser():
    def __init__(self, global_obj):
        self.tests_folder_path = os.path.join(Globals.main_base_path, "Tests")
        self.logger = global_obj.logger

        

    def get_supported_tests(self, all_tests):
        supported_tests = []
        [supported_tests.append(suit_name) for suit_name, support_status in all_tests.items() if support_status==True]
        self.logger.debug("Supported Tests as Parsed from CSV - %s"%str(supported_tests))
        return (supported_tests)
    
    
    def get_obj(self, return_header_only=False):
        repo_path = os.path.join(self.tests_folder_path, "CO_Repo.csv")
        
        object_repos = {}
        first_row = True
        
        with open(repo_path, 'r') as csvfile:
            csvreader = csv.reader(csvfile) 
            
            for row in csvreader:
                each_obj = {}
                
                if first_row:
                    first_row = False
                    object_row_header_index = {row[i]:i for i in range(0, len(row))}
                    if return_header_only:
                        return [each_row for each_row in row if each_row!='']
                    continue
                else:
                    each_obj['gold_img'] = row[object_row_header_index['image']]
                    each_obj['gold_text'] = row[object_row_header_index['text']]
                    each_obj['gold_roi'] = row[object_row_header_index['ROI']]
                    each_obj['gold_text_roi'] = row[object_row_header_index['Text_ROI']]
                    each_obj['gold_coord'] = row[object_row_header_index['coord']]
                    each_obj['gold_occu'] = row[object_row_header_index['Occurance']]
                    each_obj['gold_threshold'] = row[object_row_header_index['Threshold']]
                    each_obj['threshold_type'] = row[object_row_header_index['Threshold_Type']]
                    each_obj['threshold_value'] = row[object_row_header_index['Threshold_Value']]
                    object_repos[row[object_row_header_index['object_name']]] = each_obj
        self.logger.debug("Objects as Parsed from CSV - %s"%str(object_repos))
        return object_repos
                
    
    def get_all_tests(self, suite_name, return_header_only=False):
        suite_file_path = os.path.join(self.tests_folder_path, suite_name+".csv")  

        first_row = True
        with open(suite_file_path, 'r') as csvfile: 
            
            csvreader = csv.reader(csvfile) 
            
            each_test_case = []
            all_tests = []
            
            for row in csvreader:    
                if first_row:
                    csv_test_row_header_index = {row[i]:i for i in range(0, len(row))}
                    first_row = False
                    if return_header_only:
                        return [each_row for each_row in row if each_row!='']
                    continue
                
                action_temp = row[csv_test_row_header_index['ACTION']].strip()
                if len(action_temp)>0:
                    if action_temp[0] == '#':
                        continue
                     
                if "TC" in row[csv_test_row_header_index['Test_ID']]:
                    each_test_case = []
                if "end" in row[csv_test_row_header_index['Test_ID']]:
                    all_tests.append(each_test_case)
                    continue
                test_case = {}
                if len(each_test_case)==0:                
                    test_case['test_id'] = row[csv_test_row_header_index['Test_ID']]
                    test_case['test_name'] = row[csv_test_row_header_index['Test_Name']]
                    test_case['summary'] = row[csv_test_row_header_index['Summary']]

                action = row[csv_test_row_header_index['ACTION']] 
                test_case['imp_step'] = True if (len(action)!=0 and (action[0]=='*')) else False
                test_case['action'] = action.split("*")[1] if action[0]=="*" else action
                
                test_case['control'] = row[csv_test_row_header_index['CONTROL']]
                test_case['value'] = row[csv_test_row_header_index['Value1']]
                test_case['description'] = row[csv_test_row_header_index['Description']]
                if first_row:
                    first_row = False
                else:
                    each_test_case.append(test_case)
        self.logger.debug("Tests as Parsed from CSV - %s"%str(all_tests))
        return (all_tests)

cm = CoreManager()
cm.execute()
                    


                

        

        




