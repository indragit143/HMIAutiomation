
import time
import os

from Library.Globals import base_path
import Library.BaseImageManager

import datetime

def delay(time_in_sec=1):
    print ("Introducing the Delay of {} sec in the execution.".format(time_in_sec))
    time.sleep(time_in_sec)
    return True

def get_formatted_post_test_delay():   
    time_in_str = Library.Globals.global_cfg['post_test_delay']
    post_test_delay = 2 if int(time_in_str)<=2 else int(time_in_str)
    print ("The execution is waiting on POST Test Delay of %s seconds."%str(post_test_delay))
    delay(post_test_delay)
    print ("Successfully completed the POST Test Delay of %s seconds."%str(post_test_delay))
    return True
    
    
def get_time_diff(initial_time, final_time):
        execution_time_in_sec = (final_time - initial_time).total_seconds()        
        minutes, seconds = divmod(execution_time_in_sec, 60)
        hours, minutes = divmod(minutes, 60)
        return {'hour' : str(int(hours)), 'minutes' : str(int(minutes)), 'seconds' : str(int(seconds))}
    

def get_datetime_for_report_folder():
    date_now = datetime.datetime.now()
    return str(date_now.day)+"_"+str(date_now.month)+"_"+str(date_now.year)+"_"+\
        str(date_now.hour)+"_"+str(date_now.minute)+"_"+str(date_now.second)