import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import connect, tackle_wind

global browser


def webscrap_data(path_driver, date_from, date_to, logger, progress_bar):
    #*************************************************************************************************
    #***** STEP 1 : Access the site *****
    #*************************************************************************************************
    logger.info("********** Connect the site and check data **********")
    driver_path = path_driver + "chromedriver.exe"
    options = Options()
    options.headless = True

    browser = webdriver.Chrome(options=options, executable_path=driver_path)

    url_wind = f"https://www.windguru.cz/archive.php?id_spot=953581&id_model=3&date_from={date_from}&date_to={date_to}"
    # On lance Chrome
    browser.get(url_wind)

    #*************************************************************************************************
    #***** STEP 2 : CONNECT *****
    #*************************************************************************************************
    xpath_connect =  '//*[@id="wg_login_link"]/span'
    xpath_username = '//*[@id="inputusername"]'
    xpath_password = '//*[@id="jBoxID10"]/div/div[2]/form/label[2]/input'
    xpath_send = '//*[@id="jBoxID10"]/div/div[2]/form/button[1]'
    connect(xpath_username, xpath_password, xpath_send, browser, logger)
    progress_bar.add_tick(2)
    #*************************************************************************************************
    #***** STEP 3 : GET TO THE PAGE WE WANT *****
    #*************************************************************************************************
    time.sleep(1)
    # 2 -> 14 included : vitesse du vent
    # 14- 25 included : Direction vent
    # 26 -> 47 included : Température
    progress_bar.add_tick(2)
    # Direction vent : 0 : pas de vent; 1 : offshore; 2: onshore, 3: north; 4:south
    total_wind_speed, total_wind_directions, total_temperatures = [], [], []
    for j in range(3, 127):
        wind_speed = [browser.find_element_by_xpath(f'//*[@id="archive_results"]/table/tbody/tr/td/table/tbody/tr[{j}]/td[{i}]').text for i in range(2,14)]
        wind_directions = []
        temperatures = [browser.find_element_by_xpath(f'//*[@id="archive_results"]/table/tbody/tr/td/table/tbody/tr[{j}]/td[{i}]').text for i in range(26,38)]
        progress_bar.add_tick(1)
        for i in range(14,26):
            try:
                wind_dir = browser.find_element_by_xpath(f'//*[@id="archive_results"]/table/tbody/tr/td/table/tbody/tr[{j}]/td[{i}]/*[name()="svg"]/*[name()="g"]').get_attribute("transform").split(" ")[0]
            except Exception as e:
                wind_dir = 0 # 0 means no wind
            wind_directions.append(tackle_wind(wind_dir))
            # add progress
            progress_bar.add_tick(1)
        total_wind_speed.append(wind_speed)
        total_wind_directions.append(wind_directions)
        total_temperatures.append(temperatures)
    dates = [browser.find_element_by_xpath(f'//*[@id="archive_results"]/table/tbody/tr/td/table/tbody/tr[{i}]/td[1]/*[name()="b"]').text for i in range(3, 127)]
    progress_bar.add_tick(1)
    return dates, total_wind_speed, total_wind_directions, total_temperatures
