import multiprocessing.pool
import threading
import traceback
import json
import uuid
import time
from werkzeug.routing import RequestRedirect
from tuber import config
from tuber.database import db, r
from tuber.models import *
from tuber.permissions import *

class AsyncMiddleware(object):

    def __init__(self, application):
        self.application = application
        print(f"Activating circuitbreaker with {config.circuitbreaker_threads} threads")
        self.pool = multiprocessing.pool.ThreadPool(processes=config.circuitbreaker_threads)
        self.lock = threading.Lock()
        self.context = dict()

        @application.before_request
        def add_progress():
            if not hasattr(g, "progress"):
                g.progress = self.progress

        @application.route("/api/slow", methods=["GET"])
        def slow_call():
            if check_permission("circuitbreaker.*.test"):
                for i in range(10):
                    time.sleep(1)
                    g.progress(i*0.1, f"Doing a thing (part {i} / 10)")
                events = db.query(Event).all()
                return jsonify(Event.serialize(events, g)), 200
            return "Permission Denied", 403

        @application.route("/api/fast", methods=["GET"])
        def fast_call():
            if check_permission("circuitbreaker.*.test"):
                time.sleep(0.1)
                events = db.query(Event).all()
                return jsonify(Event.serialize(events, g)), 200
            return "Permission Denied", 403

        @application.route("/api/fastfail", methods=["GET"])
        def fast_fail_call():
            if check_permission("circuitbreaker.*.test"):
                time.sleep(0.1)
                raise ValueError("This is an intentional exception.")
            return "Permission Denied", 403

        @application.route("/api/slowfail", methods=["GET"])
        def slow_fail_call():
            if check_permission("circuitbreaker.*.test"):
                time.sleep(10)
                raise ValueError("This is an intentional exception.")
            return "Permission Denied", 403

    def __del__(self):
        self.pool.close()
        self.pool.terminate()

    def get_view_function(self, path, method):
        adapter = self.application.url_map.bind('localhost')

        try:
            match = adapter.match(path, method=method)
        except RequestRedirect as e:
            # recursively match redirects
            return self.get_view_function(e.new_url, method)
        except:
            # no match
            return None

        try:
            # return the view function and arguments
            return app.view_functions[match[0]]
        except KeyError:
            # no view is associated with the endpoint
            return None

    def __call__(self, environ, start_response):
        # If the function says it's a generator then we just return it immediately
        func = self.get_view_function(environ['PATH_INFO'], environ['REQUEST_METHOD'])
        if func and hasattr(func, "generator") and getattr(func, "generator"):
            return self.application(environ, start_response)
        
        if environ['PATH_INFO'].startswith("/api/job/"):
            job_id = environ['PATH_INFO'].split("/api/job/")[1]
            if r:
                progress = json.loads(r.get(f"{job_id}/progress"))
                if not progress:
                    start_response("404 Not Found", [])
                    return [bytes()]
                if not progress['complete']:
                    headers = [("Content-Type", "application/json")]
                    if config.circuitbreaker_refresh:
                        headers.append(("Refresh", str(config.circuitbreaker_refresh)))
                    start_response("202 Accepted", headers)
                    return [json.dumps(progress).encode()]
                data = r.get(f"{job_id}/data")
                context = json.loads(r.get(f"{job_id}/context"))
                start_response(context['status'], context['response_headers'])
                return [data]
            else:
                job = db.query(BackgroundJob).filter(BackgroundJob.uuid == job_id).one_or_none()
                if not job:
                    start_response("404 Not Found", [])
                    return [bytes()]
                else:
                    progress = json.loads(job.progress)
                    if progress['complete']:
                        context = json.loads(job.context)
                        start_response(context['status'], context['response_headers'])
                        return [job.result]
                    start_response("202 Accepted", [("Content-Type", "application/json")])
                    return [job.progress.encode()]
        job_id = str(uuid.uuid4())
        request_context = {
            "state": "pending",
            "status": "202 Accepted",
            "response_headers": [("Location", f"/api/job/{job_id}")]
        }
        with self.lock:
            if len(self.context) > config.circuitbreaker_threads:
                start_response("504 Gateway Timeout", [])
                return [bytes()]
            self.context[job_id] = request_context

        thread = self.pool.apply_async(
            self.application,
            (environ, lambda *args, **kwargs: self._start_response(job_id, *args, **kwargs)),
            callback=lambda *args, **kwargs: self._store_response(job_id, *args, **kwargs),
            error_callback=lambda *args, **kwargs: self._store_response(job_id, *args, **kwargs)
        )
        thread.wait(timeout=config.circuitbreaker_timeout)

        with self.lock:
            start_response(request_context['status'], request_context['response_headers'])
            if request_context['state'] == "immediate":
                del self.context[job_id]
                try:
                    return thread.get()
                except:
                    traceback.print_exc()
                    return ["Backend error".encode('UTF-8')]
            request_context['state'] = "deferred"
            progress = environ.get("TUBER_JOB_PROGRESS", '{"complete": false, "amount": 0, "status": "", "messages": ""}')
            if r:
                r.set(f"{job_id}/progress", progress)
            else:
                job = BackgroundJob(uuid=job_id, progress=progress)
                db.add(job)
                db.commit()
            environ['TUBER_JOB_ID'] = job_id
        return [bytes()]

    def _start_response(self, job_id, status, response_headers, *args, **kwargs):
        with self.lock:
            self.context[job_id]['status'] = status
            self.context[job_id]['response_headers'] = response_headers
        def _write(_):
            raise NotImplemented("This middleware only supports iterable results.")
        return _write

    def _store_response(self, job_id, iterable):
        if isinstance(iterable, Exception):
            iterable = traceback.format_exception(None, iterable, iterable.__traceback__)
            print("".join(iterable))
            self.context[job_id]['status'] = "500 INTERNAL SERVER ERROR"
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
            "complete": True,
            "amount": 0,
            "messages": "",
            "status": ""
        })
        if r:
            r.set(f"{job_id}/context", request_context)
            for data in iterable:
                r.append(f"{job_id}/data", data)
            r.set(f"{job_id}/progress", progress)
        else:
            data = bytes()
            for chunk in iterable:
                if isinstance(chunk, str):
                    chunk = chunk.encode('UTF-8')
                data = data + chunk
            with self.lock:
                job = db.query(BackgroundJob).filter(BackgroundJob.uuid == job_id).one_or_none()
                if not job:
                    return
                job.progress = progress
                job.result = data
                job.context = request_context
                db.add(job)
                db.commit()

    def progress(self, amount, status=""):
        with self.lock:
            job_id = request.environ.get("TUBER_JOB_ID", "")
            if not job_id:
                prior_progress = json.loads(request.environ.get("TUBER_JOB_PROGRESS", '{"complete": false, "amount": 0, "status": "", "messages": ""}'))
                prior_progress['amount'] = amount
                prior_progress['status'] = status
                prior_progress['messages'] += status + "\n"
                request.environ["TUBER_JOB_PROGRESS"] = json.dumps(prior_progress)
                return
            if r:
                progress = json.loads(r.get(f"{job_id}/progress"))
                progress['amount'] = amount
                if status:
                    progress['status'] = status
                    progress['messages'] += status + "\n"
                r.set(f"{job_id}/progress", json.dumps(progress))
            else:
                job = db.query(BackgroundJob).filter(BackgroundJob.uuid == job_id).one_or_none()
                progress = json.loads(job.progress)
                progress['amount'] = amount
                if status:
                    progress['status'] = status
                    progress['messages'] += status + "\n"
                job.progress = json.dumps(progress)
                db.add(job)
                db.commit()