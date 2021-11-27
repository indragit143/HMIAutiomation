'''
Created on 21-Mar-2021

@author: Ganesh Prasad
'''
import os 
from _ast import Pass
import logging

base_path = os.getcwd()
hmi_live_image_path = os.path.join(base_path, "../", "HMI_Screens", 
                                               "HMI_Screens", 'HMI_LIVE_IMG.jpg')
main_base_path = os.path.dirname(base_path)

dev_connection = None
handler = None
global_cfg = None
global_obj = None

REPORT_STRINGS = {'click'      : {
                                   'PASS'  : "The image {} is clicked in HMI screen.",
                                   'FAIL' : "The image {} is not clicked in HMI screen."},
                  'longclick'      : {
                                   'PASS'  : "The image {} is long clicked for 5 secs in HMI screen.",
                                   'FAIL' : "The image {} is not long clicked in HMI screen."},
                  'clicktext'  : {
                                   'PASS'  : "The expected text {} is clicked in HMI screen.",
                                   'FAIL' : "The expected text {} is not clicked in HMI screen."},
                  'clickxy'  : {
                                   'PASS'  : "The coordinations {} is clicked in HMI screen.",
                                   'FAIL' : "The expected coordinations {} is not clicked in HMI screen."},
                  'verify_img' : {
                                   'PASS'  : "The image {} is found in HMI screen.",
                                   'FAIL' : "The image {} is not found in HMI screen."},
                  'verify_exp_img' : {
                                   'PASS'  : "The expected image {} is found in HMI screen.",
                                   'FAIL' : "The expected image {} is not found in HMI screen."
                                   },
                  'verifytext' : {
                                   'PASS'  : "The expected text {} is found in HMI screen.",
                                   'FAIL' : "The expected text {} is not found in HMI screen."
                                   },
                  'delay' : {
                                   'PASS'  : "Success to introduce the delay.",
                                   'FAIL' : "Failed to introduce the delay."
                                   },
                  'GOTO_HOME' : {
                                   'PASS'  : "Success to navigate to Home Screen.",
                                   'FAIL' : "Failed to Navigate to Home Screen."
                                    },
                  'enter_keypad' : {
                                   'PASS'  : "Success to enter pin on Virtual Keypad.",
                                   'FAIL' : "Failed to enter pin on Virtual Keypad."
                                    },
                  'verify_status_img' : {
                                   'PASS'  : "The expected image {} is found in HMI screen.",
                                   'FAIL' : "The image {} is not found in HMI screen."
                                    },
                  'verify_status_txt': {
                                   'PASS': "The expected text {} is found in HMI screen.",
                                   'FAIL': "The expected text {} is not found in HMI screen."
                                    },
                  'enter_ai_value' : {
                                   'PASS'  : "Success to enter analog input.",
                                   'FAIL' : "Failed to enter analog input."},
                  'click_di_state' : {
                                   'PASS'  : "Success to click Digital input.",
                                   'FAIL' : "Failed to click Digital input."},
                  'event': {
                                   'PASS'  : "Success to generate trip or warning.",
                                   'FAIL' : "Failed to generate trip or warning."},
                  'verify_status_text':{
                                   'PASS'  : "Success to extract or matching text.",
                                   'FAIL' : "Failed to extract or matching text."},
                  'verifystring':{
                                   'PASS'  : "Success to extract or matching text.",
                                   'FAIL' : "Failed to extract or matching text."},
                  'verifyvalue':{
                                   'PASS'  : "Success to extract or matching text.",
                                   'FAIL' : "Failed to extract or matching text."},
                  'set_initial':{
                                   'PASS'  : "Success to set the initial values to HMI.",
                                   'FAIL' : "Failed to set the initial values to HMI."},
                  'time_stamp': {
                                    'PASS': "Success to extract {} matching text.",
                                    'FAIL': "Failed  to extract {} matching text."},
                  'login_user': {
                                    'PASS': "Success to login to Home Screen.",
                                    'FAIL': "Failed to login to Home Screen."}
                  }

class GlobalsObjects():
    def __init__(self):
        
        self.paths_obj = Paths()
        self.global_cfg = {}
        self.base_path = os.getcwd()
        self.global_cfg = {}
        
        
    def set_global_cfg(self, cfg_data):
        global global_cfg
        global_cfg = cfg_data
        
    def get_global_cfg(self):
        global global_cfg
        return global_cfg
    
    def create_logger(self, report_folder_path):
        self.logger = Logger(self, report_folder_path)
        
        
class Paths():
    def __init__(self):
        pass
        
        
class Logger():
    
    def __init__(self, globals, report_folder_path):
        self.globals = globals
        
        log_level = self.globals.get_global_cfg()['log_level']
        if log_level=="INFO":
            level = logging.INFO
        elif log_level=="ERROR":
            level = logging.ERROR
        elif log_level=="WARNING":
            level = logging.WARNING
        elif log_level=="DEBUG":
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.basicConfig(filename=os.path.join(report_folder_path, "hmi_test.log"), 
                            filemode='w',  level=level, format='%(asctime)s-%(name)s - %(levelname)s - %(message)s')

        
    def info(self, message):
        print (message)
        logging.info(message)
        
    def debug(self, message):
        logging.debug(message)


    def warning(self, message):
        logging.warning(message)


    def error(self, message):
        print (message)
        logging.error(message)


        

        

