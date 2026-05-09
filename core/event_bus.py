import threading
from typing import Callable, Dict, List
from utils.logger import logger

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable):
        with self._lock:
            self._subscribers.setdefault(event_name, []).append(callback)
        logger.debug(f"Subscribed to event: {event_name}")

    def emit(self, event_name: str, **kwargs):
        with self._lock:
            listeners = self._subscribers.get(event_name, []).copy()
        for cb in listeners:
            try:
                cb(**kwargs)
            except Exception as e:
                logger.error(f"Event {event_name} callback failed: {e}")
        logger.debug(f"Emitted event: {event_name}")

event_bus = EventBus()