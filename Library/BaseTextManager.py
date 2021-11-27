"""
Base Image Manager Library implements the Basic Image Processing on the Device Screen.
@author      : Siva
@date        : 07-Jun-2021

@modified    : Siva
@modified on : 19-Oct2021
"""

import os
import tempfile
from pathlib import Path

import pytesseract
import cv2 as cv

from pytesseract import Output
from Library.Globals import base_path


class BaseTextManager:
    def __init__(self,global_obj):
        self.global_obj = global_obj
        self.logger = self.global_obj.logger
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

    def verifytext(self, him_image_path, target_text, threshold_type, threshold_value, him_area=None, occurance=None,locale=None):
        verify_status = False
        curr_occur = 0

        #load the image
        him_image = cv.imread(him_image_path)

        # Convert image to BGR2grayscale
        him_image_gray = cv.cvtColor(him_image, cv.COLOR_BGR2GRAY)

        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]"%(str(sliced_w), str(sliced_h)))
            _, enhanced_img = cv.threshold(sliced_him_image, threshold_value, 255, threshold_type)
        else:
            # Image enhancement using threshold type and value
            _, enhanced_img = cv.threshold(him_image_gray, threshold_value, 255, threshold_type)

        text = pytesseract.image_to_data(enhanced_img, lang=locale, output_type=Output.DICT)
        #text = pytesseract.image_to_string(enhanced_img, lang=locale, output_type=Output.DICT)

        n_boxes = len(text['level'])

        if n_boxes > 1:
            for i in range(n_boxes):
                if text['text'][i] == target_text:
                    curr_occur = curr_occur + 1
                    if curr_occur == occurance:
                        verify_status = True
                        (x, y, w, h) = (text['left'][i], text['top'][i], text['width'][i], text['height'][i])
                        cv.rectangle(enhanced_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        self.logger.info("The Target Text [%s] is found in HMI image [%s]" % (str(target_text), str(him_image_path)))

        BaseTextManager.remove_empty_strings(self,text)

        if verify_status == True:
            temp = tempfile.gettempdir()
            filename = temp + "\\{}.jpg".format("find_text_img")
            cv.imwrite(filename, enhanced_img)
            self.logger.debug("Expected String [%s] is Found in Extracted Text [%s] from HMI" % (target_text, str(text['text'])))
        else:
            temp = tempfile.gettempdir()
            filename = temp + "\\{}.jpg".format("find_text_img_failed")
            cv.imwrite(filename, enhanced_img)
            self.logger.error("Expected String [%s] is Not Found in Extracted Text [%s] from HMI" % (target_text, str(text['text'])))
        return verify_status

    def remove_empty_strings(self, text):
        # print("Total text extracted:", text['text'])
        try:
            while True:
                text['text'].remove("")
        except ValueError:
            pass
        removed_empty = text['text']
        # print("\nRemoved Empty Strings '':", removed_empty)
        # make seperate Function
        res = []
        for ele in removed_empty:
            if ele.strip():
                res.append(ele)
        # print("\nAfter removing multiple spaces:", res)
        return res

    def count_target_text(self,target_text):
        target_text_split = list(target_text.split(" "))
        string = ""
        for i in target_text_split:
            string += " " + i
        text_conatinated = string

        return text_conatinated , target_text_split

    def verifystring(self, him_image_path, target_text, threshold_type, threshold_value, him_area=None, occurance=None, locale=None):
        # print(Color_Convertion)
        verify_status = False
        curr_occur = 0

        # load the image
        him_image = cv.imread(him_image_path)

        # Convert image to grayscale
        him_image_gray = cv.cvtColor(him_image, cv.COLOR_BGR2GRAY)

        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]" % (
            str(sliced_w), str(sliced_h)))
            _, enhanced_img = cv.threshold(sliced_him_image, threshold_value, 255, threshold_type)
        else:
            # Image enhancement using threshold type and value
            _, enhanced_img = cv.threshold(him_image_gray, threshold_value, 255, threshold_type)

        #text = pytesseract.image_to_data(enhanced_img, output_type=Output.DICT)
        text = pytesseract.image_to_data(enhanced_img, lang=locale, output_type=Output.DICT)
        self.logger.debug("Extracted Text [%s] from HMI Screen" % text)

        value_inside = BaseTextManager.remove_empty_strings(self, text)
        self.logger.debug("Extracted Text [%s] after processing for empty strings" % value_inside)

        if len(target_text) != 0:
            if len(value_inside) == 0:
                self.logger.error("Extracted text [%s] from HMI is blank" % value_inside)
            else:
                a = len(list(target_text.split(" ")))
                for i in range(0, len(value_inside)):
                    if len(str(list(target_text.split(" ")))) == len(str(value_inside[i:i + a])) and str(
                            list(target_text.split(" "))) == str(value_inside[i:i + a]):
                        verify_status = True
                        self.logger.info(
                            "Target text [%s] matched with Extracted text [%s] :)" % (target_text, value_inside))
                        break
                # if verify_status == False:
                #     self.logger.error("Target text [%s] matched with extracted text [%s]:("% (target_text, value_inside))
                else:
                    self.logger.error(
                        "Target text [%s] not matched with Extracted text [%s] :(" % (target_text, value_inside))
        else:
            self.logger.error("Target text [%s] from HMI is blank, Please check input value." % target_text)

        if verify_status == True:
            temp = tempfile.gettempdir()
            filename = temp + "\\{}.jpg".format("find_text_img")
            cv.imwrite(filename, enhanced_img)
            #self.logger.debug("Expected String [%s] is available in Extracted Text [%s] from HMI Image" % (text_conatinated, strings_concartinated))
        else:
            temp = tempfile.gettempdir()
            filename = temp + "\\{}.jpg".format("find_text_img_failed")
            cv.imwrite(filename, enhanced_img)
            #self.logger.error("Expected String [%s] is not available in Extracted Text or Text Extraction is incorrect " % text_conatinated)
        return verify_status

    def get_text_cordinates(self, hmi_image_path, target_text, threshold_type, threshold_value, him_area=None, occurance=None, locale=None):

        coordinates = None
        curr_occur = 0

        logger_message = "Trying to match the target_text <{}> on HMI image <{}> with below parameters : \n"
        logger_message += "threshold_type : {}, \nthreshold_value : {}, \nhim_area : {}, \noccurance : {}"

        self.logger.debug(logger_message.format(target_text, Path(hmi_image_path).name, threshold_type, threshold_value, him_area, occurance))
        self.logger.debug("Trying to get the Text coordinates in the HMI Image.")

        # load the image
        if os.path.isfile(hmi_image_path):
            him_image = cv.imread(hmi_image_path)
            self.logger.debug("HMI image is found in the path [%s]" % str(hmi_image_path))
        else:
            self.logger.error("HMI image does not exist in the path : [%s]" % str(hmi_image_path))
            raise FileNotFoundError('HIM Image File Path Does not Exist')

        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]"%(str(sliced_w), str(sliced_h)))

            # Convert image to grayscale
            him_image_gray = cv.cvtColor(sliced_him_image, cv.COLOR_BGR2GRAY)
        else:
            # Convert image to grayscale
            him_image_gray = cv.cvtColor(him_image, cv.COLOR_BGR2GRAY)

        # Image enhancement using threshold type and value
        _, enhanced_img = cv.threshold(him_image_gray, threshold_value, 255, threshold_type)

        text = pytesseract.image_to_data(enhanced_img, lang=locale, output_type=Output.DICT)

        n_boxes = len(text['level'])
        if n_boxes > 1:
            for i in range(n_boxes):
                if text['text'][i] == target_text:
                    curr_occur = curr_occur + 1
                    self.logger.debug("Found Occurance: [%s]" % str(curr_occur))
                    if curr_occur == occurance:
                        coordinates = (text['left'][i], text['top'][i], text['width'][i], text['height'][i])
                        cv.rectangle(enhanced_img, (coordinates[0], coordinates[1]), (coordinates[0] + coordinates[2], coordinates[1] + coordinates[3]), (0, 255, 0), 2)

                        xCenter = round((coordinates[0] + (coordinates[0] + coordinates[2]))/2)
                        yCenter = round((coordinates[1] + (coordinates[1] + coordinates[3]))/2)
                        return [xCenter, yCenter]
                        break
            return 2
        else:
            self.logger.error("Fail to extract any text from HMI Image in the path : [%s]" % str(hmi_image_path))
            return 2

    def factorypass(self, him_image_path, threshold_type, threshold_value, him_area=None):

        # load the image
        him_image = cv.imread(him_image_path)

        # Convert image to grayscale
        him_image_gray = cv.cvtColor(him_image, cv.COLOR_BGR2GRAY)

        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]" % (
                str(sliced_w), str(sliced_h)))
            _, enhanced_img = cv.threshold(sliced_him_image, threshold_value, 255, threshold_type)
        else:
            # Image enhancement using threshold type and value
            _, enhanced_img = cv.threshold(him_image_gray, threshold_value, 255, threshold_type)

        text = pytesseract.image_to_data(enhanced_img, output_type=Output.DICT)

        value_inside = BaseTextManager.remove_empty_strings(self, text)

        return value_inside

    def timestamp(self, him_image_path, threshold_type, threshold_value, him_area=None):
        Enter_status = True
        # load the image
        him_image = cv.imread(him_image_path)

        # Convert image to grayscale
        him_image_gray = cv.cvtColor(him_image, cv.COLOR_BGR2GRAY)

        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]" % (
                str(sliced_w), str(sliced_h)))
            _, enhanced_img = cv.threshold(sliced_him_image, threshold_value, 255, threshold_type)
        else:
            # Image enhancement using threshold type and value
            _, enhanced_img = cv.threshold(him_image_gray, threshold_value, 255, threshold_type)

        text = pytesseract.image_to_data(enhanced_img, output_type=Output.DICT)

        value_inside = BaseTextManager.remove_empty_strings(self, text)
        self.logger.debug("Extracted Date and Time [%s] from HIM Screen" % (value_inside))
        return Enter_status