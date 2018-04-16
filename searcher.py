import pysolr
import re
import tldextract
from Queue_Class import *
import connection

solr = pysolr.Solr('http://localhost:8983/solr/health', timeout=10)
db = connection.db


def search(keyword, Mytype):
    keyword = keyword.strip()
    delimiters = ";", "-", ";", "\\", "|", "!", "@", "-", " ", "#", "$", "%", "^", "&", "*", "/", ".", ":", "~", "`"
    regexPattern = '|'.join(map(re.escape, delimiters))
    words = re.split(regexPattern, keyword)
    wordsKey = list(words)
    if Mytype == '1':
        query = "aKey:\"" + keyword + "\"" + " OR " + "url:\"" + keyword + "\"" + " OR " + "title:\"" + keyword + "\""
        print("Query = ", query)
        results = solr.search(q=query)
        counter = 0
        urls = set()

    elif Mytype == '2':
        query = ''
        for w in words:
            if w != "":
                query += "aKey:" + w + ' '
        query += " OR url:\"" + keyword + "\""
        print(query)
        results = solr.search(q=query)
        counter = 0
        urls = set()
        # print("length : ", len(results))

    elif Mytype == '3':
        # print(words)
        urls = list()
        temp = words[0]
        words.remove(temp)
        query1 = "(aKey:" + temp
        # query2 = 'title:'+temp
        for w in words:
            if w != "":
                query1 += ' AND aKey:' + w

        query1 += ") OR url:\"" + keyword + "\""
        print(query1)
        results = solr.search(q=query1)
        counter = 0
        urls = set()

    temp_u = set()
    for result in results:
        counter += 1
        try:
            u = result['url'][0]
            query = {'url': u}
            collection_name = tldextract.extract(u).domain

            cur = db[collection_name].find_one({"url": u})
            if u.startswith('http'):
                tempu = u.replace("http://", "")
            if u.startswith('https'):
                tempu = u.replace("https://", "")
            # print(u)
            obj = UrlClass(u, result['title'], "", "")
            try:
                obj.p = cur['p']
                if len(obj.p) < 100:
                    aKey = cur['aKey']
                    for a in aKey:
                        if a.startswith('http'):
                            continue
                        obj.p += a + " "
                        if len(obj.p) >= 250:
                            break
                if len(obj.p) >= 250:
                    obj.p = obj.p[0:250]
            except Exception as errorinpage:
                print(errorinpage)
            if cur is not None:
                obj.rank = cur['new_rank']
                wordsFind = cur['aKey']
                wordCount = 0
                wordCountAll = 0
                for w in wordsFind:
                    w = w.lower()
                    # print(w, wordsKey)
                    wordCountAll += len(w.split())
                    # print(wordCountAll)
                    for w2 in wordsKey:
                        w2 = w2.lower()
                        wordCount += w.count(w2)

                digit = len(str(wordCountAll)) - 1
                tempc = (wordCount / wordCountAll) * (10 ** digit)
                # print(tempc,wordCount,wordCountAll)
                obj.rank = obj.rank + tempc
                # print("========", obj.rank, wordCount, wordCountAll, cur['url'])
                if tempu in temp_u:
                    continue
                temp_u.add(tempu)
                urls.add(obj)
            else:
                print("Not Found ", u)
        except Exception as errorinpage:
            print("Exception ", str(errorinpage))

    a = list(urls)
    a.sort(key=lambda x: float(x.rank), reverse=True)
    return a


def callSearch():
    while (True):
        k = input('Enter key Word : ')
        urls = search(k, '1')
        for u in urls:
            print(u.title, "=", u.rank)
