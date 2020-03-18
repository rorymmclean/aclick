import logging
from logging.handlers import RotatingFileHandler
import time
import datetime
from flask import Flask, request, render_template, redirect
from math import floor
from sqlite3 import OperationalError
import string
import sqlite3
import json
import pandas as pd
try:
    from urllib.parse import urlparse  # Python 3
    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Python 2
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import base64
import random

# Assuming urls.db is in your app root folder
app = Flask(__name__)
host = 'http://aclick.us/'

LOG_FILENAME = '/Users/rorymclean/Downloads/aclick/access.log' #'/home/ubuntu/logs/access.log'
formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=5)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
app.logger.addHandler(handler)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)
log.addHandler(handler)

def table_check():
    create_table = """
        CREATE TABLE WEB_URL(
        ID TEXT PRIMARY KEY AUTOINCREMENT,
        URL TEXT NOT NULL,
        FULL_URL TEXT NOT NULL,
        SHORT_URL TEXT NOT NULL,
        CREATED TEXT NOT NULL
        );
        """
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
        except OperationalError:
            pass


def toBase62(num, b=62):
    if b <= 0 or b > 62:
        return 0
    base = string.digits + ascii_lowercase + ascii_uppercase
    r = num % b
    res = base[r]
    q = floor(num / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res


def toBase10(num, b=62):
    base = string.digits + ascii_lowercase + ascii_uppercase
    limit = len(num)
    res = 0
    for i in range(limit):
        res = b * res + base.find(num[i])
    return res


@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        original_url = request.form.get('url')
        web_shortname = request.form.get('urlname')
        if web_shortname == '':
            myid = random.randint(39701, 525649984) ## From three to five digit word
        else:
            myid = toBase10(web_shortname)
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        encoded_string = toBase62(myid)
        if urlparse(original_url).scheme == '':
            fullurl = 'http://' + original_url
            url = str_encode(fullurl)
        else:
            fullurl = original_url
            url = str_encode(fullurl)

        conn = sqlite3.connect('urls.db')
        c = conn.cursor()

        c.execute('SELECT ID FROM WEB_URL WHERE FULL_URL = (?)',[fullurl])

        id_exists = c.fetchone()
        if id_exists:
            myid = int(id_exists[0])
            encoded_string = toBase62(myid)
        else:
            res = c.execute(
                'INSERT INTO WEB_URL (ID, URL, FULL_URL, SHORT_URL, CREATED) VALUES (?,?,?,?,?)',
                [myid, base64.urlsafe_b64encode(url), fullurl, encoded_string, st]
            )
            conn.commit()

        conn.close()

        return render_template('home.html', short_url=host + encoded_string)
    return render_template('home.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect("http://www.aderas.com")


@app.route('/delete/<short_url>')
def delete_short_url(short_url):
    decoded = toBase10(short_url)
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        res = cursor.execute('DELETE FROM WEB_URL WHERE ID=?', [decoded])
    conn.commit()
    conn.close()
    return redirect(host+"urls1")

@app.route('/urls1')
def urls1():
    conn = sqlite3.connect('urls.db')
    cur = conn.execute('SELECT SHORT_URL, FULL_URL, CREATED from WEB_URL order by SHORT_URL')
    myurls = [dict(short_url=row[0],
                    full_url=row[1],
                    created=row[2]) for row in cur.fetchall()]
    conn.close()
    return render_template('urls.html', myurls=myurls)


@app.route('/urls2')
def urls2():
    conn = sqlite3.connect('urls.db')
    cur = conn.execute('SELECT SHORT_URL, FULL_URL, CREATED from WEB_URL order by FULL_URL')
    myurls = [dict(short_url=row[0],
                    full_url=row[1],
                    created=row[2]) for row in cur.fetchall()]
    conn.close()
    return render_template('urls.html', myurls=myurls)


@app.route('/urls3')
def urls3():
    conn = sqlite3.connect('urls.db')
    cur = conn.execute('SELECT SHORT_URL, FULL_URL, CREATED from WEB_URL order by CREATED')
    myurls = [dict(short_url=row[0],
                    full_url=row[1],
                    created=row[2]) for row in cur.fetchall()]
    conn.close()
    return render_template('urls.html', myurls=myurls)

@app.route('/opportunity/', methods=['GET', 'POST'])
def opportunity():
    if request.method == 'POST':
        contract_number = request.form.get('contract_number')
        agency_name = request.form.get('agency_name')
        acquisition_strategy = request.form.get('acquisition_strategy')
        release_date = request.form.get('release_date')
        contract_duration = request.form.get('contract_duration')
        contract_type = request.form.get('contract_type')
        anticipated_value = request.form.get('anticipated_value')
        incumbent_name = request.form.get('incumbent_name')
        description = request.form.get('description')

        d = {'Contract Number': [contract_number],
             'Agency_Name': [agency_name],
             'Acquisition_Strategy': [acquisition_strategy],
             'Anticipated_Release_Date': [release_date],
             'Contract_Duration': [contract_duration],
             'Anticipated_Value': [anticipated_value],
             'Contract_Type': [contract_type],
             'Incumbent_Name': [incumbent_name],
             'Description': [description]
             }
#        recs = pd.DataFrame(data=d)

        jf = open('opportunity'+ datetime.datetime.now().strftime("%Y%m%d%H%M") + '.json', "w")
#        rows = [dict(rec) for rec in recs]
#        rows_json = json.dumps(rows, sort_keys=True, indent=2, separators=(',', ': '))
        rows_json = json.dumps(d, sort_keys=True, indent=2, separators=(',', ': '))
        print(rows_json, file=jf)

        return render_template('opportunity.html', response_msg="Record Saved!")
    return render_template('opportunity.html')


@app.route('/<short_url>')
def redirect_short_url(short_url):
    decoded = toBase10(short_url)
    url = host  # fallback if no URL is found
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        res = cursor.execute('SELECT URL FROM WEB_URL WHERE ID=?', [decoded])
        try:
            short = res.fetchone()
            if short is not None:
                url = base64.urlsafe_b64decode(short[0])
        except Exception as e:
            print(e)
    return redirect(url)


if __name__ == '__main__':
    # This code checks whether database table is created or not
    table_check()
    app.run(debug=False, host='0.0.0.0', port=8080)
