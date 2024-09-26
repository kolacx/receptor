from typing import List

from database import strategies_collection, destinations_collection


class EvalStrategyError(ValueError):
    pass


async def detect_strategy(event: dict) -> str:
    strategy = event.get("strategy")
    if strategy is None:
        result = await strategies_collection.find_one({"name": 'ALL'})
        if result:
            strategy = result.get('python_code')

    strategy_by_name = await strategies_collection.find_one({"name": strategy})

    if strategy_by_name is not None:
        strategy = strategy_by_name.get('python_code')

    return strategy


def filtering_by_strategy(routing_intents, strategy: str) -> List:
    safe_globals = {"__builtins__": None}
    try:
        result = eval(strategy, safe_globals)(routing_intents)
    except Exception as e:
        raise EvalStrategyError(f"{e} - {strategy}")

    return result


async def get_destinations(destinations_names: list) -> dict:
    destinations_cursor = destinations_collection.find({
        "destinationName": {"$in": destinations_names}
    })
    return {item.get('destinationName'): item async for item in destinations_cursor}
