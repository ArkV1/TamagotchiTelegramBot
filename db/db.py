from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.collection import ReturnDocument


###########################################################################################
###                                      DATABASE                                       ###
###########################################################################################

def initialize_database():
    try:
        # Connection URI
        uri = 'mongodb://localhost:27017/'
        # Create a MongoClient to the running mongod instance
        client = MongoClient(uri)
        
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        
        # Specify the database name to use or create if it doesn't exist
        db = client['MyPetTroyan']
        pets_collection = db['troyans']
        
        print("Database initialized successfully.")
        return pets_collection
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        return None
    

###########################################################################################

# Attempt to initialize the database
pets_collection = initialize_database()

# Exit if database initialization fails
if pets_collection is None:
    print("Database initialization failed. Exiting...")
    exit(1)

###########################################################################################

def create_character(unique_id, name):
    print(f"Creating character with unique_id: {unique_id} and name: {name}")
    default_character = {
        "unique_id": unique_id,
        "name": name,  # Use the variable directly without quotes or braces
        "exp": 0,
        "hunger": 0,
        "health": 100,
        "money": 0,
        "mood": 25,
    }
    pets_collection.replace_one({"unique_id": unique_id}, default_character, upsert=True)
    return


def update_character_stat(unique_id, update_operations):
    """
    Update a character's statistics, with debugging prints for the document
    before and after the update.

    Parameters:
    - unique_id (str): The unique identifier for the character.
    - update_operations (dict): MongoDB update operations dict.

    Returns:
    - The updated document or None if the update was unsuccessful.
    """
    try:
        # Print the document before the update
        current_document = pets_collection.find_one({"unique_id": unique_id})
        print("\nBefore update:", current_document)

        updated_document = pets_collection.find_one_and_update(
            {"unique_id": unique_id},
            update_operations,
            return_document=ReturnDocument.AFTER
        )

        # Print the document after the update
        print("\nAfter update:", updated_document)

        return updated_document
    except Exception as e:
        print(f"An error occurred while updating character stats: {e}")
        return None


def get_character(unique_id):
    return pets_collection.find_one({"unique_id": unique_id})

###########################################################################################