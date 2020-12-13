import pymongo
import config

client = pymongo.MongoClient(config.db_url)
db = client.psycho
user_db = client.psycho.user

