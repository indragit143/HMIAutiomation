#Introduction

this is the interim release of the HMI test automation solution for initial feedback.
this has most of the basic functionalities built into it and one will be able to execute tests without any issues
the same framework is being used for varifying the test scripts, however, the release hasnt been completely tested for all its functionalities
OCR functionality hasnt been implemented

#Requirements

test scripts can be executed from a csv file and the framework displays the execution flow and generates test report

#Recommended modules

OCR module hasnt been implemented, most other functionalities are available

Keywords Implemented:

CLICK - clicks on any control in HMI GUI based on Golden Image in whole / particular region of HMI.
verify_img - Verify HMI screen with Golder Image in whole / particular region of HMI
verify_exp_img - Verify HMI screen with Golder Image in whole / particular region of HMI.


#Installation

Pre-requisites
Make sure Python 3.6 or above is installed in your system. Solution is developed and tested with Python 3.8
Install all dependent python libraries by executing following command from cmdline using requirement.txt file.

pip install -r <full path of requirement.txt>

#Test configuration

Make sure device details are updated in config.cfg file under Device Section in config folder.
Make sure test case csv is updated with value True in tests.cfg file in config folder.

Input Files:
<testcase>.csv - Test Case file where manual test steps are converted in solution specific english based scripting.

CO_Repo.csv - Control Repository file where all unique test steps controls details are provided by image file name, text, ROI and occurance. Image/Text is mandatory. ROI & Occcurance is optional.

App_1 - Control Image repository folder where all golden images are stored.

#Troubleshooting

please contact Applic Solutions in case of any issues









