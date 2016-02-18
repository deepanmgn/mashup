from flask import *
from restaurant_sites import *

import os
import json

import sqlite3
conn = sqlite3.connect('main.db',check_same_thread = False)
#create table query_cache (id integer primary key,query varchar(256), results_json text, page_no integer, next_page varchar(512))

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@app.route("/",methods=["GET"])
def index():
    return render_template('index.html')

@app.route("/more",methods=["GET"])
def more():
    query = session['query']
    next_page_url = session['next_page']

    if next_page_url != "__last__":
        o = re.match(r'.+?search~(\d+)\.',next_page_url)
        next_page_no = int(o.group(1))
    else:
        return "__last__"

    c = conn.cursor()

    rows = []
    for row in c.execute('SELECT * FROM query_cache WHERE query like ? and page_no=?',(query,next_page_no)):
        rows.append(row)

    if rows:
        first_row = rows[0]
        results_json = first_row[2]
        session['next_page'] = first_row[4]
        results = json.loads(results_json)
    else:
        rg = RestaurantGuide(session)
        results = rg.more()
        if results:
            next_page = session['next_page']

            results_json = json.dumps(results)
            all_rows= []
            for row in c.execute('SELECT * FROM query_cache'):
                all_rows.append(row)

            rows_size = len(all_rows)
            next_id = rows_size + 1

            c.execute('INSERT INTO query_cache VALUES (?,?,?,?,?)', (next_id, query, results_json,next_page_no,next_page))

            conn.commit()
            c.close()

    return render_template('results_template.html', results=results)


@app.route("/search",methods=["GET"])
def search():
    query = request.args.get('query')
    p = re.compile( r'\s+')
    query = p.sub('+',query)
    session['query'] = query

    session.pop('next_page', None)

    c = conn.cursor()

    rows = []
    for row in c.execute('SELECT * FROM query_cache WHERE query like ?',(query,)):
        rows.append(row)

    if rows:
        first_row = rows[0]
        results_json = first_row[2]
        session['next_page'] = first_row[4]
        results = json.loads(results_json)
    else:
        rg = RestaurantGuide(session)
        results = rg.search(query)

        if results:
            next_page = session['next_page']
            results_json = json.dumps(results)
            all_rows= []
            for row in c.execute('SELECT * FROM query_cache'):
                all_rows.append(row)

            rows_size = len(all_rows)
            next_id = rows_size + 1

            c.execute('INSERT INTO query_cache VALUES (?,?,?,?,?)', (next_id, query, results_json,1,next_page))

            conn.commit()
            c.close()
    return render_template('results.html', results=results)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.debug = True
    app.run()
