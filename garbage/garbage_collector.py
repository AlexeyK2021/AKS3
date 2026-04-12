import asyncio
import signal

from data_livecycle_controller import GarbageCollector
from DatabaseController import db_manager


async def main():
    gc = GarbageCollector(db_manager.session_factory)

    stop_event = asyncio.Event()

    def shutdown():
        stop_event.set()

    loop = asyncio.get_running_loop()

    try:
        loop.add_signal_handler(signal.SIGTERM, shutdown)
        loop.add_signal_handler(signal.SIGINT, shutdown)
    except NotImplementedError:
        pass

    task = asyncio.create_task(gc.run_forever())

    print("GC worker started")

    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received")

    print("Stopping GC...")
    await gc.stop()
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())