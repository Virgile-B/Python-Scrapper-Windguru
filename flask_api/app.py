import os
from datetime import datetime

import pandas as pd
from flask import Flask, redirect, render_template, request
from flask.logging import create_logger

from config import (CHROMIUM_PATH, CONDITION_COLOR, CONDITION_MAPPING,
                    SQL_TABLE_NAMES, TABLE_EXPORT_PATH)
from db import get_db, init_db, query_db, upload_to_db
from utils import ProgressBar, check_date_format, shape_data
from webscraper import webscrap_data


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flask_api.sqlite"),
        DEBUG=True,
    )
    # initialize database
    init_db(app)

    # initialising the progress bar
    global progress_bar
    progress_bar = ProgressBar(1630)

    # initiliazing the dates
    global today, date_from
    today = pd.to_datetime(datetime.today())
    date_from = today - pd.offsets.Day(123)

    # initializing the search content for /data
    global search_content
    search_content = dict()

    # the home page
    @app.route("/")
    def home():
        return render_template("home.html")

    # page to be accessed only to make SQL query
    @app.route("/sql", methods=["GET"])
    def sql():
        response = []
        if request.method == "GET" and ("sql" in request.values.keys()):
            # get the query as a string
            query = str(request.values["sql"])
            with app.app_context():
                try:
                    response = query_db(
                        query
                    )
                except UnboundLocalError as e:
                    create_logger(app).warning(
                        f"A bad request was made: {e}, \n{request.headers}"
                    )
        return {"data": response}

    # a page that displays the dashboard
    @app.route("/dashboard", methods=["GET"])
    def dashboard():
        if request.method == "GET":
            with app.app_context():
                data = fetch_all(
                    app=app, 
                    start_date=datetime.date(today - pd.offsets.BDay(7)), 
                    end_date=datetime.date(today),
                )
                if not data:
                    return render_template("dashboard.html", data=[], date_list=[])
                data = pd.DataFrame.from_dict(data)
                data["condition_value"] = (
                    data["temperature"] >= 10
                ).astype(int) + (
                    (data["speed"] >= 12) & (data["speed"] <= 35)
                ).astype(int) + (
                    data["direction"] <= 2 
                    ).astype(int)
                # mapping the conditions
                data["condition"] = data["condition_value"].map(
                    CONDITION_MAPPING
                )
                data["condition_color"] = data["condition_value"].map(
                    CONDITION_COLOR
                )
                date_list = list(set(
                    data["date"].astype(str)
                ))
                data_to_send = dict()
                for date in date_list:
                    data_to_send.update(
                        {date: data[
                            data["date"] == date
                        ].to_dict("list")}
                    )
                return render_template("dashboard.html", data=data_to_send, date_list=sorted(date_list)[::-1])

    # page to use to webscrap
    @app.route("/webscraper", methods=["GET", "POST"])
    def webscrap():
        global progress_bar, today, date_from
        is_webscraping = False
        logger = create_logger(app)
        
        with app.app_context():
            if request.method == "GET":
                return render_template("webscraper.html")

            elif request.method == "POST":
                if bool(request.form.get("webscrap_website")) and not is_webscraping:
                    # initializing variables
                    progress_bar.reset()
                    progress_bar.add_tick(1)
                    is_webscraping = True
                    db = get_db()

                    # launching the webscraper
                    logger.info("launching the webscraper")
                    progress_bar.add_tick(1)

                    logger.info(f"searching between {date_from} to {today}")
                    
                    dates, tot_wind_speed, tot_wind_direction, tot_temperature = webscrap_data(
                        path_driver=CHROMIUM_PATH,
                        date_from=datetime.date(date_from),
                        date_to=datetime.date(today),
                        logger=logger,
                        progress_bar=progress_bar,
                    )
                    progress_bar.add_tick(2)
                    speed, direc, temp = shape_data(dates, tot_wind_speed, tot_wind_direction, tot_temperature)

                    progress_bar.add_tick(2)
                    upload_to_db(
                        db=db,
                        df_speed=speed,
                        df_direction=direc,
                        df_temperature=temp,
                        table_names=SQL_TABLE_NAMES,
                        logger=logger,
                    )
                    # reset variables
                    db.commit()
                    db.close()
                    progress_bar.reset()
                    is_webscraping = False
                return redirect("/webscraper")

    @app.route("/webscraper/progress")
    def progress():
        global progress_bar
        return str(progress_bar.percentage())

    # page to use to fetch the data
    @app.route("/data", methods=["GET", "POST"])
    def data():
        global search_content

        logger = create_logger(app)
        table = []
        valid = True
        # initiliaze values if first time on page
        if not search_content:
            search_content = dict(
                {
                    "start-date": "2022-10-01",
                    "end-date": "2022-11-22",
                }
            )

        with app.app_context():
            if request.method == "GET":
                logger.info("Displaying the data")
                return render_template("data.html", table=table, is_valid=valid, dates=search_content)
            
            # only used when posting the search form
            elif request.method == "POST":
                # check if form is valid
                if bool(request.form.get("search-form")):
                    if check_date_format(
                        request.form["start-date"]
                    ) and check_date_format(
                        request.form["end-date"]
                    ) and request.form["start-date"] < request.form["end-date"]:
                        content = {
                            "start-date": request.form["start-date"],
                            "end-date": request.form["end-date"],
                        }
                        valid = True
                        search_content.update(content)
                        logger.info(
                            f"Searching between {content['start-date']} and {content['end-date']}"
                        )
                        table = fetch_all(app, search_content["start-date"], search_content["end-date"])

                        if "export" in request.form.keys() and bool(request.form["export"]):
                            path = os.path.join(app.root_path, TABLE_EXPORT_PATH, "weather_condition.csv") 
                            logger.info(
                                f"Exporting the data to csv: {path}")
                            export_table = pd.DataFrame(table)
                            export_table.to_csv(path)
                    else:
                        # set form to 'invalid request'
                        valid = False
                return render_template("data.html", table=table, is_valid=valid, dates=search_content)
    return app


def fetch_all(app, start_date, end_date):
    logger = create_logger(app)
    # query the database
    response = query_db("select * from conditions where date >= ? and date <= ? order by date DESC;", [start_date, end_date])
    logger.info(f"found {len(response)} elements in the database")
    return response


if __name__ == "__main__":
    app = create_app()
    app.run()