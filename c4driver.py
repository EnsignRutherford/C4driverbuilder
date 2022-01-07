"""
Initially published on github on March 9, 2021
Updated January 5th, 2022 

This python program will allow you to use a custom icon in the Control4 Scenario Experience Button.
It does this by taking the original driver with plain buttons and replaces the image files used
for the icons.

Pre-requisites:  Python3, and an image file.  If the necessary package requirements are not installed the user
will be prompted to install them.

You need at least one png image file that will be used for the new icon. If desired, you can also provide a second
image file that is the selected version of this button. Let's assume the default icon image file is called stones.png. 
Then you could also have an image file for the selected button which must be named stones_selected.png, and it must be
in the same folder.

The main image file must be a png file, and ideally it should be square and 1024x1024 or larger.

Place the image file(s) in a folder along with this file.  If needed for first-time creation the script will download
the experience-button-scenario.c4z file.

Run the program with: "python3 c4driver.py stones" assuming that the image file is stones.png.
The program should just take a few seconds to run.  You should end up with an additional file in that folder
called uibutton_stones.c4z.  This is a control4 driver file.  Have your dealer install this in the room and give it 
the name you want to be displayed in the Navigator. This script will create a log file with info in this 
example uibutton_stones.log

For more info on how to alter a driver to use your own custom icons see the YouTube video:
https://www.youtube.com/watch?v=wW-eOh3sWFM&t=95s

Recommendations: - Your icon will look best if you do some preparation. Try to find a file with a transparent 
background. Use image editing software (I use paint.net which is free) to make this file square. If your image
file is smaller than 1024x1024 then it will have to be stretched and may not look very good. You can also make
a selected icon.  This is the icon that will appear after you push the custom experience button.

"""


""" Imports and dependencies """
import logging
try:
    import PIL
except ImportError:
    print("Pillow Library not installed.\nType 'python3 -m pip install pillow' at the command prompt and try again.")
    quit()
import os
import shutil
import sys
try:
    import wget
except ImportError:
    wget = None
    print("wget Library not installed.\nType 'python3 -m pip install wget' at the command prompt and try again.")
    quit()
import zipfile
from datetime import datetime

try:
    from lxml import etree
except ImportError:
    etree = None
    print("lxml Library not installed.\nType 'python3 -m pip install lxml' at the command prompt and try again.")
    quit()
from pathlib import Path
from PIL import Image


""" Constants """
DRIVER_FILE_EXTENSION = "c4z"
DRIVER_XML_FILE = "driver.xml"
EXPERIENCE_BUTTON_SCENARIO_DRIVER_URL = "http://drivers.control4.com/experience-button-scenario.c4z"
EXPERIENCE_BUTTON_SCENARIO_NAME = "experience-button-scenario"
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


def make_image_files(in_file: str, out_file_prefix: str) -> None:
    if os.path.exists(in_file):
        im = Image.open(in_file)
        LOGGING.info("Using image file: " + in_file + " - image format is: " + im.format + ", size is:" + str(im.size))
        size_list = [16, 32, 70, 90, 300, 512, 1024]  # Sizes in pixels of image files to be created
        for sz in size_list:
            size = (sz, sz)
            # Outfile prefix will be default or selected
            out_file = out_file_prefix + "_" + str(sz) + "." + IMAGE_FILE_EXTENSION
            LOGGING.info("Creating: " + out_file)
            if in_file != out_file:
                try:
                    new_image = im.resize(size)
                    new_image.save(out_file, IMAGE_FILE_EXTENSION)
                except OSError:
                    mesg = "Cannot create resized image for {0}.".format(in_file)
                    print(mesg)
                    LOGGING.error(mesg)


def process_xml_file(file_name: str, driver_name: str, driver_label: str, update_driver: bool) -> None:
    current_time = datetime.now().strftime("%m/%d/%Y %H:%M")  # for creation and last modified date
    tree = etree.parse(file_name)
    if update_driver:
        pass
    else:
        # replace the name of the proxy, so it appears properly when first installed
        tree.xpath("/devicedata/proxies/proxy")[0].attrib['name'] = driver_label.title().replace('_', ' ')
        # replaces the name of the driver, so it's default description in system explorer will be the name of the driver
        tree.xpath("/devicedata/name")[0].text = tree.xpath("/devicedata/proxies/proxy")[0].attrib['name'] + " - Experience Button"
        # replaces the names of the icon files
        for image_directory in tree.xpath("/devicedata/capabilities/navigator_display_option/display_icons/Icon"):
            image_directory.text = image_directory.text.replace(EXPERIENCE_BUTTON_SCENARIO_NAME, driver_name)
        for image_state in tree.xpath("/devicedata/capabilities/navigator_display_option/display_icons/state"):
            for image_directory in image_state.iter():
                image_directory.text = image_directory.text.replace(EXPERIENCE_BUTTON_SCENARIO_NAME, driver_name)
    tree.xpath("/devicedata/created")[0].text = current_time  # replaces the created date
    tree.xpath("/devicedata/modified")[0].text = current_time  # replaces the modified
    tree.xpath("/devicedata/version")[0].text = str(int(tree.xpath("/devicedata/version")[0].text) + 1)  # update the version
    tree.write(file_name, pretty_print=True, xml_declaration=True, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print()
        sys.exit("No filename provided for image file. Please provide an image name as an argument.  Aborting.")

    # Define constants
    orig_driver_name = TEMPLATE_DRIVER_FILE  # This file must exist in the base folder
    out_dir = "tempdir"  # Temporary folder to hold unzipped original C4Z file and image files.
    image_path = "temp_image"  # Temporary folder to hold the icon files
    driver_name = sys.argv[1]  # The icon file name passed in the command line
    driver_label = driver_name
    orig_image_file = driver_name + "." + IMAGE_FILE_EXTENSION  # This is the original image file
    base_selected_file = driver_name + "_selected." + IMAGE_FILE_EXTENSION  # This is the provided selected file that will be used, it is optional
    final_c4z_image_path = "uibutton_" + driver_name
    driver_name = final_c4z_image_path
    final_c4z_image_file_name = final_c4z_image_path + "." + DRIVER_FILE_EXTENSION
    final_c4z_file = final_c4z_image_path + "." + DRIVER_FILE_EXTENSION
    configure_logging(driver_name)
    LOGGING.info("Started script execution.")
    if not os.path.exists(orig_image_file):
        mesg = "No image file called '{0}' in current directory.  Aborting.".format(orig_image_file)
        LOGGING.error(mesg)
        sys.exit(mesg)
    if os.path.exists(final_c4z_file):
        orig_driver_name = final_c4z_file
        mesg = "Updating existing driver file {0}.".format(final_c4z_file)
        print(mesg)
        LOGGING.info(mesg)
        update_driver = True
    else:
        wget.download(EXPERIENCE_BUTTON_SCENARIO_DRIVER_URL, bar=None, out=orig_driver_name)
        if not (os.path.exists(orig_driver_name)):
            sys.exit("No file called experience-button-scenario.c4z in current directory.  Aborting.")
        mesg = "Creating driver file {0}.".format(final_c4z_file)
        print(mesg)
        LOGGING.info(mesg)
        update_driver = False
    if not (os.path.exists(base_selected_file)):  # Look to see if there is a selected file
        base_selected_file = orig_image_file  # If there isn't then just use the default file
        LOGGING.info("No selected image file so using the same image file for both default and selected")
    # This is the driver file with xml code - it will be slightly altered
    xml_file_name = os.path.join(out_dir, DRIVER_XML_FILE)
    Path(image_path).mkdir(parents=True, exist_ok=True)  # Create the temporary folder for the icon files
    default_image_path = os.path.join(image_path, "default")  # Path name for selected icon images
    selected_image_path = os.path.join(image_path, "selected")  # Path name for default icon images
    make_image_files(orig_image_file, default_image_path)  # Make all the default files
    make_image_files(base_selected_file, selected_image_path)  # Make all the selected files
    zipfile.ZipFile(orig_driver_name).extractall(path=out_dir)  # Extracts driver file to the path given
    # Processes xml to change icon names for buttons and xml parameters - name, created and modified
    process_xml_file(xml_file_name, driver_name, driver_label, update_driver)
    old_icon_path = os.path.join(out_dir, "www", "icons-old")
    if os.path.exists(old_icon_path):
        shutil.rmtree(old_icon_path)  # Remove icons-old folder if it exists - no one knows why this folder exists - lazy coder?
    # Move the device small and large icons to the driver file
    shutil.move(os.path.join(image_path, "default_16.png"), os.path.join(out_dir, "www", "icons", "device_sm.png"))
    shutil.move(os.path.join(image_path, "default_32.png"), os.path.join(out_dir, "www", "icons", "device_lg.png"))
    # These files weren't needed; it was easier to create them in a loop and then delete
    os.remove(os.path.join(image_path, "selected_16.png"))
    os.remove(os.path.join(image_path, "selected_32.png"))
    # Copy all the icon files to the proper folder
    for file in Path(image_path).glob("*." + IMAGE_FILE_EXTENSION):
        shutil.copy(file, os.path.join(out_dir, "www", "icons", "device"))
    shutil.rmtree(image_path)  # Remove the temporary folder for the resized image files
    # Make the zip file, have to use zip as an extension
    shutil.make_archive(driver_name, ZIP_FILE_EXTENSION, os.path.join(os.getcwd(), out_dir))
    shutil.rmtree(out_dir)  # Remove the folder for the resized image files
    shutil.move(driver_name + "." + ZIP_FILE_EXTENSION, final_c4z_image_file_name)  # Rename zip to final driver name
    if not update_driver:
        os.remove(orig_driver_name)
        LOGGING.info(final_c4z_image_file_name + " driver file created.")
    else:
        LOGGING.info(final_c4z_image_file_name + " driver file updated.")
    LOGGING.info("Finished script execution.")


""" Main program execution starts here. """
if __name__ == "__main__":
    main()
