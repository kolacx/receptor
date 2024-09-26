from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://root:qwe123@mongo:27017/"
DATABASE_NAME = "receptor"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

destinations_collection = db['destinations']
strategies_collection = db['strategies']
logs_collection = db['logs']
users_collection = db['users']

destinations_collection.delete_many({})
strategies_collection.delete_many({})
logs_collection.delete_many({})
users_collection.delete_many({})

strategies = [
    {
        'name': 'ALL',
        'python_code': 'lambda routing_intents: routing_intents'
    },
    {
        'name': 'IMPORTANT',
        'python_code': 'lambda routing_intents: [intent for intent in routing_intents if intent.get("important", False)]'
    },
    {
        'name': 'SMALL',
        'python_code': 'lambda routing_intents: [routing for routing in routing_intents if routing.get("bytes") < 1024]'
    }
]

strategies_collection.insert_many(strategies)

destinations = [
    {
        'destinationName': 'destination1',
        'transport': 'http.post',
        'url': 'http://127.0.0.1:8000/ping-post',
    },
    {
        'destinationName': 'destination2',
        'url': 'http://127.0.0.1:8000/ping-get',
        'transport': 'http.get'
    },
    {
        'destinationName': 'destination3',
        'transport': 'log.info'
    }
]

destinations_collection.insert_many(destinations)

