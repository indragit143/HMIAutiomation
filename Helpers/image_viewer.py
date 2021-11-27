import sys, os, cv2

sys.path.append(os.path.dirname(os.getcwd()))
from Library import BaseImageManager
 
from Library import Globals
import Library.BaseImageManager
import ini, sys

import os, sys, tempfile, shutil
import time
import threading
from datetime import datetime
import string

import wx
import wx.grid
import wx.dataview
import wx.adv
import shutil
import xlrd
from collections import OrderedDict
import pandas as pd

import py_compile


class SprintPlanner(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1150, 675))
        sprint_plan_panel = wx.Panel(self)
        self.main_panel = wx.Panel(sprint_plan_panel, -1, pos=(0,0), size=(1150, 675))

        self.__addControls()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.nb,0,wx.EXPAND|wx.ALL,border=10)
        sprint_plan_panel.SetSizer(sizer)


    """ Adds the widget to the Sprint Planner launch GUI. 
    """
    def __addControls(self):
        self.nb = wx.Notebook(self.main_panel)

        """ Creates the tabs in the main GUI
        """
        self.hmi_screen_obj = HMIViewer(self.nb)
        self.home_screen_obj = HomeScreen(self.nb)


        """ Adds all the created tabs into main GUI.
        """
        self.__addTabs("GI Locator", self.hmi_screen_obj)
        self.__addTabs("Code Compiler", self.home_screen_obj)




        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__tab_change_callback, self.nb)






    """ The method __addTabs() add the tabs to the main Sprint Planner GUI.
        args    : tab_name      - Name of the tabs to be added.
                  tab_class_obj - Object of the class, where the tab implementation is written.
        returns : None
    """
    def __addTabs(self, tab_name, tab_class_obj):
        self.nb.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.nb.AddPage(tab_class_obj, tab_name)



    """ A callback method __tab_change_callback() called whenever a tab changes in the GUI.
        args    : event - An event object.
        returns : None.
    """
    def __tab_change_callback(self, event):
        current_selected_tab = (self.nb.GetPageText(self.nb.GetSelection()))
        if current_selected_tab in GlobalTab.planner_related_tabs:
            GlobalTab.planner_related_tabs.remove(current_selected_tab)
        if len(GlobalTab.planner_related_tabs) == 0:
            self.home_screen_obj.plan_button.Enable(True)
            GlobalTab.planner_related_tabs.append(-1)



""" The class 'GlobalTab' is a base class, which is derived in the classes of all tabs.
"""
class GlobalTab(wx.Panel):
    planner_related_tabs = ['Projects', 'Test Groups', 'Inputs']
    project_priority = []
    fw_ip_priority = []
    ps_priority = []
    ftl_priority = []
    infra_priority = []
    security_priority = []
    fe_priority = []
    engineers = []
    input_sheet_path = None

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        font = wx.Font(12, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
        wx.StaticText(self, label="HMI Automation Tools", pos=(350, 10)).SetFont(font)
        wx.StaticLine(self, pos=(10, 40), size=(1085, 3))


class HMIViewer(GlobalTab, wx.App):

    def __init__(self, parent):
        GlobalTab.__init__(self, parent)
        self.load_controls()
        self.gil = GILocator()
        self.golden_app_path = os.path.join(Library.Globals.main_base_path, "HMI_Screens", "App_1")


    def load_controls(self):
        locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        filepath = "welcome.png"
        goldenpath = "welcome_small.png"
        self.bmp = wx.Image(filepath,wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        

        # img = wx.EmptyImage(800,480)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(self.bmp), pos=(15,60))

        wx.StaticBox(self, wx.ID_ANY, "Settings", pos=(825, 55), size=(320, 500))


        wx.StaticText(self, label="Select the Input HMI Image :", pos=(835,85))
        self.hmi_screen_path = wx.TextCtrl(self, pos=(835,105), size=(200,25), style=wx.TE_READONLY)
        hmi_screen_browse=wx.Button(self,1, "Browse",pos=(1040,105), size=(50,25))
        hmi_screen_browse.Bind(wx.EVT_BUTTON,self.onHMIImgSelect) 


        wx.StaticText(self, label="Select the Golden Image : ", pos=(835,145))
        self.golden_img_path = wx.TextCtrl(self, pos=(835,165), size=(200,25), style=wx.TE_READONLY)
        golden_img_browse=wx.Button(self,1, "Browse",pos=(1040,165), size=(50,25))
        golden_img_browse.Bind(wx.EVT_BUTTON,self.onGoldenImgSelect)

        locate = wx.Button(self, 1, "Locate", pos=(920, 200), size=(75, 25))
        locate.Bind(wx.EVT_BUTTON, self.onLocate)

        wx.StaticText(self, label="Matched Co-ordinate : ", pos=(835, 240))
        self.golden_cordinate = wx.TextCtrl(self, pos=(975, 235), size=(100, 25), style=wx.TE_READONLY)

        wx.StaticText(self, label="HMI Screen ROI : ", pos=(835,275))
        self.hmi_roi = wx.TextCtrl(self, pos=(835,295), size=(200,25), style=wx.TE_READONLY)
        ROI=wx.Button(self,1, "ROI",pos=(1040,295), size=(50,25))
        ROI.Bind(wx.EVT_BUTTON,self.onROI)

        wx.StaticText(self, label="Sliced Image : ", pos=(835, 330))
        self.golden_bmp = wx.Image(goldenpath,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.imageGolden = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(self.golden_bmp), pos=(835, 350))

        self.sliced_img_txt = wx.TextCtrl(self, pos=(835, 515), size=(200, 25), style=wx.TE_LEFT)
        sliced_img_save = wx.Button(self, 1, "SAVE", pos=(1040, 515), size=(50, 25))
        sliced_img_save.Bind(wx.EVT_BUTTON,self.onSave)

    def onGoldenImgSelect(self, event):
        dialog = wx.FileDialog(None, "Choose Golden Image file")
        if dialog.ShowModal() == wx.ID_OK:
            self.golden_path = (dialog.GetPath())
            self.golden_img_path.SetValue(self.golden_path)
        dialog.Destroy() 

    def onHMIImgSelect(self, event):
        dialog = wx.FileDialog(None, "Choose HMI Image file")
        if dialog.ShowModal() == wx.ID_OK:
            self.hmi_path = (dialog.GetPath())
            self.hmi_screen_path.SetValue(self.hmi_path)
        dialog.Destroy()

    def onLocate(self, event):
        him_area = [[0,0], [0,0]]
        
        try:
            him_roi_area = self.hmi_roi.GetValue().split(",")

            him_area[0][0] = int(him_roi_area[0])
            him_area[0][1] = int(him_roi_area[1])
            him_area[1][0] = int(him_roi_area[2])
            him_area[1][1] = int(him_roi_area[3])

        except:
            him_area = None
        
        him_area = None
        self.bmp_hmi = wx.Image(self.hmi_path, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        dc = wx.MemoryDC(self.bmp_hmi)
        dc.SetPen(wx.Pen('red', 5, wx.SOLID))
        dc.SetBrush(wx.Brush('red', wx.TRANSPARENT))
        c = self.gil.get_img_cordinates(self.hmi_path, self.golden_path, him_area)

        him_area_1 = [[0,0], [0,0]] if him_area==None else him_area

        golden_img = wx.Image(self.golden_path, wx.BITMAP_TYPE_ANY)
        w = golden_img.GetWidth()
        h = golden_img.GetHeight()

        try:
            x = c[0]+him_area_1[0][0]
            y = c[1]+him_area_1[0][1]

            x1 = x-w/2
            y1 = y-h/2
            dc.DrawRectangle(x1, y1, w, h)
            dc.DrawRectangle(c[0]+him_area_1[0][0], c[1]+him_area_1[0][1], 2, 2)

            self.golden_cordinate.SetValue(str(x)+' , '+ str(y))
        except:
            print ("GOLDEN IMAGES ARE NOT MATCHED....")

        self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.bmp_hmi))
        self.Refresh()
##        self.mainSizer.Fit(self.frame)

    def onROI(self,event):
        IMAGE_FILE_LOCATION = self.hmi_path

        # image read
        input_img = cv2.imread(IMAGE_FILE_LOCATION)

        # GrayScale Conversion for the Canny Algorithm
        img_gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)

        # initializing the list for storing the coordinates
        coordinates = []

        def shape_selection(event, x, y, flags, param):
            # making coordinates global
            global coordinates

            # Storing the (x1,y1) coordinates when left mouse button is pressed
            if event == cv2.EVENT_LBUTTONDOWN:
                coordinates = [(x, y)]

                # Storing the (x2,y2) coordinates when the left mouse button is released and make a rectangle on the selected region
            elif event == cv2.EVENT_LBUTTONUP:
                coordinates.append((x, y))
                x = coordinates[0][0]
                y = coordinates[0][1]
                x1 = coordinates[1][0]
                y1 = coordinates[1][1]

                self.hmi_roi.SetValue(str(x) + ' , ' + str(y) + ' , ' + str(x1) + ' , ' + str(y1))

                # Drawing a rectangle around the region of interest (roi)
                cv2.rectangle(image, coordinates[0], coordinates[1], (0, 0, 255), 2)
                cv2.imshow("image", image)

                #self.sliced_img = image[coordinates[0][1]:coordinates[1][1],coordinates[0][0]:coordinates[1][0]]
                self.sliced_img = image[y+2:y1-2, x+2:x1-2]
                temp = tempfile.gettempdir()
                filename = temp + "\\{}.jpg".format("sliced_img")
                cv2.imwrite(filename,self.sliced_img)

                self.bmp_golden = wx.Image(filename, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
                self.imageGolden.SetBitmap(wx.BitmapFromImage(self.bmp_golden))
                self.sliced_img_txt.SetValue("sliced_golden_img.jpg")
                self.Refresh()

        image = input_img
        image_copy = image.copy()
        cv2.namedWindow("image")
        cv2.setMouseCallback("image", shape_selection)

        while True:
            # display the image and wait for a keypress
            cv2.imshow("image", image)
            key = cv2.waitKey(1) & 0xFF

            if key == 13:  # If 'enter' is pressed, apply OCR
                break

            if key == ord("c"):  # Clear the selection when 'c' is pressed
                image = image_copy.copy()

        if len(coordinates) == 2:
            image_roi = image_copy[coordinates[0][1]:coordinates[1][1],
                        coordinates[0][0]:coordinates[1][0]]
            cv2.imshow("Selected Region of Interest - Press any key to proceed", image_roi)
            cv2.waitKey(0)

        # closing all open windows
        cv2.destroyAllWindows()

    def onSave(self,event):
        temp = tempfile.gettempdir()
        sliced_golden_img = temp + "\\{}.jpg".format("sliced_img")
        print(self.golden_app_path)
        print(self.sliced_img_txt.GetValue())
        golden_img = self.golden_app_path + "\\" + self.sliced_img_txt.GetValue()
        print(golden_img)
        shutil.move(sliced_golden_img,golden_img)


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

class GILocator():
    
    def __init__(self):
                
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
            
       
        self.globals = Globals.GlobalsObjects()
            
        self.globals.set_global_cfg(configs)
        
        self.globals.create_logger(os.getcwd()) 
        self.logger = self.globals.logger

        
        self.img_base = Library.BaseImageManager.BaseImageManager(self.globals)
        

         
    def get_img_cordinates(self, hmi, gi, him_area1):
        
        return self.img_base.get_image_cordinates(hmi, gi, him_area=him_area1)




        





""" The class 'HomeScreen' contains the implementation of Home Screen.
"""
class HomeScreen(GlobalTab):

    def __init__(self, parent):
        GlobalTab.__init__(self, parent)

        wx.StaticBox(self, wx.ID_ANY, "Load Inputs", pos=(25, 80), size=(640, 180))

        self.__load_controls()

    def __load_controls(self):
        wx.StaticText(self, label="Select the HMI Project Base Folder : ", pos=(55,115))
        self.project_browse_path = wx.TextCtrl(self, pos=(280,112), size=(250,25), style=wx.TE_READONLY)
        project_browse_button=wx.Button(self,1, "Browse",pos=(540,112), size=(50,25))
        project_browse_button.Bind(wx.EVT_BUTTON,self.onHMIProjectSelection)


        wx.StaticText(self, label="Select the Folder for Compiled Project : ", pos=(55,155))
        self.com_project_browse_path = wx.TextCtrl(self, pos=(280,152), size=(250,25), style=wx.TE_READONLY)
        com_project_browse_button=wx.Button(self,1, "Browse",pos=(540,152), size=(50,25))
        com_project_browse_button.Bind(wx.EVT_BUTTON,self.onHMICompiledProjectSelection)

        compile_button=wx.Button(self,1, "Compile",pos=(55,192), size=(80,50))
        compile_button.Bind(wx.EVT_BUTTON,self.onCompile)


    def onHMIProjectSelection(self, event):
        dialog = wx.DirDialog(None, "Choose Project Main Folder :")
        if dialog.ShowModal() == wx.ID_OK:
            self.project_folder = (dialog.GetPath())
            self.project_browse_path.SetValue(self.project_folder)
        dialog.Destroy()

    def onHMICompiledProjectSelection(self, event):
        dialog = wx.DirDialog(None, "Choose Folder for Compiled Project :")
        if dialog.ShowModal() == wx.ID_OK:
            self.com_project_folder = (dialog.GetPath())
            self.com_project_browse_path.SetValue(self.com_project_folder)
        dialog.Destroy()

    def onCompile(self, event):
        files_folder_path = []
        exceptional_folders = ['.git', '.gitignore', '.project', '.pydevproject', 'Report', 'hmi_test.log', '__pycache__']    
        for root, fold, files in os.walk(self.project_folder):
            if len(list(set(root.split("\\")) & set(exceptional_folders)))==0:
                for file_e in files:
                    if file_e not in exceptional_folders:
                        file_path = os.path.join(root, file_e)
                        files_folder_path.append([file_path, file_path.split(self.project_folder)[1]])
                        

        for each_file in files_folder_path:
            partial_file = "\\".join(each_file[1].split("\\")[1:])
            source = each_file[0]
            destination = os.path.join(self.com_project_folder, partial_file)
            if not os.path.isdir(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            
            if ".py" in source:
                py_compile.compile(source, destination+"c")
            else:
                shutil.copy(source, destination)
                    
            




if __name__ == '__main__':
    app=wx.App()
    c = SprintPlanner(None, -1, 'HMI Automation Tools')
    c.Show(True)
    app.MainLoop()

