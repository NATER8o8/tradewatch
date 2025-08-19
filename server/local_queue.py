
import threading, time, uuid, traceback
from typing import Any, Callable, Dict, List, Optional

class LocalJob:
    def __init__(self, func: Callable, args: tuple, kwargs: dict):
        self.id = uuid.uuid4().hex
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = "queued"
        self.created_at = time.time()
        self.enqueued_at = time.time()
        self.started_at = None
        self.ended_at = None
        self.result = None
        self.exc_info = None
        self.meta: Dict[str, Any] = {}

    def get_status(self) -> str:
        return self.status

    def return_value(self):
        return self.result

class LocalQueue:
    def __init__(self):
        self.jobs: Dict[str, LocalJob] = {}
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._queue: List[str] = []
        self.running = True
        self.worker.start()

    def enqueue(self, func: Callable, *args, **kwargs) -> LocalJob:
        j = LocalJob(func, args, kwargs)
        with self.lock:
            self.jobs[j.id] = j
            self._queue.append(j.id)
        return j

    def _worker_loop(self):
        while self.running:
            j: Optional[LocalJob] = None
            with self.lock:
                if self._queue:
                    jid = self._queue.pop(0)
                    j = self.jobs.get(jid)
            if not j:
                time.sleep(0.1); continue
            j.status = "started"; j.started_at = time.time()
            try:
                j.result = j.func(*j.args, **j.kwargs)
                j.status = "finished"
            except Exception as e:
                j.exc_info = traceback.format_exc()
                j.status = "failed"
            j.ended_at = time.time()

    def get_job(self, job_id: str) -> Optional[LocalJob]:
        return self.jobs.get(job_id)

    def list_job_ids(self) -> List[str]:
        with self.lock:
            return list(self.jobs.keys())

# singleton
QUEUE = LocalQueue()
