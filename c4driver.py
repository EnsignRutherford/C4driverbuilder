"""
Initially published on github on March 9, 2021
Updated January 5th, 2022 

This python program will allow you to use a custom icon in the Control4 Scenario Experience Button.
It does this by taking the original driver with plain buttons and replaces the image files used
for the icons.

Pre-requisites:  Python3, and an image file.  You must also have the packages 'Pillow' and 'wget' installed.  
If you get an error saying ModuleNotFoundError: No module named 'PIL' then from the command line 
type python3 -m pip install pillow

I have tried this on Windows 10, Linux and Ubuntu on Win10 using SFU. I think it should work on a Mac as well.
The driver can be downloaded from http://drivers.control4.com/experience-button-scenario.c4z

You need at least one png image file that will be used for the new icon. If desired, you can also provide a second
image file that is the selected version of this button. Let's assume the default icon image file is called stones.png. 
Then you could also have an image file for the selected button which must be named stones_selected.png and it must be 
in the same folder.

The main image file must be a png file and ideally it should be square and 1024x1024 or larger.

Place the image file(s) in a folder along with this file.  If needed for first-time creation the script will download
the experience-button-scenario.c4z file.

Run the program with: "python3 c4driver.py stones" assuming that the image file is stones.png.
The program should just take a few seconds to run.  You should end up with an additonal file in that folder
called uibutton_stones.c4z.  This is a control4 driver file.  Have your dealer install this in the room and give it 
the name you want to be displayed in the Navigator. This script will create a log file with info in this 
example uibutton_stones.log

For more info on how to alter a driver to use your own custom icons see the following Youtube
video: https://www.youtube.com/watch?v=wW-eOh3sWFM&t=95s

Recommendations: - Your icon will look best if you do some preparation. Try to find a file with a transparent 
background. Use image editing software (I use paint.net which is free) to make this file square. If your image
file is smaller than 1024x1024 then it will have to be stretched and may not look very good. You can also make
a selected icon.  This is the icon that will appear after you push the custom experience button.

"""


""" Imports and dependencies """
import glob
import logging
import PIL
import os
import re
import shutil
import sys
import wget
import zipfile 
from datetime import datetime
from pathlib import Path
from PIL import Image


""" Constants """
DRIVER_FILE_EXTENSION = "c4z"
DRIVER_XML_FILE = "driver.xml"
EXPERIENCE_BUTTON_SCENARIO_DRIVER_URL = "http://drivers.control4.com/experience-button-scenario.c4z"
IMAGE_FILE_EXTENSION = "png"
TEMPLATE_DRIVER_FILE = "experience-button-scenario.c4z"
ZIP_FILE_EXTENSION = "zip"


""" Global variables """
LOGGING = logging.getLogger()


def configure_logging(logging_file: str) -> None:
    global LOGGING
    LOGGING.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%m-%d-%y %H:%M:%S')
    file_handler = logging.FileHandler(logging_file + ".log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    LOGGING.addHandler(file_handler)
    

def make_image_files(infile: str, outfileprefix: str) -> None:
    im = Image.open(infile)                                                                                         # Maybe check for valid filename
    LOGGING.info("Using image file: " + infile + " - image format is: " + im.format + ", size is:" + str(im.size))
    sizelist=[16, 32, 70, 90, 300, 512, 1024]                                                                       # Sizes in pixels of image files to be created
    for sz in sizelist:
        size = (sz, sz)
        outfile = outfileprefix + "_" + str(sz) + "." + IMAGE_FILE_EXTENSION                                        # Outfile prefix will be default or selected
        LOGGING.info("Creating: " + outfile)
        if infile != outfile:
                try:
                    new_image=im.resize(size)
                    new_image.save(outfile, IMAGE_FILE_EXTENSION)
                except OSError:
                    print("cannot create resized image for", infile)
                    LOGGING.error("cannot create resized image for" + infile)
  

def process_xml_file(file_name: str, driver_name: str, driver_label: str, update_driver: bool) -> None: 
    now = datetime.now()
    current_time = now.strftime("%m/%d/%Y %H:%M")

    xml1 = "<created>.*</created>"                                                                                  # This is to change the created date with current date/time see https://stackoverflow.com/questions/16159969/replace-all-text-between-2-strings-python
    xml2 = "<modified>.*</modified>"                                                                                # This is to change the modified date with current date/time
    xml3 = "<version>(.*)</version>"                                                                                # This is to change the version of the driver for ease of updating within a Control4 project
    c = "<created>" + current_time + "</created>"
    m = "<modified>" + current_time + "</modified>"
    
    data = open(file_name, 'rt', encoding='utf8', errors='ignore').read()
    data = data.encode().decode("ascii", "ignore")
    if (update_driver == False):
        stext = "experience-button-scenario"                                                                        # driver name used for files
        stext2 = "Scenario - Experience Button"                                                                     # driver name that is hard coded - replace 'Scenario' with the name of the image
        stext3 = 'name="Scenario"'
        rtext = driver_name
        rtext2 = driver_label.title().replace('_', ' ') + " - Experience Button"
        data = data.replace(stext, rtext)                                                                           # replaces the names of all of the icon files
        data = data.replace(stext2, rtext2)                                                                         # replaces the name of the driver
        data = data.replace(stext3, 'name="' + driver_label.title().replace('_', ' ') + '"')                        # replaces the name of the driver so it's default description in system explorer will be the name of the driver
    data=re.sub(xml1, c, data, flags = re.DOTALL)                                                                   # replaces the created date
    data=re.sub(xml2, m, data, flags = re.DOTALL)                                                                   # replaces the modified date
    version_info = re.search(xml3, data).group(0)                                                                   # update the version
    version = re.findall(xml3, version_info)[0]
    new_version_info = '<version>{0}</version>'.format(int(version) + 1)
    data = data.replace(version_info, new_version_info)
    fin = open(file_name, "wt")                                                                                     # open xml file to write
    fin.write(data)                                                                                                 # write updated xml file
    fin.close()


def main() -> None:
    if len(sys.argv) < 2:
        print ()
        sys.exit("No filename provided for image file. Please provide an image name as an argument.  Aborting.")

    # Define constants
    orig_driver_name = TEMPLATE_DRIVER_FILE                                                                         # This file must exist in the base folder
    outdir = "tempdir"                                                                                              # Temporary folder to hold unzipped original C4Z file and image files.
    image_path = "temp_image"                                                                                       # Temporary folder to hold all of the icon files
    driver_name = sys.argv[1]                                                                                       # The icon file name passed in the command line
    driver_label = driver_name
    orig_image_file = driver_name + "." + IMAGE_FILE_EXTENSION                                                      # This is the original image file which must be provided and it must be "driver_name".png
    base_selected_file = driver_name + "_selected." + IMAGE_FILE_EXTENSION                                          # This is the provided selected file that will be used, it is optional
    final_c4z_image_path = "uibutton_" + driver_name
    driver_name = final_c4z_image_path
    final_c4z_image_file_name = final_c4z_image_path + "." + DRIVER_FILE_EXTENSION
    final_c4z_file = final_c4z_image_path + "." + DRIVER_FILE_EXTENSION

    configure_logging(driver_name)
    LOGGING.info("Started script execution.")

    if (not os.path.exists(orig_image_file)):
        mesg = "No image file called '{0}' in current directory.  Aborting.".format(orig_image_file)
        LOGGING.error(mesg)
        sys.exit(mesg)

    if (os.path.exists(final_c4z_file)):
        orig_driver_name = final_c4z_file
        mesg = "Updating existing driver file {0}.".format(final_c4z_file)
        print(mesg)
        LOGGING.info(mesg)
        update_driver = True
    else:
        wget.download(EXPERIENCE_BUTTON_SCENARIO_DRIVER_URL, bar = None, out = orig_driver_name)    
        if not(os.path.exists(orig_driver_name)):
            sys.exit("No file called experience-button-scenario.c4z in current directory.  Aborting.")
        mesg = "Creating driver file {0}.".format(final_c4z_file)
        print(mesg)
        LOGGING.info(mesg)        
        update_driver = False

    if not(os.path.exists(base_selected_file)):                                                                    # Look to see if there is a selected file
        base_selected_file=orig_image_file                                                                         # If there isn't then just use the default file
        LOGGING.info("No selected image file so using the same image file for both default and selected")
        
    xml_file_name = os.path.join(outdir, DRIVER_XML_FILE)                                                          # This is the driver file with xml code - it will be slightly altered
    Path(image_path).mkdir(parents = True, exist_ok = True)                                                        # Create the temporaty folder for the icon files
    default_image_path = os.path.join(image_path, "default")                                                       # Path name for selected icon images
    selected_image_path = os.path.join(image_path, "selected")                                                     # Path name for default icon images

    make_image_files(orig_image_file, default_image_path)                                                          # Make all of the default files
    make_image_files(base_selected_file, selected_image_path)                                                      # Make all of the selected files

    zipfile.ZipFile(orig_driver_name).extractall(path = outdir)                                                    # Extracts driver file to the path given
    process_xml_file(xml_file_name, driver_name, driver_label, update_driver)                                      # Processes xml to change icon names for buttons and xml parameters - name, created and modified
    old_icon_path=os.path.join(outdir, "www", "icons-old")
    if (os.path.exists(old_icon_path)):
        shutil.rmtree(old_icon_path)                                                                               # Remove icons-old folder if it exists - no one knows why this folder exists - lazy coder?
    shutil.move(os.path.join(image_path, "default_16.png"), os.path.join(outdir, "www", "icons", "device_sm.png")) # Move the device small icon to the driver file
    shutil.move(os.path.join(image_path, "default_32.png"), os.path.join(outdir, "www", "icons", "device_lg.png")) # Move the device large icon to the driver file
    os.remove(os.path.join(image_path, "selected_16.png"))                                                         # These files weren't needed but it was easier to create them in a loop and then delete
    os.remove(os.path.join(image_path, "selected_32.png"))                                                         # These files weren't needed but it was easier to create them in a loop and then delete
    def_files = glob.glob(os.path.join(image_path, "default_*.png"))                                               # This is a list of all of the default image files 
    sel_files = glob.glob(os.path.join(image_path, "selected*.png"))                                               # This is all of the selected image files
    for file in def_files + sel_files:
        shutil.copy(file,os.path.join(outdir, "www", "icons", "device"))                                           # Copy all of the icon files to the proper folder
    shutil.rmtree(image_path)                                                                                      # Remove the temporary folder for the resized image files
    shutil.make_archive(driver_name, ZIP_FILE_EXTENSION, os.path.join(os.getcwd(), outdir))                        # Make the zip file, have to use zip as an extension
    shutil.rmtree(outdir)                                                                                          # Remove the folder for the resized image files
    shutil.move(driver_name + "." + ZIP_FILE_EXTENSION, final_c4z_image_file_name)                                 # Rename zip to final driver name
    if (update_driver == False):
        os.remove(orig_driver_name)
        LOGGING.info(final_c4z_image_file_name + " driver file created.")
    else:
        LOGGING.info(final_c4z_image_file_name + " driver file updated.")
    LOGGING.info("Finished script execution.")

""" Main program execution starts here. """
if __name__ == "__main__":
    main()
    
