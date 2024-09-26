from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URL = "mongodb://root:qwe123@mongo:27017/"
DATABASE_NAME = "receptor"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

destinations_collection = db['destinations']
strategies_collection = db['strategies']
logs_collection = db['logs']
users_collection = db['users']
