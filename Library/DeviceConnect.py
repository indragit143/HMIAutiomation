
"""
Device Connection Library to establish the connection with the Device and Perform the basic operations.
@author      : Siva 
@date        : 25-Apr-2021

@modified    : Vinayak Rao, vinayak.rao@applicsolutions.com
@modified on : 02-May-2021
"""

from vncdotool import api
import socket
import os
import time
from Library.Globals import base_path
from Library.Globals import main_base_path


"""
The Class to implement the Device Connections.
"""
class DeviceConnect(object):

    def __init__(self, host, port, password, globalObj):
        self.hostport = host
        self.port = port
        self.password = password
        self.globals = globalObj
        self.logger = self.globals.logger
        self.logger.debug("Device connect Constructor is created successfully.")
        

    """
    The method connect() creates the device connection.
    Args    : retry  - The attempt number if the Device COnnection Fails. 
    Returns : status - The connection object if success to create and False otherwise.
    """
    def connect(self, retry=10):
        status = False
        self.logger.debug("Attempting to create a Device connection with IP - %s, Host - %s and Password - %s"%(self.hostport,
                                                                                                                    self.port,
                                                                                                                    self.password))
        for attempt in range(0,retry):
            self.logger.debug("Trying Device Connection in Attempt  - %s time."%str(attempt+1))
            try:
                socket.inet_aton(self.hostport)
                status = api.connect(self.hostport + '::' + str(self.port), self.password)
                self.logger.debug("Successfully created the Device Connection in Attempt - %s time."%str(attempt+1))
                break
            except Exception as e:
                self.logger.error("Failed the Device Connection in Attempt  - %s time."%str(attempt+1))
                self.logger.error(e)
        return status
    
    
    """ The method Is_connection_alive() checks if the Device COnnection is alive or not.
        Args    : None
        Returns : True - If the Device Connection is Alive and False - Otherwise.
    """
    def Is_connection_alive(self):
        self.logger.debug("Checking if the Device Connection is alive!!!")
        s = socket.socket()
        status = False
        try:
            s.connect((self.hostport, self.port))
            self.logger.info("Device is connected and is alive!!")
            status = True
        except Exception as e:
            self.logger.error("The Device Connection is not Alive.")
            self.logger.error(e)
        s.close()
        return status
   
    
    """ 
    The method Get_live_image() reads the live image and stores at a specified location.
    Args    : client - The Device connection object.
    Returns : hmi_live_image_path - Path of the HMI Device Screen Image and False if Fails to get the image.
    """
    def Get_live_image(self, client):
        client.timeout = 20

        try:
            self.logger.debug("Trying to get the Device Image.")
            hmi_screen_dir = os.path.join(main_base_path, "HMI_Screens", "HMI_Screens")
            if not os.path.isdir(hmi_screen_dir):
                os.mkdir(hmi_screen_dir)
            hmi_live_image_path = os.path.join(base_path, "../", "HMI_Screens", 
                                               "HMI_Screens", 'HMI_LIVE_IMG.jpg')
            self.logger.debug(client)
            try:
                client.captureScreen(hmi_live_image_path)
            except TimeoutError:
                return False
            self.logger.debug("Successfully captured the Device Image at the Path - %s"%hmi_live_image_path)
            return hmi_live_image_path
        except Exception as e:
            self.logger.error("Failed to capture the Device Image.")
            self.logger.error(e)
            return False

    """ 
           The method Get_live_images() reads the live images for the given duration and stores at a specified location.
           Args    : client - The Device connection object.
           Returns : hmi_live_image_path - Path of the HMI Device Screen Image and False if Fails to get the image.
           """

    def Get_live_images(self, client, duration=5):
        client.timeout = 20
        try:
            self.logger.debug("Trying to get the Device Images for given duration.")
            hmi_screen_dir = os.path.join(main_base_path, "HMI_Screens", "HMI_Screens")
            if not os.path.isdir(hmi_screen_dir):
                os.mkdir(hmi_screen_dir)
            hmi_status_screen_dir = os.path.join(base_path, "../", "HMI_Screens",
                                                 "HMI_Screens", "HMI_Status_Screens")
            if not os.path.isdir(hmi_status_screen_dir):
                os.mkdir(hmi_status_screen_dir)

            start_time = time.time()
            i = 1
            while True:
                current_time = time.time()
                elapsed_time = current_time - start_time
                hmi_status_image_path = os.path.join(base_path, "../", "HMI_Screens",
                                                     "HMI_Screens", "HMI_Status_Screens", 'HMI_STATUS_IMG'+str(i)+'.jpg')
                self.logger.debug(client)
                try:
                    client.captureScreen(hmi_status_image_path)
                except TimeoutError:
                    return False
                if elapsed_time > float(duration):
                    self.logger.debug(
                        "Successfully captured the Device Status Images at the Path - %s" % hmi_status_image_path)
                    break
                i = i + 1
            return hmi_status_screen_dir
        except Exception as e:
            self.logger.error("Failed to capture the Device Status Images.")
            self.logger.error(e)
            return False

    """
    The method Is_device_exists() checks if the Device is discoverable via IP Address.
    Args    : hostport - IP of the device.
    Returns : True     - If the device is discoverable and False otherwise.
    """
    def Is_device_exists(self,hostport):
        self.logger.debug("Checking if the Device Exists!!")
        ret = os.system("ping -n 1 " + hostport)
        if ret != 0:
            self.logger.error("Device does not exists")
            return False
        else:
            self.logger.info("Device Exists after the check.")
            return True
        
        
    """
    The method disconnect() disconnects the Device connection.
    Args    : client -  The Device connection object.
    Returns : status - True if success to disconnect and False otherwise.
    """
    def disconnection(self,client):
        status = False
        self.logger.debug("Disconnect the Device.")
        try:
            self.logger.info("Success to disconnect the device.")
            status = True
        except Exception as e:
            self.logger.error("Device Disconnection Failed.")
            self.logger.error(e)
        return status
