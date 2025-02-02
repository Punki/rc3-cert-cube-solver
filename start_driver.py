#!/usr/bin/env python3

#
# Starts Selenium Chrome webdriver (ie. opens a Chrome window which remains open).
# Opens the maze website in that browser window, so that the user can manually log in etc.
#
# The Selenium connection details of the browser window are displayed on terminal,
# and can be manually passed to the actual bot script which will then use this browser window.
#


import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <URL for some room in the maze>" % sys.argv[0])
        sys.exit(1)

    startUrl = sys.argv[1]

    # disable camera, microphone etc. (to prevent popups asking for permission):
    opt = Options()
    opt.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 2,
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "profile.default_content_setting_values.notifications": 2
    })


    #driver = webdriver.Chrome(chrome_options=opt) #Old Working one..
    driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=opt)
    driver.get(startUrl)

    print(f"driver URL: {driver.command_executor._url}")
    print("driver session:", driver.session_id)

    # keep running, so the browser window stays open:
    while True:
        time.sleep(1)
