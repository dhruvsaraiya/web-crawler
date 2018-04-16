from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask import session
from flask.ext.session import Session
from datetime import timedelta
from pymongo import *
import os
import random
import json
import connection
from searcher import *

app = Flask(__name__)
SESSION_TYPE = 'mongodb'
app.config.from_object(__name__)
Session(app)

uri = 'localhost:27017'
client = MongoClient(uri)
database = client.login
db = connection.db


def check_login(role):
    if 'username' in session:
        if session['role'] == role:
            return True
    return False


def from_json(json_obj):
    if 'url' in json_obj:
        return UrlClass(json_obj['url'], json_obj['title'], json_obj['p'], json_obj['rank'])


@app.route('/admin/manage/add', methods=['GET', 'POST'])
def add():
    if not check_login('admin'):
        return redirect('logout')
    if request.method == 'POST':
        fnm = request.form['f_name']
        lnm = request.form['l_name']
        nm = fnm + " " + lnm
        unm = request.form['u_name']
        pwd = request.form['pwd']
        role = 'emp'
        database['login'].update_one({"username": unm},
                                     {"$set": {"username": unm, "password": pwd, "role": role, "name": nm}},
                                     upsert=True)
        return render_template("add_emp.html", status="Added")
    return render_template("add_emp.html")


@app.route('/admin/manage/view', methods=['GET', 'POST'])
def view():
    if not check_login('admin'):
        return redirect('logout')
    url = request.url
    l = len(request.base_url) + 1
    url = url[l:]
    print(url)
    if len(url) > 1:
        unm = request.args['unm']
        database['login'].delete_one({"username": unm})
    rs = database['login'].find({"role": "emp"})
    emps = list()
    for a in rs:
        emps.append(EmployeeClass(a['name'], a['username'], a['password']))
    return render_template("view_emp.html", emps=emps)


@app.route('/admin/manage/approve', methods=['GET', 'POST'])
def approve():
    if not check_login('admin'):
        return redirect('logout')
    url = request.url
    l = len(request.base_url) + 1
    url = url[l:]
    print(url)
    if len(url) > 1:
        cnm = request.args['cnm']
        a = request.args['a']
        nop = request.args['nop']
        nop = abs(int(nop))

        if a == '1':
            try:
                data = db['queue'].find_one({"collection_name": cnm})
                data = data['url']
                c = db['queue'].delete_many({"collection_name": cnm, "status": "pending"})
                print("==========",c)
                db['queue'].insert_one(
                    {"req_no": random.randint(1, 100000), "collection_name": cnm, "url": data, "no_of_pages": nop,
                     "status": "approved"})
                # db['queue'].update_many({"collection_name": cnm}, {"$set": {"status": "approved", "no_of_pages": nop}})
            except Exception as e:
                pass
        if a == '2':
            db['queue'].delete_many({"collection_name": cnm})

    rs = db['queue'].find({"status": "pending"})
    links = list()
    domains = dict()
    for li in rs:
        d = tldextract.extract(li['url']).domain
        nop = li['no_of_pages']
        l = li['url']
        cnm = li['collection_name']
        if d not in domains:
            domains[d] = LinkClass(d, l, cnm, nop)
        else:
            domains[d].nop += nop
    for li in domains:
        li = domains[li]
        links.append(LinkClass(li.domain, li.link, li.cnm, li.nop))
    return render_template("approve.html", links=links)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        unm = request.form['username']
        pwd = request.form['password']
        role = None
        query = {"username": unm, "password": pwd}
        rs = database['login'].find_one(query)
        try:
            session['username'] = rs['username']
            session['role'] = rs['role']
            role = rs['role']
            if role == 'admin':
                return redirect('admin/crawl')
            elif role == 'emp':
                return redirect('employee/crawl')
            else:
                error = 'Invalid username or password. Please try again!'
        except Exception as e:
            error = 'Invalid username or password. Please try again!'
    return render_template('login.html', error=error)


@app.route('/admin/crawl')
def main_admin():
    if check_login('admin'):
        return render_template('crawl.html', role='admin')
    else:
        return redirect('logout')


@app.route('/employee/crawl', methods=['get', 'post'])
def main_emp():
    if check_login('emp'):
        url = request.url
        l = len(request.base_url) + 1
        url = url[l:]
        print(url)
        if request.method == 'POST':
            pro_name = request.form['pro_name']
            url = request.form['url']
            no = request.form['no']
            no = abs(int(no))
            rand = random.randint(1, 100000)
            db['queue'].insert_one(
                {"req_no": rand, "collection_name": pro_name, "url": url, "no_of_pages": no, "status": "pending"})
            return render_template('crawl.html', req=rand, role=session['role'])
        return render_template('crawl.html', role='emp')
    else:
        return redirect('logout')


@app.route('/admin/collections')
def col():
    if not check_login('admin'):
        return redirect('logout')

    nm = db.collection_names()
    output = set()
    for n in nm:
        if n.endswith('_links'):
            continue
        if n == 'webs':
            continue
        if n == 'queue':
            continue
        output.add(n)
    # print(output)
    return render_template('col.html', out=output)


@app.route('/admin/show', methods=['get', 'post'])
def crawl_1():
    if not check_login('admin'):
        return redirect('logout')
    db = connection.db
    url = request.url
    l = len(request.base_url) + 1
    url = url[l:]
    print(url)
    if len(url) > 1:
        project_name = request.args['pn']
        query = {'aKey': {'$ne': None}}
        project = {'url': 1, 'new_rank': 1, 'title': 1}
        cur = db[project_name].find(query, project)
        l = list(cur)
        return render_template('next.html', urls=l, role=session['role'])
    if request.method == 'POST':
        pro_name = request.form['pro_name']
        url = request.form['url']
        no = request.form['no']
        no = abs(int(no))
        rand = random.randint(1, 100000)
        db['queue'].insert_one(
            {"req_no": rand, "collection_name": pro_name, "url": url, "no_of_pages": no, "status": "approved"})

        return render_template('next.html', req=rand, role=session['role'])
    return render_template("next.html", role=session['role'])


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('Contact.html')


global items_per_page
items_per_page = 10


@app.route('/')
@app.route('/user', methods=['post', 'get'])
def user():
    app.permanent_session_lifetime = timedelta(minutes=15)
    session.permanent = True
    search_out = None
    keyword = None
    length = None
    page_arr = None
    try:
        search_out = session['search_out']
        keyword = session['keyword']
        length = session['length']
        page_arr = session['page_arr']
    except Exception as e:
        pass
    url = request.url
    l = len(request.base_url) + 1
    url = url[l:]
    arr = url.split('&')
    pb = 1
    if request.method == 'GET':
        if len(arr) == 3:
            pb = request.args['pb']
            pb = int(pb)
        if len(arr) == 2:
            keyword = request.args['q']
            Mytype = request.args['or']
            search_out = search(keyword, Mytype)
            length = len(search_out)
            if (length % 10) == 0:
                p = int(len(search_out) / items_per_page)
            else:
                p = int(len(search_out) / items_per_page) + 1
            page_arr = list()
            for i in range(1, p + 1):
                page_arr.append(i)
            search_out_json = list()
            for a in search_out:
                search_out_json.append(json.dumps(a, cls=MyEncoder))
            session['search_out'] = search_out_json
            print(session['search_out'])
            session['keyword'] = keyword
            session['page_arr'] = page_arr
            session['length'] = length
        if len(arr) == 1:
            return render_template('user.html', k="")
        temp = list()
        search_out = session['search_out']
        for j in range(items_per_page * (pb - 1), items_per_page * pb):
            if j < len(search_out):
                obj = JSONDecoder(object_hook=from_json).decode(search_out[j])
                temp.append(obj)
            else:
                break
        if len(temp) == 0:
            return render_template('user.html', k=keyword, no_of_pages=page_arr, nodata="true")
        return render_template('user.html', out=temp, k=keyword, no_of_pages=page_arr, length=length)
    if request.method == 'POST':
        pass
    return render_template('user.html', k="")


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect('user')


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.json_encoder = MyEncoder
    app.run(debug=True)
