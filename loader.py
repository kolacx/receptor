import asyncio
import aiohttp
import logging

from abc import ABC, abstractmethod

logger = logging.getLogger('uvicorn.error')


class ListenerException(Exception):
    pass


class ListenerURLException(ListenerException):
    pass


class DispatcherException(Exception):
    pass


class EventListener(ABC):

    def __init__(self, **kwargs):
        self.destination_name = kwargs.get("destinationName")
        self.transport = kwargs.get('transport')

    @abstractmethod
    async def handle(self, event: dict):
        pass


class LogINFOEventListener(EventListener):
    async def handle(self, event: dict):
        msg = f"payload sent to [{self.destination_name}] via [{self.transport}] transport"
        logger.info(msg)
        return {
            "destination": self.destination_name,
            "transport": self.transport,
            "strategy": event.get('strategy')
        }


class LogWARNINGEventListener(EventListener):
    async def handle(self, event: dict):
        msg = f"payload sent to [{self.destination_name}] via [{self.transport}] transport"
        logger.info(msg)
        return {
            "destination": self.destination_name,
            "transport": self.transport,
            "strategy": event.get('strategy')
        }


class HttpPOSTEventListener(EventListener):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_url = kwargs.get("url", None)
        if self.api_url is None:
            raise ListenerURLException(f"Destinations [{self.destination_name}] without url")

    async def handle(self, event: dict):
        async with aiohttp.request('POST', url=self.api_url, json=event.get("payload")) as response:
            r = await response.json()
        msg = f"payload sent to [{self.destination_name}] via [{self.transport}] transport"
        logger.info(msg)
        return {
            "destination": self.destination_name,
            "transport": self.transport,
            "request": event.get("payload"),
            "response": r,
            "url": self.api_url,
            "strategy": event.get('strategy')
        }


class HttpPUTEventListener(EventListener):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_url = kwargs.get("url", None)
        if self.api_url is None:
            raise ListenerURLException(f"Destinations [{self.destination_name}] without url")

    async def handle(self, event: dict):
        async with aiohttp.request('PUT', url=self.api_url, json=event.get("payload")) as response:
            r = await response.json()
        msg = f"payload sent to [{self.destination_name}] via [{self.transport}] transport"
        logger.info(msg)
        return {
            "destination": self.destination_name,
            "transport": self.transport,
            "request": event.get("payload"),
            "response": r,
            "url": self.api_url,
            "strategy": event.get('strategy')
        }


class HttpGETEventListener(EventListener):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_url = kwargs.get("url", None)
        if self.api_url is None:
            raise ListenerURLException(f"Destinations [{self.destination_name}] without url")

    async def handle(self, event: dict):
        async with aiohttp.request('GET', url=self.api_url) as response:
            r = await response.json()
        msg = f"payload sent to [{self.destination_name}] via [{self.transport}] transport"
        logger.info(msg)
        return {
            "destination": self.destination_name,
            "transport": self.transport,
            "request": event,
            "response": r,
            "url": self.api_url,
            "strategy": event.get('strategy')
        }


class EventDispatcher:
    def __init__(self, listeners):
        self.listeners = listeners

    async def dispatch(self, event):
        listeners = [listener.handle(event) for listener in self.listeners]
        try:
            response = await asyncio.gather(*listeners)
            return response
        except Exception as e:
            raise DispatcherException(f"Fatal handle destination: {e}")


# http.post, https.put, http.get, log.info, log.warn
listeners_map = {
    'http.post': HttpPOSTEventListener,
    'http.put': HttpPUTEventListener,
    'http.get': HttpGETEventListener,
    'log.info': LogINFOEventListener,
    'log.warn': LogWARNINGEventListener,
}


def create_dispatcher(destinations) -> EventDispatcher:
    listeners = []
    for destination in destinations:
        listener_class = listeners_map.get(destination.get("transport"), None)
        if listener_class is None:
            raise ListenerException(f"Listener for [{destination.get("transport")}] dose not exists")
        listeners.append(listener_class(**destination))

    return EventDispatcher(listeners)
