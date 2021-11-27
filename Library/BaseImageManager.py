
"""
Base Image Manager Library implements the Basic Image Processing on the Device Screen.
@author      : Siva 
@date        : 25-Apr-2021

@modified    : Vinayak Rao, vinayak.rao@applicsolutions.com
@modified on : 02-May-2021
"""

import os
import cv2 as cv
import numpy as np
from pathlib import Path


class BaseImageManager():
    def __init__(self, global_obj):
        self.global_obj = global_obj
        self.logger = self.global_obj.logger
                
    def __is_him_image_exists(self, him_image_path):
        if not os.path.isfile(him_image_path):
            self.logger.error("HMI image does not exist in the path : [%s]"%str(him_image_path))
            raise FileNotFoundError('HIM Image File Path Does not Exist')
        else:
            self.logger.debug("HMI image is found in the path [%s]"%str(him_image_path))
        him_image = cv.imread(him_image_path)
        return him_image

    def __is_golden_image_exists(self, golden_image_path):
        if not os.path.isfile(golden_image_path):
            self.logger.error("Golden image does not exist in the path : [%s]"%str(golden_image_path))
            raise FileNotFoundError('Golden Image File Path Does not Exist')
        else:
            self.logger.debug("Golden image is found in the path [%s]"%str(golden_image_path))
        golden_image = cv.imread(golden_image_path)
        return golden_image

    def get_image_cordinates(self, him_image_path, golden_image_path, coordinate_loc=None, scale_factor=1,
                                 threshold=0.9, occurance=1, image_is_text=True, him_area=None):
        logger_message = "Trying to match the golden image <{}> on HMI image <{}> with below parameters : \n"
        logger_message+= "coordinate_loc : {}, \nscale_factor : {}, \nthreshold : {}, \noccurance : {}, \nimage_is_text : {}, \nhim_area : {}"
        
        self.logger.debug(logger_message.format(Path(golden_image_path).name, Path(him_image_path).name, 
                                                                  coordinate_loc,
                                                                  scale_factor, threshold, occurance,
                                                                  image_is_text, him_area))
        self.logger.debug("Trying to get the image coordinates in the HMI Image.")
        him_image = self.__is_him_image_exists(him_image_path)
        
        """Converting HMI live image to RGB format"""
        him_image = cv.cvtColor(him_image,cv.COLOR_BGR2RGB)
        
        him_image2 = him_image.copy()
        golden_image = self.__is_golden_image_exists(golden_image_path)        
        w, h = golden_image.shape[1::-1]
        self.logger.debug("The width and height of golden image is [Width - %s, Height - %s]"%(str(w), str(h)))
        
        if him_area != None:
            sliced_him_image = him_image[him_area[0][1]:him_area[1][1], him_area[0][0]:him_area[1][0]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]"%(str(sliced_w), str(sliced_h)))           
            if w <= sliced_w and h <= sliced_h:
                method = eval('cv.TM_CCOEFF_NORMED')
                res = cv.matchTemplate(sliced_him_image, golden_image, method)
                (yCoords, xCoords) = np.where(res >= threshold)                
            else:
                self.logger.error("The height and width of golden image is greater then ROI image obtained in the HMI image")
                return 2
        else: 
            method = eval('cv.TM_CCOEFF_NORMED')
            res = cv.matchTemplate(him_image, golden_image, method)
            (yCoords, xCoords) = np.where(res >= threshold)
        self.logger.debug("[INFO] {} matched locations *before* NMS".format(len(yCoords)))

        """ Initialize the list of rectangles """
        rects = []
        
        """ loop over the starting (x, y)-coordinates again """
        for (x, y) in zip(xCoords, yCoords):
            
            """ Update our list of rectangles """
            rects.append((x, y, x + w, y + h))
            
        # apply non-maxima suppression to the rectangles
        pick = self.non_max_suppression(np.array(rects))
        self.logger.debug("[INFO] {} matched locations *after* NMS".format(len(pick)))

        if len(pick) == 0:
            self.logger.debug("The coordinates are not obtained in the HMI image from the golden image : [%s]"%str(golden_image_path))
            return 2
        else:
            pick = np.flip(pick,axis=0)
            cv.rectangle(him_image2, (pick[occurance-1,0],pick[occurance-1,1]), (pick[occurance-1,2],pick[occurance-1,3]), (255, 0, 0), 3)            
            
            if coordinate_loc == "LEFT":
                xLeft = pick[occurance-1,0]
                yLeft = (pick[occurance-1,1] + pick[occurance-1,3])/ 2
                xLeft = round(xLeft)
                yLeft = round(yLeft)
                self.logger.debug("The LEFT coordinates [%s, %s] are found in HMI image by matching the golden image [%s]."%(str(xLeft),
                                                                                                                        str(yLeft),
                                                                                                                        str(golden_image_path)))
                cv.putText(him_image2, str(xLeft) + ',' +
                    str(yLeft), (xLeft,yLeft), cv.FONT_HERSHEY_PLAIN,
                    1, (255, 0, 0), 2)                                
                return [xLeft,yLeft]
            elif coordinate_loc == "RIGHT":
                xRight = pick[occurance-1,2]
                yRight = (pick[occurance-1,1] + pick[occurance-1,3]) / 2
                xRight = round(xRight)
                yRight = round(yRight)
                self.logger.debug("The RIGHT coordinates [%s, %s] are found in HMI image by matching the golden image [%s]."%(str(xRight),
                                                                                                                        str(yRight),
                                                                                                                        str(golden_image_path)))
                return [xRight,yRight]
            elif coordinate_loc == "TOP":
                xTop = (pick[occurance-1,0] + pick[occurance-1,2]) / 2
                yTop = pick[occurance-1,1]
                xTop = round(xTop)
                yTop = round(yTop)
                self.logger.debug("The TOP coordinates [%s, %s] are found in HMI image by matching the golden image [%s]."%(str(xTop),
                                                                                                                        str(yTop),
                                                                                                                        str(golden_image_path)))
                return [xTop,yTop]
            elif coordinate_loc == "BOTTOM":
                xBottom = (pick[occurance-1,0] + pick[occurance-1,2]) / 2
                yBottom = pick[occurance-1,3]
                xBottom = round(xBottom)
                yBottom = round(yBottom)
                self.logger.debug("The BOTTOM coordinates [%s, %s] are found in HMI image by matching the golden image [%s]."%(str(xBottom),
                                                                                                                        str(yBottom),
                                                                                                                        str(golden_image_path)))
                return [xBottom,yBottom]
            else:               
                xCenter = (pick[occurance-1,0] + pick[occurance-1,2]) / 2
                yCenter = (pick[occurance-1,1] + pick[occurance-1,3]) / 2
                xCenter = round(xCenter)
                yCenter = round(yCenter)
                self.logger.debug("The coordinates [%s, %s] are found in HMI image by matching the golden image [%s]."%(str(xCenter),
                                                                                                                        str(yCenter),
                                                                                                                        str(golden_image_path)))
                return [xCenter,yCenter]

    def non_max_suppression(self, boxes, probs=None, overlapThresh=0.3):
        # if there are no boxes, return an empty list
        if len(boxes) == 0:
            return []

        # if the bounding boxes are integers, convert them to floats -- this
        # is important since we'll be doing a bunch of divisions
        if boxes.dtype.kind == "i":
            boxes = boxes.astype("float")

        # initialize the list of picked indexes
        pick = []

        # grab the coordinates of the bounding boxes
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        # compute the area of the bounding boxes and grab the indexes to sort
        # (in the case that no probabilities are provided, simply sort on the
        # bottom-left y-coordinate)
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = y2

        # if probabilities are provided, sort on them instead
        if probs is not None:
            idxs = probs

        # sort the indexes
        idxs = np.argsort(idxs)

        # keep looping while some indexes still remain in the indexes list
        while len(idxs) > 0:
            # grab the last index in the indexes list and add the index value
            # to the list of picked indexes
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            # find the largest (x, y) coordinates for the start of the bounding
            # box and the smallest (x, y) coordinates for the end of the bounding
            # box
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])

            # compute the width and height of the bounding box
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)

            # compute the ratio of overlap
            overlap = (w * h) / area[idxs[:last]]

            # delete all indexes from the index list that have overlap greater
            # than the provided overlap threshold
            idxs = np.delete(idxs, np.concatenate(([last],
                                                   np.where(overlap > overlapThresh)[0])))

        # return only the bounding boxes that were picked
        return boxes[pick].astype("int")
    
    def verify_image(self, him_image_path, golden_image_path, coordinate_loc=None, scale_factor=1,
                                 threshold=0.8, occurance=1, image_is_text=True, him_area=[(0, 0), (100, 100)]):
        self.logger.debug("Checking if the golden image [%s] is present in the HMI image [%s]."%(str(golden_image_path), 
                                                                                                str(him_image_path)))
        him_image = self.__is_him_image_exists(him_image_path)
        him_image2 = him_image.copy()
        golden_image = self.__is_golden_image_exists(golden_image_path)
        w, h = golden_image.shape[1::-1]
        self.logger.debug("The width and height of golden image is [Width - %s, Height - %s]"%(str(w), str(h)))
        
        if him_area != None:
            sliced_him_image = him_image[him_area[0][0]:him_area[1][0],him_area[0][1]:him_area[1][1]]
            sliced_w, sliced_h = sliced_him_image.shape[1::-1]
            self.logger.debug("The width and height of ROI hmi image are [Width - %s, Height - %s]"%(str(sliced_w), str(sliced_h)))           
            if w <= sliced_w and h <= sliced_h:
                method = eval('cv.TM_CCOEFF_NORMED')
                res = cv.matchTemplate(sliced_him_image, golden_image, method)
                (yCoords, xCoords) = np.where(res >= threshold)
            else:
                self.logger.error("The height and width of golden image is greater then ROI image obtained in the HMI image")
                return 2
        
        self.logger.debug("[INFO] {} matched locations *before* NMS".format(len(yCoords)))

        # initialize our list of rectangles
        rects = []
        # loop over the starting (x, y)-coordinates again
        for (x, y) in zip(xCoords, yCoords):
            # update our list of rectangles
            rects.append((x, y, x + w, y + h))
        # apply non-maxima suppression to the rectangles
        pick = self.non_max_suppression(np.array(rects))
        self.logger.debug("[INFO] {} matched locations *after* NMS".format(len(pick)))

        if len(pick) < occurance:
            return 1
        elif len(pick) == 0:
            self.logger.error("The golden image [%s] is not found in HMI image [%s]"%(str(golden_image_path), str(him_image_path)))
            return 2
        else:
            pick = np.flip(pick,axis=0)
            cv.rectangle(him_image2, (pick[occurance-1,0],pick[occurance-1,1]), (pick[occurance-1,2],pick[occurance-1,3]), (255, 0, 0), 3)
            cv.imshow("Matched :",him_image2)
            cv.waitKey(0) 
            self.logger.info("The golden image [%s] is found in HMI image [%s]"%(str(golden_image_path), str(him_image_path)))           
            return True

    def click_coord_exists(self, him_image_path,coordxy=None):

        him_image = self.__is_him_image_exists(him_image_path)

        w, h = him_image.shape[1::-1]

        if(coordxy[0] < w and coordxy[1] < h):
            return True
        else:
            self.logger.debug("The co-ordinations [%s] [%s] is not found in the HMI image"%(str(coordxy[0]), str(coordxy[1])))
            return False

    