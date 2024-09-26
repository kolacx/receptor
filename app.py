import logging
from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.responses import JSONResponse

from auth import Token, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, User, \
    get_current_active_user, get_password_hash, UserInDB, get_user
from loader import create_dispatcher, ListenerException, DispatcherException
from models import Logs
from database import logs_collection, users_collection
from schemas import Event, CreateUser
from services import detect_strategy, filtering_by_strategy, EvalStrategyError, get_destinations

app = FastAPI()

logger = logging.getLogger('uvicorn.error')


@app.post("/ping-post")
async def pint():
    return {"pong": "post"}


@app.get("/ping-get")
async def pint():
    return {"pong": "get"}


@app.post("/event", dependencies=[Depends(get_current_active_user)])
async def process_event(event: Event):
    event = event.model_dump()

    # Get list of destination names from incoming routingIntents
    destinations_names = [routing.get("destinationName") for routing in event.get("routingIntents")]

    # Get Destination dict {name: obj} from database by destinations_names
    destinations = await get_destinations(destinations_names)

    # Central objects task_map. At map wee mark permission for process Intents.
    task_map = {
        d: {
            "in_db": d in destinations,
            "approved": False,
            "destinations": destinations.get(d)
        }
        for d in destinations_names
    }

    # Выбираем стратегию фильтрации
    # Choice strategy for filtering by incoming strategy field
    strategy = await detect_strategy(event)

    # Try to accept strategy
    try:
        approved_list = filtering_by_strategy(event.get("routingIntents"), strategy)
    except EvalStrategyError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "exception": e.__class__.__name__,
                "error": str(e)
            }
        )

    # Mark who strategy allowed
    approved_names_list = {item.get('destinationName') for item in approved_list}
    for k, v in task_map.items():
        if k in approved_names_list:
            v["approved"] = True

    # Create list of destinations by full approved ( approved + in_db )
    task = [item.get('destinations') for item in task_map.values() if item.get('approved') and item.get('in_db')]

    # Create EventDispatcher for creating handlers
    try:
        dispatcher = create_dispatcher(task)
    except ListenerException as e:
        logger.error(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "exception": e.__class__.__name__,
                "error": str(e)
            }
        )

    # Send incoming Intents by destinations
    try:
        resul = await dispatcher.dispatch(event)
    except DispatcherException as e:
        logger.error(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "exception": e.__class__.__name__,
                "error": str(e)
            }
        )

    # Logging
    logs_collection.insert_many([Logs(**r).model_dump() for r in resul])

    # Logging errors and skipped destinations
    for k, v in task_map.items():
        if not v.get('approved') and v.get('in_db'):
            logger.info(f"[{k}] skipped")

        if not v.get('in_db'):
            logger.info(f"UnknownDestinationError ({k})")

    # Prepare response
    response = {k: True if v.get('approved') and v.get('in_db') else False for k, v in task_map.items()}

    return response


@app.post("/users/create", response_model=User)
async def create_user(user: CreateUser):
    u = await get_user(users_collection, user.username)

    if u:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "username": "Already exists",
            }
        )

    hashed_password = get_password_hash(user.password)
    create_user_data = UserInDB(username=user.username, hashed_password=hashed_password).model_dump()

    result = await users_collection.insert_one(create_user_data)
    created_user = await users_collection.find_one({"_id": result.inserted_id})

    return created_user


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(users_collection, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

