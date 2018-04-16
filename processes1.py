import connection
import time
from rank import *
from spider import *
from indexer import *
from mail import *


def f():
    db = connection.db
    while True:
        print("Crawling")
        query = {"url": {"$ne": None}, "status": "approved"}
        cur = db['queue'].find(query)
        for c in cur:
            # print("a")
            r = c['req_no']
            u = c['url']
            p = c['collection_name']
            n = c['no_of_pages']
            try:
                crawl(p, u, n)
                print("crawled")
                giveRank(p)
                print("ranked")
                index(p)
                print("indexed")
                mail(p, r, "")
            except Exception as e:
                mail(p, r, str(e))
            db['queue'].delete_one({"url": u, "req_no": r})
        print("Job Completed")
        time.sleep(5)


f()
