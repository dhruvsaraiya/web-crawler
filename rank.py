import connection
import math
from bson import ObjectId
from decimal import *
from random import randint


def giveRank(collection_name):
    # conn = sqlite3.connect('spider.sqlite')
    # cur = conn.cursor()
    db = connection.db
    getcontext().prec = 16

    # Find the ids that send out page rank - we only are interested
    # in pages in the SCC that have in and out links
    link_table = collection_name + "_links"
    ids = db[link_table].distinct("from_id")
    # cur.execute('''SELECT DISTINCT from_id FROM Links''')
    # print(ids)
    from_ids = list()
    for row in ids:
        # print(row)
        if row != '':
            from_ids.append(row)

    # Find the ids that receive page rank
    to_ids = list()
    links = list()

    cur = db[link_table].find()
    # cur.execute('''SELECT DISTINCT from_id, to_id FROM Links''')
    for row in cur:
        from_id = row['from_id']
        to_id = row['to_id']
        if from_id == to_id: continue
        if from_id not in from_ids: continue
        if to_id not in from_ids: continue  # dangling page
        links.append(row)
        if to_id not in to_ids: to_ids.append(to_id)

    # Get latest page ranks for strongly connected component
    prev_ranks = dict()
    for node in from_ids:
        query = {"_id": ObjectId(node)}
        cur = None
        cur = db[collection_name].find(query)
        # cur.execute('''SELECT new_rank FROM Pages WHERE id = ?''', (node, ))
        for row_i in cur:
            row = row_i
        prev_ranks[node] = Decimal(row['new_rank'])

    # print("don +>>>>>>>>>>")
    # print(prev_ranks)

    # sval = input('How many iterations:')
    # sval = 100
    many = 1
    # if ( len(sval) > 0 ) : many = int(sval)

    # Sanity check
    # if len(prev_ranks) < 1 :
    # print("Nothing to page rank.  Check data.")
    # quit()

    # Lets do Page Rank in memory so it is really fast

    totdiff = Decimal(0.0)
    count = 0;
    while True:
        # print prev_ranks.items()[:5]
        next_ranks = dict();
        total = Decimal(0.0)
        for (node, old_rank) in list(prev_ranks.items()):
            # print('dhruv')
            # print(node)
            # print(old_rank)
            total = total + old_rank
            next_ranks[node] = Decimal(0.0)
        # print total

        # Find the number of outbound links and sent the page rank down each
        for (node, old_rank) in list(prev_ranks.items()):
            # print node, old_rank
            give_ids = list()
            # for (from_id, to_id) in links:
            for row in links:
                from_id = row['from_id']
                to_id = row['to_id']
                if from_id != node:
                    continue
                #  print '   ',from_id,to_id
                if to_id not in to_ids:
                    continue
                give_ids.append(to_id)
            if len(give_ids) < 1:
                continue
            amount = old_rank / len(give_ids)
            #print("amount : ", amount, len(give_ids))
            # print node, old_rank,amount, give_ids
            for id in give_ids:
                next_ranks[id] = next_ranks[id] + amount
        newtot = 0
        for (node, next_rank) in list(next_ranks.items()):
            newtot = newtot + next_rank
        evap = (total - newtot) / len(next_ranks)

        # print newtot, evap
        for node in next_ranks:
            next_ranks[node] = next_ranks[node] + evap

        newtot = 0
        for (node, next_rank) in list(next_ranks.items()):
            newtot = newtot + next_rank

        # Compute the per-page average change from old rank to new rank
        # As indication of convergence of the algorithm
        totdiff = 0
        for (node, old_rank) in list(prev_ranks.items()):
            new_rank = next_ranks[node]
            diff = abs(old_rank - new_rank)
            totdiff = totdiff + diff

        #print("Total Diff :", totdiff)
        avediff = totdiff / len(prev_ranks)
        #print("Difference : ")
        #print(avediff)

        # rotate
        prev_ranks = next_ranks
        precision = 0.000000000001
        #print(count)
        if math.isclose(avediff, precision, abs_tol=0.0000000000003):
            break
        elif count > 1000:
            break
        else:
            count = count + 1
        #print("hey : ",count)

    # Put the final ranks back into the database
    print(count," Ranked")
    #print(list(next_ranks.items())[:5])
    cur = db[collection_name].find({"aKey": {"$ne": None}})
    for row_i in cur:
        #print(row_i['url'])
        t = row_i['new_rank']
        url = row_i['url']
        db[collection_name].update_one({'url': url}, {"$set": {"old_rank": t}})
    # cur.execute('''UPDATE Pages SET old_rank=new_rank''')
    for (id, new_rank) in list(next_ranks.items()):
        r = float(new_rank)
        if float(new_rank) <= 0:
            r = 0.0
        db[collection_name].update_one({'_id': ObjectId(id)}, {"$set": {"new_rank": r}})
        # cur.execute('''UPDATE Pages SET new_rank=? WHERE id=?''', (new_rank, id))
    print("Ranking Done")
    # db[collection_name].save()
    # db[link_table].save()
    # conn.commit()
    # cur.close()
