import sqlite3

import pandas as pd
from flask import current_app, g
from flask.logging import create_logger

import os

from config import SQL_TABLE_NAMES


def get_db():
    db = getattr(g, '_database', None)
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = make_dicts
        db = g.db
    return db


def create_instance_dir(app, logger):
    instance_path = app.instance_path
    if not os.path.isdir(instance_path):
        logger.info(
            f"No instance directory. Creating one at {instance_path}"
        )
        os.mkdir(instance_path)


def check_db_exist(db, table=SQL_TABLE_NAMES):
    cur = db.cursor()
    response = True
    try:
        cur.execute(f"SELECT count(*) FROM {table}")
        cur.close()
    except sqlite3.Error:    
        response = False
    return response


def init_db(app):
    logger = create_logger(app)
    logger.info("Initializing the database")

    with app.app_context():
        # checking if the instance folder exist
        create_instance_dir(
            app=app,
            logger=logger,
        )
        db = get_db()
        # creating the database 
        if not db:
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            db.close()


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
            for idx, value in enumerate(row))


def query_db(query, args=(), one=False):
    db = get_db()
    if sqlite3.complete_statement(query) and check_db_exist(db):
        try:
            cur = db.execute(query, args)
            rv = cur.fetchall()
            cur.close()
        except sqlite3.Error as e:
            print("An error occurred:", e.args[0])
        return (rv[0] if rv else None) if one else rv
    else:
        return []


def post_to_db(data):
    # if data valid do:
    try:
        db = get_db()
        db.execute(
            "INSERT INTO user(id,username,password) VALUES(?,?,?)", 
            data,
        )
        db.commit()
        db.close()
    except sqlite3.Error as e:
        print("An error occurred:", e.args[0])


def format_dataframe(*, df: pd.DataFrame, col_name: str):
    df.index = df.index.set_names("date")
    df.index = pd.to_datetime(df.index)
    formated_df = df.stack()
    # set new index name
    formated_df.index = formated_df.index.set_names(("date", "hour"))
    return pd.DataFrame(formated_df, columns=[col_name])


def upload_to_db(*, db, df_speed, df_direction, df_temperature, table_names, logger):
    """
    Upload all dataframes to db.
    """
    formated_speed = format_dataframe(
        df=df_speed,
        col_name="speed",
    )
    formated_dir = format_dataframe(
        df=df_direction,
        col_name="direction",
    )
    formated_temp = format_dataframe(
        df=df_temperature,
        col_name="temperature",
    )

    complete_df = formated_temp.join(
        [formated_speed, formated_dir],
    )

    logger.info("Uploading the complete dataframe to the database")

    complete_df.to_sql(table_names, con=db, if_exists="replace")
