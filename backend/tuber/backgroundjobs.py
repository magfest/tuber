import multiprocessing.pool
import threading
import json
import uuid
import time
from tuber import config
from tuber.database import db, r
from tuber.models import *
from tuber.permissions import *

class AsyncMiddleware(object):

    def __init__(self, application):
        self.application = application
        self.pool = multiprocessing.pool.ThreadPool(processes=config.circuitbreaker_threads)
        self.lock = threading.Lock()
        self.context = dict()

        @application.route("/api/slow", methods=["GET"])
        def slow_call():
            if check_permission("circuitbreaker.test"):
                for i in range(10):
                    time.sleep(1)
                    # g.progress(i*0.1)
                events = db.query(Event).all()
                return jsonify(Event.serialize(events, g)), 200
            return "Permission Denied", 403

        @application.route("/api/fast", methods=["GET"])
        def fast_call():
            if check_permission("circuitbreaker.test"):
                time.sleep(0.1)
                events = db.query(Event).all()
                return jsonify(Event.serialize(events, g)), 200
            return "Permission Denied", 403

    def __del__(self):
        self.pool.close()
        self.pool.terminate()

    def __call__(self, environ, start_response):
        if environ['REQUEST_URI'].startswith("/api/job/"):
            job_id = environ['REQUEST_URI'].split("/api/job/")[1]
            if r:
                progress = json.loads(r.get(f"{job_id}/progress"))
                if not progress:
                    start_response("404 Not Found", [])
                    return ""
                if not progress['complete']:
                    start_response("202 Accepted", [("Content-Type", "application/json")])
                    return json.dumps(progress)
                data = r.get(f"{job_id}/data")
                start_response("200 Ok", [("Content-Type", "application/json")])
                return data
            else:
                job = db.query(BackgroundJob).filter(BackgroundJob.uuid == job_id).one_or_none()
                if not job:
                    start_response("404 Not Found", [])
                    return ""
                else:
                    progress = json.loads(job.progress)
                    if progress['complete']:
                        start_response("200 Ok", [("Content-Type", "application/json")])
                        return job.result.decode()
                    start_response("202 Accepted", [("Content-Type", "application/json")])
                    return job.progress
        job_id = str(uuid.uuid4())
        request_context = {
            "state": "pending",
            "status": "202 Accepted",
            "response_headers": [("Location", f"/api/job/{job_id}")]
        }
        with self.lock:
            if len(self.context) > config.circuitbreaker_threads:
                start_response("504 Gateway Timeout", [])
                return ""
            self.context[job_id] = request_context

        thread = self.pool.apply_async(
            self.application,
            (environ, lambda *args, **kwargs: self._start_response(job_id, *args, **kwargs)),
            callback=lambda *args, **kwargs: self._store_response(job_id, *args, **kwargs)
        )
        thread.wait(timeout=config.circuitbreaker_timeout)

        with self.lock:
            start_response(request_context['status'], request_context['response_headers'])
            if request_context['state'] == "immediate":
                del self.context[job_id]
                return thread.get()
            request_context['state'] = "deferred"
            progress = json.dumps({"complete": False})
            if r:
                r.set(f"{job_id}/progress", progress)
            else:
                job = BackgroundJob(uuid=job_id, progress=progress)
                db.add(job)
                db.commit()
        return ""

    def _start_response(self, job_id, status, response_headers, *args, **kwargs):
        with self.lock:
            self.context[job_id]['status'] = status
            self.context[job_id]['response_headers'] = response_headers
        def _write(_):
            raise NotImplemented("This middleware only supports iterable results.")
        return _write

    def _store_response(self, job_id, iterable):
        with self.lock:
            if self.context[job_id]['state'] == "pending":
                self.context[job_id]['state'] = "immediate"
                return
        request_context = json.dumps({
            "status": self.context[job_id]['status'],
            "response_headers": self.context[job_id]['response_headers']
        })
        del self.context[job_id]
        progress = json.dumps({
            "complete": True
        })
        if r:
            r.set(f"{job_id}/context", request_context)
            for data in iterable:
                r.append(f"{job_id}/data", data)
            r.set(f"{job_id}/progress", progress)
        else:
            data = bytes()
            for chunk in iterable:
                data = data + chunk
            with self.lock:
                job = db.query(BackgroundJob).filter(BackgroundJob.uuid == job_id).one()
                job.progress = progress
                job.result = data
                job.context = request_context
                db.add(job)
                db.commit()
