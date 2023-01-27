import time
from datetime import datetime

import pandas as pd
import requests

global browser


def shape_data(lines, wind_speed, wind_direction, temperature):
    dates = [datetime.strptime(date, "%d.%m.%Y") for date in lines]
    cols2 = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    df_wind_speed = pd.DataFrame(data=wind_speed, index=pd.to_datetime(dates), columns = cols2)
    df_wind_dir = pd.DataFrame(data=wind_direction, index=pd.to_datetime(dates), columns = cols2)
    df_temperature = pd.DataFrame(data=temperature, index=pd.to_datetime(dates), columns = cols2)
    return df_wind_speed.astype(int), df_wind_dir.astype(int), df_temperature.astype(int)


def connect(xpath_u, xpath_pwd, xpath_s, browser, logger):
    try:
        time.sleep(1)
        username = browser.find_element_by_xpath(xpath_u)
        logger.info("Trouver le cartouche d'id = ok")
        username.send_keys("203test")
        logger.info("Entrer id = ok")
        #password = driver.find_element_by_id("password")
        password = browser.find_element_by_xpath(xpath_pwd)
        password.send_keys("Virgile28")
        logger.info("Entrer pwd = ok")
        time.sleep(1)
        browser.find_element_by_xpath(xpath_s).click()
        logger.info("done \n")
        time.sleep(2)
    except Exception as e:
        logger.info(f"There is an issue: {e}")
    logger.info("Identification done")


def tackle_wind(wind_dir):
    # Good, Bad, pretty good, pretty bad transposed as a score:
    # [225,325] = max score
    # [180,225] or [325,360] = moderate good
    # [360,405] or [495,540] = moderate bad
    # [405,495] = lowest score
    # score between 0 and 3 (worst to best)
    result = 0
    try:
        direction = int(wind_dir[7:10])
    except Exception as e:
        direction = 0
    if direction==0:
        result = -1
    elif direction < 325 and direction > 225:
        result = 3
    elif (direction > 180 and direction < 225) or (direction > 325 and direction < 360):
        result = 2
    elif (direction > 360 and direction < 405) or (direction > 495 and direction < 540):
        result = 1
    elif direction > 405 and direction < 495:
        result = 0
    return result


def check_date_format(date):
    try:
        date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return False
    return True


class ProgressBar():
    """
    Quick progress bar.
    """
    def __init__(self, size: int) -> None:
        self.size = size
        self.progress = 0
    
    def add_tick(self, tick: int):
        if self.progress + tick <= self.size:
            self.progress += tick

    def percentage(self) -> float:
        return int(100 * (self.progress / self.size))

    def reset(self):
        self.progress = 0


def sql_query(url: str, query: str):
    """
    Allows the user to make a SQL request to the API.

    params:
        * url: url of the api endpoint for the query.
        * query: string representing the SQL query

    return:
        * the query response
    """
    try:
        response = requests.get(
            url,
            {
                "sql": query + ";",
            }
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise f"Invalid request: {e}"
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Invalid response: {response.status_code}"
