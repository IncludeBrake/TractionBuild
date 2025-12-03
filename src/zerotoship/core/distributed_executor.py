"""
Distributed Executor for concurrent crew execution.
"""
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

class DistributedExecutor:
    def __init__(self, crew_router, max_workers=5):
        self.crew_router = crew_router
        self.max_workers = max_workers
        self.queue = asyncio.Queue()
        self.workers = []
        self.futures = {}
        self._started = False

    async def schedule(self, state, context, project_data):
        if not self._started:
            raise RuntimeError("Executor has not been started.")
            
        task_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self.futures[task_id] = future
        await self.queue.put((task_id, state, context, project_data))
        logger.info(f"Scheduled task {task_id} for state {state}")
        return await future

    async def worker(self):
        while True:
            task_id, state, context, project_data = await self.queue.get()
            logger.info(f"Worker picked up task {task_id} for state {state}")
            try:
                result = await self.crew_router.execute(state, context, project_data)
                if task_id in self.futures:
                    self.futures[task_id].set_result(result)
            except Exception as e:
                logger.exception(f"Task {task_id} failed with exception: {e}")
                if task_id in self.futures:
                    self.futures[task_id].set_exception(e)
            finally:
                if task_id in self.futures:
                    del self.futures[task_id]
                self.queue.task_done()

    async def start(self):
        if self._started:
            return
        self.workers = [asyncio.create_task(self.worker()) for _ in range(self.max_workers)]
        self._started = True
        logger.info(f"DistributedExecutor started with {self.max_workers} workers.")

    async def stop(self):
        if not self._started:
            return
        await self.queue.join()
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self._started = False
        logger.info("DistributedExecutor stopped.")
