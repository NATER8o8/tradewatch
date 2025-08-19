
from typing import Dict, Any, List
import os
try:
    from rq import Queue
    RQ_OK = True
except Exception:
    RQ_OK = False
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry, ScheduledJobRegistry, DeferredJobRegistry
from .tasks import get_queue
from .local_queue import QUEUE as LQ

def _status_of(job: Job) -> str:
    try:
        return job.get_status() or "unknown"
    except Exception:
        return "unknown"

def job_info(job_id: str) -> Dict[str, Any]:
    q = get_queue()
    if q is None:
        j = LQ.get_job(job_id)
        if not j:
            raise Exception('job not found')
        return {
            "id": j.id,
            "status": j.status,
            "created_at": j.created_at,
            "enqueued_at": j.enqueued_at,
            "started_at": j.started_at,
            "ended_at": j.ended_at,
            "func_name": getattr(j.func, "__name__", str(j.func)),
            "args": j.args,
            "kwargs": j.kwargs,
            "result": j.result,
            "exc_info": j.exc_info,
            "meta": j.meta,
        }
    job = Job.fetch(job_id, connection=q.connection)
    info = {
        "id": job.id,
        "status": _status_of(job),
        "created_at": str(job.created_at) if job.created_at else None,
        "enqueued_at": str(job.enqueued_at) if job.enqueued_at else None,
        "started_at": str(getattr(job, "started_at", None)) if getattr(job, "started_at", None) else None,
        "ended_at": str(getattr(job, "ended_at", None)) if getattr(job, "ended_at", None) else None,
        "func_name": job.func_name,
        "args": job.args,
        "kwargs": job.kwargs,
        "result": job.return_value() if hasattr(job, "return_value") else None,
        "exc_info": job.exc_info,
        "meta": job.meta or {},
    }
    return info

def list_jobs(limit: int = 25) -> List[Dict[str, Any]]:
    q = get_queue()
    if q is None:
        return [{"id": jid, "status": LQ.get_job(jid).status} for jid in LQ.list_job_ids()[:limit]]
    registries = [
        ("queued", [j.id for j in q.jobs]),
        ("started", StartedJobRegistry(queue=q).get_job_ids()),
        ("finished", FinishedJobRegistry(queue=q).get_job_ids()),
        ("failed", FailedJobRegistry(queue=q).get_job_ids()),
        ("scheduled", ScheduledJobRegistry(queue=q).get_job_ids()),
        ("deferred", DeferredJobRegistry(queue=q).get_job_ids()),
    ]
    out = []
    for status, ids in registries:
        for j in ids[:limit]:
            out.append({"id": j, "status": status})
            if len(out) >= limit:
                return out
    return out
