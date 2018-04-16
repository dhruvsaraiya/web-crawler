from pymongo import MongoClient

uri = 'localhost:27017'
client = MongoClient(uri)
db = client.Health
