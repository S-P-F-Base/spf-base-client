import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Lock, Thread

logger = logging.getLogger(__name__)


@dataclass
class TimerTask:
    tag: str
    func: Callable[[], None]
    repeat_interval: float
    next_run: float
    repeat_count: int | None = None


class TimerManager:
    _is_initialized: bool = False
    _tasks: list[TimerTask] = []

    _thread: Thread | None = None
    _stop_event: Event = Event()
    _lock: Lock = Lock()

    @classmethod
    def initialize(cls) -> None:
        if cls._is_initialized:
            return

        cls._stop_event.clear()
        cls._thread = Thread(target=cls._timer_worker, daemon=True)
        cls._thread.start()
        cls._is_initialized = True

    @classmethod
    def stop(cls) -> None:
        cls._stop_event.set()

        if cls._thread:
            cls._thread.join()

        cls._is_initialized = False

    @classmethod
    def add_timer(
        cls,
        tag: str,
        func: Callable[[], None],
        interval: float,
        repeat_count: int | None = None,
    ):
        obj = TimerTask(
            tag=tag,
            func=func,
            repeat_interval=interval,
            next_run=time.monotonic() + interval,
            repeat_count=repeat_count,
        )

        with cls._lock:
            cls._tasks.append(obj)

    @classmethod
    def remove_timer(cls, tag: str):
        with cls._lock:
            cls._tasks = [t for t in cls._tasks if t.tag != tag]

    @classmethod
    def tick(cls):
        now = time.monotonic()
        with cls._lock:
            for task in cls._tasks[:]:
                if now >= task.next_run:
                    try:
                        task.func()
                    except Exception as e:
                        logger.error(f"Error in timer {task.tag}: {e}")

                    if task.repeat_count is not None:
                        task.repeat_count -= 1
                        if task.repeat_count <= 0:
                            cls._tasks.remove(task)
                            continue

                    task.next_run = now + task.repeat_interval

    @classmethod
    def _timer_worker(cls) -> None:
        while not cls._stop_event.is_set():
            cls.tick()
            time.sleep(0.01)
