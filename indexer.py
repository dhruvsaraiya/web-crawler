import connection
import pysolr
import re

def index(collection_name):
    db = connection.db
    query = {'aKey': {'$ne': None}}
    project = {'url': 1, 'aKey': 1, 'title': 1}
    cur = db[collection_name].find(query, project)
    l = list(cur)

    solr = pysolr.Solr('http://localhost:8983/solr/health', timeout=10)

    words = re.split('-', collection_name)
    remQuery = 'url:'
    for w in words:
        remQuery += '*' + w + '*' + ' AND url:'

    remQuery = remQuery[:-9]
    print("Remove : ",remQuery)
    try:
        solr.delete(q=remQuery)
    except:
        pass
    solr.add(l)

    solr.optimize()
    print("Indexing Done")
