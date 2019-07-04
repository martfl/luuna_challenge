#!/usr/local/bin/python

import os
import time
import pandas
import hashlib
import logging
import datetime
import requests
import subprocess
import mysql.connector

from string import Template
from mysql.connector.errors import InterfaceError
from r_template import r_template

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)


def get_db():
    backoff = 0.1
    while(True):
        try:
            db = mysql.connector.connect(
                option_files='/code/db.conf', use_pure=True)
            if db.is_connected():
                logger.info("Connected to database.")
                return db
        except InterfaceError as e:
            logger.error(e)
            logger.info("Waiting for database...")
            time.sleep(backoff)
            backoff *= 2


def get_data(stop, sleep):
    n_samples = int(stop/sleep)
    frame = pandas.DataFrame([])
    logger.info("Measuring employee velocity...")
    while n_samples > 0:
        req = requests.get("http://server:3000/speed")
        emp_data = req.json()["data"]
        emp_speed = pandas.Series([float(emp["velocity"]) for emp in emp_data])
        emp_no = pandas.Series([int(emp["employee_id"]) for emp in emp_data])
        s = pandas.DataFrame({"emp_no": emp_no, "emp_speed": emp_speed})
        frame = pandas.concat([frame, s])
        logger.info("Time left: ~" + str(n_samples * sleep) + "s.")
        n_samples -= 1
        time.sleep(sleep)
    hashstr = hashlib.md5(frame.to_string().encode())
    name = "report" + str(datetime.date.today()) + hashstr.hexdigest()
    return name, frame


if __name__ == '__main__':
    stop = 5*60
    sleep = 5
    db = get_db()
    cursor = db.cursor()
    key, data = get_data(stop, sleep)
    mean_speed = data.groupby(by='emp_no', as_index=False).mean()
    sql_query = """
        select
            v_full_employees.emp_no,
            concat(last_name, ', ', first_name) as full_name,
            department,
            titles.title,
            salaries.salary as base_salary
        from v_full_employees
        inner join titles on v_full_employees.emp_no = titles.emp_no
        inner join salaries on v_full_employees.emp_no = salaries.emp_no
        where
            v_full_employees.emp_no in {0}
            and salaries.to_date = (
                select max(salaries.to_date)
                from salaries
                where v_full_employees.emp_no = salaries.emp_no
            )
            and titles.to_date = (
                select max(titles.to_date)
                from titles
                where v_full_employees.emp_no = titles.emp_no
            );
    """.format(str(tuple(mean_speed.emp_no)))

    cursor.execute(sql_query)
    emp_data = pandas.DataFrame(
        data=[row for row in cursor],
        columns=cursor.column_names
    )
    cursor.close()
    db.close()

    emp_data = emp_data.assign(
        day_average_speed=mean_speed.emp_speed)
    emp_data = emp_data.assign(
        daily_salary=round(emp_data.base_salary + emp_data.base_salary*(emp_data.day_average_speed), 2))
    emp_data = emp_data.set_index("emp_no")

    # create /srv/shiny-server/reports/$date/index.Rmd
    basedir = "/srv/shiny-server/reports"

    newpath = os.path.join(basedir, str(datetime.date.today()))

    logger.info("Writing new report")
    logger.info("Report at: " + newpath)
    os.makedirs(newpath, exist_ok=True)
    path_file = os.path.join(newpath, key + ".csv")
    logger.info("Writing csv as: " + path_file)
    emp_data.to_csv(path_file)
    index_file = os.path.join(newpath, "index.Rmd")
    rmd_file = Template(r_template).safe_substitute(
        date=str(datetime.date.today()), file=key + ".csv")
    logger.info("Writing index as: " + index_file)
    with open(index_file, "w") as text_file:
        text_file.write(rmd_file)

    # subprocess.call("/usr/bin/shiny-server")
    # cache = redis.Redis(host='redis', port=6379)
    # cache.set(key, )
