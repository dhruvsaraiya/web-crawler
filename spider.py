import urllib.error
import ssl
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import connection
import tldextract
from random import randint
from Queue_Class import *
import math


def crawl(collection_name, start_url, no_of_pages):
    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    starturl = start_url

    db = connection.db

    href = start_url
    ipos = href.find('#')
    if (ipos > 1): href = href[:ipos]
    if (href.endswith('.png') or href.endswith('.jpg') or href.endswith('.gif')):
        return
    if (href.endswith('/')): href = href[:-1]

    query = {"url": href}
    cur = db[collection_name].find(query)
    already = False
    print("hey")
    for c in cur:
        print("here")
        already = True
        break

    link_table = collection_name + "_links"
    initial_dict = {}
    if already:
        print("ALREADY")
        query = {"title": None, "aKey": None}
        project = {"_id": 1, "url": 1, "title": 1, "old_rank": 1, "new_rank": 1, "error": 1}
        cur = db[collection_name].find(query, project)
        for c in cur:
            obj = QueueClass(c['url'], c['_id'])
            obj.old_rank = 0.0
            obj.new_rank = 1.0
            obj.error = 0
            if tldextract.extract(c['url']).domain == collection_name:
                initial_dict[c['url']] = obj
    else:
        print("DON")
        starturl = start_url
        if (len(starturl) < 1): starturl = 'wikipedia.org'
        if (starturl.endswith('/')): starturl = starturl[:-1]
        web = starturl
        if (starturl.endswith('.htm') or starturl.endswith('.html')):
            pos = starturl.rfind('/')
            web = starturl[:pos]

        db[collection_name].insert_one({"url": starturl})
        findId = db[collection_name].find_one({"url": starturl})
        obj = QueueClass(starturl, findId["_id"])
        initial_dict[starturl] = obj
        print("length :", len(initial_dict))
        if (len(web) > 1):
            try:
                db["webs"].update_one({"url": web}, {"$set": {"dummy": 1}}, upsert=True)
            except Exception as e:
                print(str(e))
            # cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES ( ?, NULL, 1.0 )', ( starturl, ) )

    cur = db['webs'].find()
    webs = set()
    for row in cur:
        webs.add(str(row['url']))
    # print(webs)

    many = no_of_pages
    while True:
        many = many - 1
        if len(initial_dict) == 0: return
        nextUrl = list(initial_dict).pop(0)
        next = initial_dict[nextUrl]
        del initial_dict[nextUrl]
        # print(next)
        # cur.execute('SELECT id,url FROM Pages WHERE html is NULL and error is NULL ORDER BY RANDOM() LIMIT 1')
        try:
            # print(next.id,next.url)
            fromid = next.id
            url = next.url
        except:
            print('No unretrieved HTML pages found')
            many = 0
            break

        print("<====    " + url + "   ====>")
        # print(fromid, url, end=' ')

        # If we are retrieving this page, there should be no links from it
        del_count = db[link_table].delete_many({"from_id": fromid})
        # cur.execute('DELETE from Links WHERE from_id=?', (fromid, ) )
        try:
            document = urlopen(url, context=ctx)
            # print("" + url + "   ====>")
            html = document.read()
            if document.getcode() != 200:
                print("Error on page: ", document.getcode())
                next.error = -1
            if 'text/html' != document.info().get_content_type():
                print("Ignore non text/html page")
                db[collection_name].delete_many({"url": url})
                next.error = -1
                continue
            # print("" + url + "   +++++====>")
            # print('('+str(len(html))+')', end=' ')

            soup = BeautifulSoup(html, "html.parser")
        except KeyboardInterrupt:
            # saveToDB(db, collection_name, initial_dict, len(initial_dict), link_table, links)
            print('')
            print('Program interrupted by user...')
            break
        except Exception as error_in_page:
            print("Unable to retrieve or parse page : ", error_in_page)
            cursorEx = db[collection_name].find()
            if str(error_in_page).lower().count("forbidden") > 0:
                if cursorEx.count() <= 1:
                    db.drop_collection(collection_name)
            next.error = -1
            continue

        # Retrieve all of the anchor tags
        tags = soup('a')
        aKeyText = []
        stringA = []
        count = 0
        for tag in tags:
            href = tag.get('href', None)
            stringA = tag.findAll(text=True)
            if (stringA != ""):
                aKeyText += stringA
            if (href is None): continue
            # Resolve relative references like href="/contact"
            up = urlparse(href)
            if (len(up.scheme) < 1):
                href = urljoin(url, href)
            ipos = href.find('#')
            if (ipos > 1): href = href[:ipos]
            if (href.endswith('.png') or href.endswith('.jpg') or href.endswith('.gif')): continue
            if (href.endswith('/')): href = href[:-1]
            if (tldextract.extract(href).domain != collection_name):
                continue
            # print("Ohh",href)
            if (len(href) < 1): continue

            db[collection_name].update_one({"url": href}, {"$set": {"url": href}}, upsert=True)
            # cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES ( ?, NULL, 1.0 )', ( href, ) )
            # count = count + 1
            # conn.commit()

            # cur.execute('SELECT id FROM Pages WHERE url=? LIMIT 1', ( href, ))
            cur = db[collection_name].find_one({"url": href}, {"_id": 1})
            try:
                toid = cur["_id"]
            except:
                print('Could not retrieve id')
                continue
            # print fromid, toid
            # print(href)
            db[link_table].update_one({"from_id": fromid, "to_id": toid}, {"$set": {"from_id": fromid, "to_id": toid}},
                                      upsert=True)
            obj = QueueClass(href, toid)
            initial_dict[href] = obj
            # print("len",len(initial_dict))
            # cur.execute('INSERT OR IGNORE INTO Links (from_id, to_id) VALUES ( ?, ? )', ( fromid, toid ) )

        tags = soup('title')
        titleText = ""
        for tag in tags:
            titleText = tag.findAll(text=True)

        pText = ""
        try:
            desc = soup.findAll(attrs={"name": "description"})
            pText = desc[0]['content']
        except Exception as error_in_page:
            print("No meta tag found so", error_in_page)
            try:
                desc = soup('p')[0].findAll(text=True)
                print(desc)
            except Exception as error_in_page:
                print("not even p tag", error_in_page)
        # print(pText)
        next.aKey = aKeyText
        next.title = titleText
        next.p = pText
        db[collection_name].update_one({"url": url}, {
            "$set": {"aKey": next.aKey, "p": next.p, "title": next.title, "new_rank": 1.0, "old_rank": 0.0,
                     "error": next.error}}, upsert=False)
        # print(count)
        if many <= 0:
            break
