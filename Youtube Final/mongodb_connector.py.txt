import pymongo

def connect_to_mongodb():
    # Replace the connection string with your MongoDB URL and database name
    mongo_url = "mongodb://localhost:27017/"
    database_name = "channel_data_db"
    collection_name = "channel_data_collection"

    # Connect to the MongoDB server
    client = pymongo.MongoClient(mongo_url)

    # Connect to the database
    database = client[database_name]

    # Return the collection where you want to store the data
    collection = database[collection_name]
    return collection






















