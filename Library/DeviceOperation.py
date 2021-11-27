'''
Created on 21-Mar-2021

@author: Ganesh Prasad
'''
import os 
import Library.Globals
from Library.BaseTextManager import BaseTextManager
from Library.Globals import base_path
import Library.factoryPassword
import Library.BaseImageManager
from pickle import NONE, TRUE
from Library import common_utils

import DigiSimPy
from DigiSimPy.KeyWords import WriteChannel, WriteModbus
from DigiSimPy.GENERIC.IODefinition import AI
from DigiSimPy.GENERIC.GenericReference import AP
from DigiSimPy.GENERIC.IODefinition import *
from DigiSimPy.Initial_Settings import bootSettings
from Library.trips_warnings import *

"""
The Class to implement the Device Operations.
"""
class DeviceOperation():
    
    def __init__(self, global_obj):
        self.logger = global_obj.logger
        self.img_base = Library.BaseImageManager.BaseImageManager(global_obj)
        self.txt_base = Library.BaseTextManager.BaseTextManager(global_obj)
        self.base_delay = int(global_obj.get_global_cfg()['base_delay'])
        self.delay_factor = int(global_obj.get_global_cfg()['delay_factor'])
        self.golden_app_path = os.path.join(Library.Globals.main_base_path, "HMI_Screens", "App_1")

#   print (Library.Globals.global_cfg['string_table_with_id'])
#   print (Library.Globals.global_cfg['string_table_with_eng_str'])

    """
        The method home_popup_handler() handles the popup on HMI screen.
        Args    : func  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def home_popup_handler(func):        
        def inner1(self, *args, **kwargs):
            handler_object_string = Library.Globals.global_cfg['popup_objects']
            handler_objects = [handler_object.strip() for handler_object in handler_object_string.split(",")]
            for popup in handler_objects:
                if self.verify_img(args[0], popup, 2):
                    self.click(args[0], popup, 1)   
            common_utils.delay(self.base_delay*self.delay_factor)        
            status = func(self, *args, **kwargs)            
            return status        
        return inner1

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def try_on_failure(func):            
        def inner1(self, *args, **kwargs): 
            gold_img_status = True 
            retry_given = (kwargs['retries'] if 'retries' in (kwargs.keys()) else 10)

            for retry_iteration in range(1, retry_given):
                self.logger.debug("Trying to match at iteration : %s"%str(retry_iteration))
                status1 = func(self, *args, **kwargs)
                if (type(status1))==list:
                    status = status1[0]
                    gold_img_status = status1[1]
                else:
                    status = status1

                if status==True or status=="PASS":
                    self.logger.debug("Success to match at iteration : %s"%str(retry_iteration))
                    break
                else:
                    self.logger.debug("Fail to match at iteration : %s"%str(retry_iteration))
                if retry_iteration==5:
                    if not gold_img_status:
                        Library.Globals.handler.disconnect()
                        Library.Globals.handler = Library.Globals.dev_connection.connect()
            return status
        return inner1

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    @try_on_failure
    def click(self, test_objects, control_name, retries=10):
        click_status = False

        self.logger.debug("Performing the click on the control [%s] with details [%s]"%(control_name, test_objects[control_name]))        
        click_img = test_objects[control_name]['gold_img']
        hmi_roi = test_objects[control_name]['gold_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        golden_img_threshold = self.get_golden_img_threshold(test_objects[control_name]['gold_threshold'].strip())
        self.logger.debug("HMI ROI is : %s"%str(hmi_roi))
        self.logger.debug("Object Occurance given : %s"%str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)
        live_img_status = Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)

        golden_img_path = os.path.join(self.golden_app_path, click_img)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens", 
                                               "HMI_Screens", 'HMI_LIVE_IMG.jpg')
        
        golden_cord = self.img_base.get_image_cordinates(hmi_img_path, golden_img_path, him_area=hmi_roi_area, 
                                                         occurance=golden_img_occu, threshold=golden_img_threshold)
        if golden_cord !=2:
            if hmi_roi_area != None:
                golden_x_cor = int(golden_cord[0]) + hmi_roi_area[0][0]
                golden_y_cor = int(golden_cord[1]) + hmi_roi_area[0][1]
            else: 
                golden_x_cor = int(golden_cord[0])
                golden_y_cor = int(golden_cord[1])
            self.logger.debug("Matched Coordinates for the control [%s] in HMI screen is [%s]"%(control_name, str([golden_x_cor, golden_y_cor])))
            if (type(golden_cord))==list:
                self.logger.debug("Clicking on the control [%s] on the coordinate in HMI screen [%s, %s]"%(control_name, 
                                                                                            str(golden_x_cor), str(golden_y_cor)))
                Library.Globals.handler.mouseMove(golden_x_cor, golden_y_cor)
                Library.Globals.handler.mousePress(1)
                time.sleep(3)
                click_status = True
                self.logger.debug("Success to click on the control [%s] on the coordinate in HMI screen [%s, %s]"%(control_name, 
                                                                                            str(golden_x_cor), str(golden_y_cor)))
            else:
                self.logger.error("Click on the control [%s] will not be performed"%control_name)        
        return [click_status, live_img_status]

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    @try_on_failure
    def clicklong(self, test_objects, control_name, retries=10):
        click_status = False

        self.logger.debug(
            "Performing the click and hold on the control [%s] with details [%s]" % (control_name, test_objects[control_name]))
        click_img = test_objects[control_name]['gold_img']
        hmi_roi = test_objects[control_name]['gold_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        golden_img_threshold = self.get_golden_img_threshold(test_objects[control_name]['gold_threshold'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)
        live_img_status = Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)

        golden_img_path = os.path.join(self.golden_app_path, click_img)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens",
                                    "HMI_Screens", 'HMI_LIVE_IMG.jpg')

        golden_cord = self.img_base.get_image_cordinates(hmi_img_path, golden_img_path, him_area=hmi_roi_area,
                                                         occurance=golden_img_occu, threshold=golden_img_threshold)
        if golden_cord != 2:
            if hmi_roi_area != None:
                golden_x_cor = int(golden_cord[0]) + hmi_roi_area[0][0]
                golden_y_cor = int(golden_cord[1]) + hmi_roi_area[0][1]
            else:
                golden_x_cor = int(golden_cord[0])
                golden_y_cor = int(golden_cord[1])
            self.logger.debug("Matched Coordinates for the control [%s] in HMI screen is [%s]" % (
            control_name, str([golden_x_cor, golden_y_cor])))
            if (type(golden_cord)) == list:
                self.logger.debug(
                    "Clicking on the control [%s] on the coordinate in HMI screen [%s, %s]" % (control_name,
                                                                                               str(golden_x_cor),
                                                                                               str(golden_y_cor)))
                Library.Globals.handler.mouseMove(golden_x_cor, golden_y_cor)
                Library.Globals.handler.mouseDown(1)
                time.sleep(10)
                Library.Globals.handler.mouseUp(1)
                time.sleep(3)
                click_status = True
                self.logger.debug(
                    "Success to clicked and holded for 5 secs on the control [%s] on the coordinate in HMI screen [%s, %s]" % (control_name,
                                                                                                       str(
                                                                                                           golden_x_cor),
                                                                                                       str(
                                                                                                           golden_y_cor)))
            else:
                self.logger.error("Click on the control [%s] will not be performed" % control_name)
        return [click_status, live_img_status]

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def clickxy(self, test_objects,control_name):
        click_status = False

        self.logger.debug("Performing the click on the control [%s] with details [%s]" % (control_name, test_objects[control_name]))
        click_coord = test_objects[control_name]['gold_coord'].strip()
        live_img_status = Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)

        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens", "HMI_Screens", 'HMI_LIVE_IMG.jpg')

        coord_xy = self.get_coords_as_list(click_coord)


        if coord_xy != None:
            if(self.img_base.click_coord_exists(hmi_img_path,coordxy=coord_xy)):
                golden_cord_x = coord_xy[0]
                golden_cord_y = coord_xy[1]
                Library.Globals.handler.mouseMove(golden_cord_x, golden_cord_y)
                Library.Globals.handler.mousePress(1)
                time.sleep(3)
                click_status = True
                self.logger.debug("Successfully clicked on the control [%s] on the coordinate in HMI screen [%s, %s]" % (control_name,
                    str(golden_cord_x),
                    str(golden_cord_y)))
            else:
                self.logger.error("Click on Co-ordinations X [%s] Y [%s] will not be performed due to co-ordinations doesn't exist in HMI" % str(coord_xy[0]),str(coord_xy[1]))
        else:
            self.logger.error("Click on the Control [%s] will not be performed due to invalid co-ordinates in repository." % control_name)
            click_status = False
        return click_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def clicktext(self, test_objects,control_name, value, locale):
        click_status = False

        threshold_type = self.get_golden_threshold_type(test_objects[control_name]['threshold_type'].strip())

        threshold_value = self.get_golden_threshold_value(test_objects[control_name]['threshold_value'].strip())

        img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())

        #target_text = test_objects[control_name]['gold_text'].strip()

        hmi_roi = test_objects[control_name]['gold_text_roi'].strip()

        hmi_roi_area_text = self.get_roi_as_list(hmi_roi)

        Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)

        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens","HMI_Screens", 'HMI_LIVE_IMG.jpg')

        golden_text_cord = self.txt_base.get_text_cordinates(hmi_img_path, value,threshold_type=threshold_type,threshold_value=threshold_value,him_area=hmi_roi_area_text,occurance=img_occu, locale=locale)

        if golden_text_cord !=2:
            if hmi_roi_area_text != None:
                golden_x_cor = int(golden_text_cord[0]) + hmi_roi_area_text[0][0]
                golden_y_cor = int(golden_text_cord[1]) + hmi_roi_area_text[0][1]
            else:
                golden_x_cor = int(golden_text_cord[0])
                golden_y_cor = int(golden_text_cord[1])

            self.logger.debug("Matched Coordinates for the Target Text [%s] in HMI screen is [%s]"%(value, str([golden_x_cor, golden_y_cor])))

            if (type(golden_text_cord))==list:
                self.logger.debug("Clicking on the Target Text [%s] on the coordinate in HMI screen [%s, %s]"%(value,
                                                                                            str(golden_x_cor), str(golden_y_cor)))
                Library.Globals.handler.mouseMove(golden_x_cor, golden_y_cor)
                Library.Globals.handler.mousePress(1)
                time.sleep(3)
                click_status = True
                self.logger.info("Success to click on the Target Text [%s] on the coordinate in HMI screen [%s, %s]"%(value,
                                                                                            str(golden_x_cor), str(golden_y_cor)))
            else:
                self.logger.error("Click on the Target Text [%s] will not be performed"%value)
        else:
            self.logger.error("Click on the Target Text [%s] not Found in HMI Screen" % value)
        return click_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_dev_connection(self):
        return self.dev_connection

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_roi_as_list(self, hmi_roi):
        if hmi_roi=="":
            hmi_roi_area = None 
        else:
            roi = hmi_roi.split(",")
            x1 = int(roi[0]);x2 = int(roi[1]);x3 = int(roi[2]);x4 = int(roi[3])
            hmi_roi_area = [[x1, x2], [x3, x4]] 
        return hmi_roi_area

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_coords_as_list(self, coords):
        if coords=="":
            coords_xy = None
        else:
            coords_pt = coords.split(",")
            x = int(coords_pt[0]);y = int(coords_pt[1])
            coords_xy = [x, y]
        return coords_xy

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_golden_img_occurance(self, golden_occu):
        if golden_occu=="":
            return 1
        else:
            return int(golden_occu)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_golden_img_threshold(self, golden_threshold):
        if golden_threshold=="":
            return 0.9 
        else:
            return float(golden_threshold)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_golden_threshold_type(self, golden_threshold_type):
        if golden_threshold_type =="":
            gold_threshold_type=None
        else:
            gold_threshold_type=int(golden_threshold_type)
        return gold_threshold_type

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def get_golden_threshold_value(self, golden_threshold_value):
        if golden_threshold_value =="":
            gold_threshold_value=None
        else:
            gold_threshold_value=int(golden_threshold_value)
        return gold_threshold_value

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    @try_on_failure
    def verify_exp_img(self, test_objects, control_name, retries=10):    
        verify_status = False   

        golden_img_path = os.path.join(self.golden_app_path, test_objects[control_name]['gold_img'])    
        
        hmi_roi = test_objects[control_name]['gold_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s"%str(hmi_roi))
        self.logger.debug("Object Occurance given : %s"%str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi) 
        
        live_img_status = Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens", 
                                                   "HMI_Screens", 'HMI_LIVE_IMG.jpg')
        self.logger.debug("Checking if the golden img [%s] is present in the HMI img [%s]."%(str(golden_img_path), str(hmi_img_path)))
            
        golden_cord = self.img_base.get_image_cordinates(hmi_img_path, golden_img_path, him_area=hmi_roi_area, occurance=golden_img_occu)
        
        self.logger.debug("Received coordinates after matching the golden img [%s] with HMI img [%s] is [%s]"%(str(golden_img_path), 
                                                                                                              str(hmi_img_path), 
                                                                                                              str(golden_cord)))

        if golden_cord!=2:
            self.logger.debug("The golden image [%s] is found in the HMI screen [%s]."%(str(golden_img_path), str(hmi_img_path)))
            verify_status = True            
        return [verify_status, live_img_status]

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    @home_popup_handler
    def goto_home(self, test_objects, control_name, retries_now=2):
        self.logger.debug("Navigating to <Home> Screen.")
        self.click(test_objects, "MAIN_MENU", retries_now)
        common_utils.delay(self.base_delay*self.delay_factor)
        self.click(test_objects, "HOME", retries_now)
        
        self.logger.debug("Successfully navigated to <Home> Screen.")
        
        """ TODO : Add a check if the screen has really navigated to Home Screen.
        """
        return True

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def navigate_to_home(self, test_objects, user):
        status = False
        if (self.verify_img(test_objects, "SCREEN_SAVER", 2)):
            self.click(test_objects, "SCREEN_SAVER", 2)
            if user == "TECHNICIAN":
                pass_code = "8412"
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "DOWN", 2)
                self.click(test_objects, "TECHNICIAN", 2)
                self.click(test_objects, "PASSWORD", 2)
                self.enter_keypad(test_objects, "TICK_MARK", pass_code)
                self.click(test_objects, "TICK_MARK", 2)
            elif user == "MAINTENANCE":
                pass_code = "407"
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "PASSWORD", 2)
                self.enter_keypad(test_objects, "TICK_MARK", pass_code)
                self.click(test_objects, "TICK_MARK", 2)
            elif user == "FACTORY":
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "DOWN", 2)
                self.click(test_objects, "FACTORY", 2)

                curr_pwd = self.factory_pass(test_objects, "CURRENT_PIN")
                c_pass = str(curr_pwd[2])

                macId = self.factory_pass(test_objects, "MACHINE_ID")
                m_id = str(macId[2])

                Factory_password = Library.factoryPassword.getOTP(c_pass, m_id)

                self.click(test_objects, "CLOSE_BUTTON", 2)
                self.click(test_objects, "PASSWORD", 2)
                self.enter_keypad(test_objects, "TICK_MARK", Factory_password)
                self.click(test_objects, "TICK_MARK", 2)
            status = True
        elif (self.verify_img(test_objects, "SUBMENU_CLOSE_HOME", 2)):
            self.click(test_objects, "HOME", 2)   
            status = True 
        elif (self.verify_img(test_objects, "HOME_BANNER", 2)):  
            self.click(test_objects, "MAIN_MENU", 2)
            common_utils.delay(self.base_delay*self.delay_factor)
            self.click(test_objects, "HOME", 2)    
            status = True   
        else:            
            self.goto_home(test_objects, "", 2)
            if self.verify_img(test_objects, "HOME_BANNER"):
                status = True 
        return status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def verify_text(self, test_objects, control_name, value, locale):

        threshold_type = int(test_objects[control_name]['threshold_type'])
        threshold_value = int(test_objects[control_name]['threshold_value'])
        hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)

        Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens",
                                    "HMI_Screens", 'HMI_LIVE_IMG.jpg')
        self.logger.debug("Checking if the Target Text [%s] is present in the HMI img [%s]." % (str(value), str(hmi_img_path)))

        return BaseTextManager.verifytext(self, hmi_img_path, value, threshold_type, threshold_value, him_area=hmi_roi_area, occurance=golden_img_occu, locale=locale)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def verify_string(self, test_objects, control_name, value, locale):

        # Color_Convertion = test_objects[control_name]['Color_conv']
        # print(Color_Convertion)
        threshold_type = int(test_objects[control_name]['threshold_type'])
        threshold_value = int(test_objects[control_name]['threshold_value'])
        hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)

        Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens",
                                    "HMI_Screens", 'HMI_LIVE_IMG.jpg')
        self.logger.debug(
            "Checking if the Target Text [%s] is present in the HMI img [%s]." % (str(value), str(hmi_img_path)))

        return BaseTextManager.verifystring(self, hmi_img_path, value, threshold_type, threshold_value,
                                          him_area=hmi_roi_area, occurance=golden_img_occu)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def enter_keypad(self, test_objects, control_name, value):
        click_status = False

        self.logger.debug("Entering the numeric pin on the control [%s] with details [%s]" % (control_name, test_objects[control_name]))
        click_img = test_objects[control_name]['gold_img']
        hmi_roi = test_objects[control_name]['gold_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        golden_img_threshold = self.get_golden_img_threshold(test_objects[control_name]['gold_threshold'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)
        live_img_status = Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)

        golden_img_path = os.path.join(self.golden_app_path, click_img)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens",
                                    "HMI_Screens", 'HMI_LIVE_IMG.jpg')

        golden_cord = self.img_base.get_image_cordinates(hmi_img_path, golden_img_path, him_area=hmi_roi_area,
                                                         occurance=golden_img_occu, threshold=golden_img_threshold)
        if golden_cord != 2:
            if hmi_roi_area != None:
                golden_x_cor = int(golden_cord[0]) + hmi_roi_area[0][0]
                golden_y_cor = int(golden_cord[1]) + hmi_roi_area[0][1]
            else:
                golden_x_cor = int(golden_cord[0])
                golden_y_cor = int(golden_cord[1])
            self.logger.debug("Matched Coordinates for the control [%s] in HMI screen is [%s]" % (control_name, str([golden_x_cor, golden_y_cor])))
            if (type(golden_cord)) == list:
                self.logger.debug("Entering numberic pin on the control [%s] on the coordinate in HMI screen [%s, %s]" % (control_name,
                                                                                               str(golden_x_cor),
                                                                                               str(golden_y_cor)))
                [num_coords_x, num_coords_y] = self.getCoords_virkeypad(value,golden_x_cor,golden_y_cor)

                for i in range(len(num_coords_x)):
                    Library.Globals.handler.mouseMove(num_coords_x[i], num_coords_y[i])
                    Library.Globals.handler.mousePress(1)
                    time.sleep(3)
                click_status = True
                self.logger.debug("Success to enter numberic pin on the control [%s] on the coordinate in HMI screen [%s, %s]" % (control_name,
                                                                                                       str(golden_x_cor), str(golden_y_cor)))
            else:
                self.logger.error("Enter numberic pin on the control [%s] will not be performed" % control_name)
        #return [click_status, live_img_status]
        return click_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def verify_img(self, test_objects, control_name, retry_now=10):
        return self.verify_exp_img(test_objects, control_name, retries=retry_now)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def verify_device_status_img(self,test_objects, control_name, value):
        device_status_img = False

        golden_img_path = os.path.join(self.golden_app_path, test_objects[control_name]['gold_img'])

        hmi_roi = test_objects[control_name]['gold_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)

        live_imgs_dir = Library.Globals.dev_connection.Get_live_images(Library.Globals.handler,float(value))

        self.logger.debug("Checking if the golden device status img [%s] is present in the HMI imgs path [%s]." % (
        str(golden_img_path), str(live_imgs_dir)))

        for filename in os.listdir(live_imgs_dir):
            hmi_image_path = os.path.join(live_imgs_dir,filename)
            if device_status_img == False:
                golden_cord = self.img_base.get_image_cordinates(hmi_image_path, golden_img_path, him_area=hmi_roi_area,
                                                         occurance=golden_img_occu)
                self.logger.debug(
                "Received coordinates after matching the golden img [%s] with HMI img [%s] is [%s]" % (str(golden_img_path),
                                                                                                   str(filename),
                                                                                                   str(golden_cord)))
                if golden_cord != 2:
                    self.logger.debug("The golden image [%s] is found in the HMI screen [%s]." % (str(golden_img_path), str(filename)))
                    device_status_img = True
                    break
        for f in os.listdir(live_imgs_dir):
            os.remove(os.path.join(live_imgs_dir,f))
        return device_status_img

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def verify_device_status_txt(self,test_objects, control_name, value, locale):
        device_status_txt = False

        #golden_img_path = os.path.join(self.golden_app_path, test_objects[control_name]['gold_img'])
        threshold_type = int(test_objects[control_name]['threshold_type'])
        threshold_value = int(test_objects[control_name]['threshold_value'])
        hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))

        hmi_roi_area = self.get_roi_as_list(hmi_roi)

        live_imgs_dir = Library.Globals.dev_connection.Get_live_images(Library.Globals.handler, duration=5)

        self.logger.debug("Checking if the device status text [%s] is present in the HMI imgs path [%s]." % (str(value), str(live_imgs_dir)))
        for filename in os.listdir(live_imgs_dir):
            if device_status_txt == False:
                #device_status_txt = self.txt_base.verifytext(live_imgs_dir+"/"+filename,value,threshold_type,threshold_value,hmi_roi_area,golden_img_occu,locale=locale)
                device_status_txt = self.txt_base.verifystring(live_imgs_dir + "/" + filename, value, threshold_type,
                                                             threshold_value, hmi_roi_area, golden_img_occu,
                                                             locale=locale)
                if device_status_txt == True:
                    self.logger.debug("The golden text [%s] is found in the HMI screen [%s]." % (str(value), str(filename)))
                    device_status_txt = True
                    break
        for f in os.listdir(live_imgs_dir):
            os.remove(os.path.join(live_imgs_dir,f))
        return device_status_txt

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def getCoords_virkeypad(self,value,gold_coord_x,gold_coord_y):
        keypad_layout = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 0, 11]]
        key_coord_x = []
        key_coord_y = []
        for item in range(len(value)):
            for row in range(len(keypad_layout)):
                for column in range(len(keypad_layout[row])):
                    if keypad_layout[row][column] == int(value[item]):
                        if row <= 2:
                            key_coord_x.append(gold_coord_x - (70 * (3 - column)))
                            key_coord_y.append(gold_coord_y - (35 * (5 - (row * 2))))
                        if row == 3:
                            key_coord_x.append(gold_coord_x - (70 * (3 - column)))
                            key_coord_y.append(gold_coord_y + 35)
        return [key_coord_x, key_coord_y]

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def click_di_state(self, test_objects, control_name, value):
        Enter_status = False

        self.logger.debug("Entering the analog Input on the control [%s] with details [%s]" % (
            control_name, test_objects[control_name]))

        Digital_inputs = ["Condensate_Drain_Error",
                          "Dryer_High_Pressure",
                          "Secondary_Band_Select_Remote_Lead_Lag",
                          "Phase_Monitor",
                          "Remote_Start",
                          "Remote_Stop",
                          "Remote_Load_Unload",
                          "Remote_Load_Unload_Enable",
                          "Emergency_Stop"]

        channel_name = test_objects[control_name]['gold_text']
        Value = value

        count = 0
        while count < len(Digital_inputs):
            if len(channel_name) and len(Value) != 0:  # validating if String is Empty
                if Digital_inputs[count] == str(channel_name): #if Value == (0 or 1)  # validating String is not Equeal
                    WriteChannel(channel=eval(str("DI." + channel_name)), val=Value, module_id="",
                                     comment="Setting the analog input value for : " + channel_name)
                    Enter_status = True
                    break
            count += 1
        else:
            print("String is not matched (or) empty please provide valide String..: {}".format(
                str(test_objects[control_name]['gold_text'])))

        return Enter_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def enter_ai_value(self, test_objects, control_name, value):
        Enter_status = False

        self.logger.debug("Entering the analog Input on the control [%s] with details [%s]" % (
            control_name, test_objects[control_name]))

        Analog_inputs = ["Inlet_Vacuum",
                         "Sump_Pressure",
                         "Package_Discharge_Pressure",
                         "Coolant_Filter_Inlet_Pressure",
                         "Coolant_Filter_Outlet_Pressure",
                         "AfterCooler_Discharge_Pressure",
                         "Remote_Pressure",
                         "Interstage_Pressure",
                         "Package_Inlet_Temperature",
                         "Airend_Discharge_Temperature",
                         "Injected_Coolant_Temperature",
                         "Oil_Cooler_Outlet_Temperature",
                         "Aftercooler_Discharge_Temperature",
                         "Dryer_Evaporator",
                         "Dryer_Condenser"
                         ]

        channel_name = test_objects[control_name]['gold_text']
        Value = value

        count = 0
        while count < len(Analog_inputs):
            if len(channel_name) and len(Value) != 0:
                if Analog_inputs[count] == str(channel_name):
                    WriteChannel(channel=eval(str("AI." + channel_name)),
                                 val=Value, module_id="",
                                 comment="Setting the analog input value for : " + channel_name)
                    Enter_status = True
                    break
            count += 1
        else:
            print("String is not matched please provide valide String..: {0} ".format(channel_name))

        return Enter_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    # event create common function for all trips and warnings, Start inhibits these three are called events
    def event(self, action_name):
        Enter_status = False

        action_n = action_name.split(".")
        if len(action_n[1]) != 0:
            eval(str(action_n[1]))
            Enter_status = True
        else:
            print("Invalid Api")
        return Enter_status

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def factory_pass(self, test_objects, control_name):

        threshold_type = int(test_objects[control_name]['threshold_type'])
        threshold_value = int(test_objects[control_name]['threshold_value'])
        hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
        golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
        self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
        self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
        hmi_roi_area = self.get_roi_as_list(hmi_roi)

        Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
        hmi_img_path = os.path.join(base_path, "../", "HMI_Screens","HMI_Screens", 'HMI_LIVE_IMG.jpg')

        return BaseTextManager.factorypass(self, hmi_img_path, threshold_type, threshold_value,
                                           him_area=hmi_roi_area)

    """
        The method connect() creates the device connection.
        Args    : retry  - The attempt number if the Device COnnection Fails. 
        Returns : status - The connection object if success to create and False otherwise.
    """
    def set_initial(self, action):
        status = True
        DigiSimPy.Initial_Settings.bootSettings()
        return status

    def time_stamp(self, test_objects, control_name, value):

        if len(value) == 0:
            threshold_type = int(test_objects[control_name]['threshold_type'])
            threshold_value = int(test_objects[control_name]['threshold_value'])
            hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
            golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
            self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
            self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
            hmi_roi_area = self.get_roi_as_list(hmi_roi)

            Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
            hmi_img_path = os.path.join(base_path, "../", "HMI_Screens", "HMI_Screens", 'HMI_LIVE_IMG.jpg')

            return BaseTextManager.timestamp(self, hmi_img_path, threshold_type, threshold_value,
                                             him_area=hmi_roi_area)

        else:
            user_value = datetime.datetime.strptime(str(value), "%d-%m-%Y").strftime("%Y-%m-%d")
            #print("User Value", user_value)

            # pasting from verify string
            threshold_type = int(test_objects[control_name]['threshold_type'])
            threshold_value = int(test_objects[control_name]['threshold_value'])
            hmi_roi = test_objects[control_name]['gold_text_roi'].strip()
            golden_img_occu = self.get_golden_img_occurance(test_objects[control_name]['gold_occu'].strip())
            self.logger.debug("HMI ROI is : %s" % str(hmi_roi))
            self.logger.debug("Object Occurance given : %s" % str(golden_img_occu))
            hmi_roi_area = self.get_roi_as_list(hmi_roi)

            Library.Globals.dev_connection.Get_live_image(Library.Globals.handler)
            hmi_img_path = os.path.join(base_path, "../", "HMI_Screens",
                                        "HMI_Screens", 'HMI_LIVE_IMG.jpg')
            self.logger.debug(
                "Checking if the Target Text [%s] is present in the HMI img [%s]." % (
                    str(user_value), str(hmi_img_path)))

            return BaseTextManager.verifystring(self, hmi_img_path, user_value, threshold_type, threshold_value,
                                                him_area=hmi_roi_area, occurance=golden_img_occu)

    def goto_user(self, test_objects, user):
        status = False
        if (self.verify_img(test_objects, "SCREEN_SAVER", 2)) or (self.verify_img(test_objects, "USER_BTN", 2)):
            self.click(test_objects, "SCREEN_SAVER", 2)

            if user == "TECHNICIAN":
                pass_code = "8412"
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "DOWN", 2)
                self.click(test_objects, "TECHNICIAN", 2)
                self.click(test_objects, "PASSWORD", 2)
                DeviceOperation.enter_keypad(self, test_objects, "TICK_MARK", pass_code)
                self.click(test_objects, "TICK_MARK", 2)
            elif user == "MAINTENANCE":
                pass_code = "407"
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "PASSWORD", 2)
                DeviceOperation.enter_keypad(self, test_objects, "TICK_MARK", pass_code)
                self.click(test_objects, "TICK_MARK", 2)
            elif user == "FACTORY":
                self.click(test_objects, "USER_BTN", 2)
                self.click(test_objects, "DOWN", 2)
                self.click(test_objects, "FACTORY", 2)

                curr_pwd = self.factory_pass(test_objects, "CURRENT_PIN")
                c_pass = str(curr_pwd[2])

                macId = self.factory_pass(test_objects, "MACHINE_ID")
                m_id = str(macId[2])

                Factory_password = Library.factoryPassword.getOTP(c_pass, m_id)

                self.click(test_objects, "CLOSE_BUTTON", 2)
                self.click(test_objects, "PASSWORD", 2)
                self.enter_keypad(test_objects, "TICK_MARK", Factory_password)
                self.click(test_objects, "TICK_MARK", 2)
        status = True
        return status

            
