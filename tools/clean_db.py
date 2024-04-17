from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Drop a database
client.drop_database('tamagotchi_db')

# Drop a collection
db = client['tamagotchi_db']
db.pets.drop()
