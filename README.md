# Receptor.ai
Test task

# Comments
Project is published at Docker Hub Repository kolacx4/receptor 

In order to start the project you need to download [docker-compose.yaml](https://github.com/kolacx/receptor/blob/main/docker-compose.yaml) file

After running projects near docker-compose.yaml will be created data/ file, where saved databases (data/db)

To reconfigure the database, use the mongo-express web interface

To see all tables follow by http://localhost:8081/db/receptor url after init_db.sh (read below)

All requests and responses write at logs docs (Enabled after first /event)

All logs are available by docker logs
```sh
docker logs -f receptor-backend
```
Service urls
- http://localhost:8000/ping-post
- http://localhost:8000/ping-get


User credentials
```json
{
    "username": "admin",
    "password": "qwe123"
}
```

## Technology
- FastAPI
- MongoDB
- Docker

## Instruction

Run projects
```sh
docker compose up -d
```
After run project, 3 containers will be available:
- receptor-backend (Project)
- mongo-db (Database)
- mongo-express (Web interface for MongoDB)

Init database
```sh
docker exec -it receptor-backend ./init_db.sh
```
File init_db.sh creates default Strategy records:
```json
[
    {
        "name": "ALL",
        "python_code": "lambda routing_intents: routing_intents"
    },
    {
        "name": "IMPORTANT",
        "python_code": "lambda routing_intents: [intent for intent in routing_intents if intent.get(\"important\", False)]"
    },
    {
        "name": "SMALL",
        "python_code": "lambda routing_intents: [routing for routing in routing_intents if routing.get(\"bytes\") < 1024]"
    }
]
```
default Destinations:
```json
[
    {
        "destinationName": "destination1",
        "transport": "http.post",
        "url": "http://127.0.0.1:8000/ping-post"
    },
    {
        "destinationName": "destination2",
        "url": "http://127.0.0.1:8000/ping-get",
        "transport": "http.get"
    },
    {
        "destinationName": "destination3",
        "transport": "log.info"
    }
]
```
default User
```json
[
    {
        "username": "admin",
        "hashed_password": "get_password_hash('qwe123')"
    }
]
```
## Use
Documentation available by address
```
http://localhost:8000/redoc
http://localhost:8000/doc
```

Mongo-express available by address
```
http://localhost:8081/
```

### API
Log In
```
[POST] http://localhost:8000/token
```
BODY
```json
{
    "username": "admin",
    "password": "qwe123"
}
```
Response
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcyNzQyNTMwOX0.CVNFlWYS5PbhnLa38VgcShArV9eCKdDhlRxzKbvx5XQ",
    "token_type": "bearer"
}
```

Events url
```
[POST] http://localhost:8000/event
[HEADERS] Authorization: Bearer <token>
```

Body
```json
{
	"payload": {"a": 123},
	"routingIntents": [
		{ "destinationName": "destination1", "score": 1},
		{ "destinationName": "destination2", "score": -1},
		{ "destinationName": "destination3", "score": 0},
		{ "destinationName": "destination4", "score": -1},
		{ "destinationName": "destination5", "score": 1}
	],
    "strategy": "lambda routing_intents: [intent for intent in routing_intents if intent.get('score', 0) < 0]"
}
```
Response
```json
{
    "destination1": false,
    "destination2": true,
    "destination3": false,
    "destination4": false,
    "destination5": false
}
```