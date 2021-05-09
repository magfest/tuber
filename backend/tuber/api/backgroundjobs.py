from flask import request, jsonify, g, _request_ctx_stack, Response
from tuber.models import *
from tuber.permissions import *
from tuber import app, db, config, r
import json
import time
import uuid

if config.enable_circuitbreaker:
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(processes=config.circuitbreaker_threads)

@app.route("/api/slow", methods=["GET"])
def slow_call():
    if check_permission("circuitbreaker.test"):
        for i in range(10):
            time.sleep(1)
            g.progress(i*0.1)
        return "success", 200
    return "Permission Denied", 403

@app.route("/api/fast", methods=["GET"])
def fast_call():
    if check_permission("circuitbreaker.test"):
        time.sleep(0.1)
        return "success", 200
    return "Permission Denied", 403

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    if not g.session:
        return "Permission Denied", 403
    if r:
        if 'job' in request.args:
            progress = json.loads(r.get(f"{g.session}/{request.args['job']}/progress"))
            if not progress:
                return "", 404
            result = None
            if 'complete' in progress:
                if progress['complete']:
                    result = json.loads(r.get(f"{g.session}/{request.args['job']}/result"))
            return jsonify(result=result, progress=progress)
        else:
            jobs = {}
            for key in r.scan_iter(match=f"{g.session}/*/progress", count=5):
                session, job, _ = key.decode('UTF-8').split("/")
                progress = json.loads(r.get(key) or "null")
                result = json.loads(r.get(f"{session}/{job}/result") or "null")
                jobs[key.decode('UTF-8').split("/")[1]] = {
                    "progress": progress,
                    "result": result
                }
            return jsonify(jobs)
    else:
        if 'job' in request.args:
            job = db.session.query(BackgroundJob).filter(BackgroundJob.uuid == request.args['job'], BackgroundJob.session == g.session).one_or_none()
            if not job:
                return "", 404
            return jsonify(result=json.loads(job.result or "{}"), progress=json.loads(job.progress))
        else:
            jobs = {}
            for job in db.session.query(BackgroundJob).filter(BackgroundJob.session == g.session).all():
                jobs[job.uuid] = {
                    "progress": json.loads(job.progress),
                    "result": json.loads(job.result or "{}")
                }
            return jsonify(jobs)

@app.route("/api/jobs/<jobid>", methods=["GET"])
def get_job(jobid):
    if r:
        if not r.exists(f"{g.session}/{jobid}/progress"):
            return "", 404
        result = r.get(f"{g.session}/{jobid}/result")
        if not result:
            return "", 202
        result = json.loads(result)
    else:
        job = db.session.query(BackgroundJob).filter(BackgroundJob.uuid == jobid, BackgroundJob.session == g.session).one()
        if not job:
            return "", 404
        if not job.result:
            return "", 202
        result = json.loads(job.result)
    if result['mimetype'] == "application/json":
        return jsonify(result['data']), result['status_code']
    return result['data'], result['status_code']

# This wraps all view functions with a circuit breaker that allows soft timeouts.
# Basically, if a view function takes more than the timeout to render a page then
# the client gets a 202 and receives a claim ticket while the view function keeps
# running in the background. The result gets pushed to either redis or the sql db
# and the client can retrieve it (or the status while it's pending) later.
#
# The main design goal is for this to be transparent to people writing flask view
# functions, so make sure the environment matches whether this wrapper is enabled
# or not.
#
# View functions that often take a long time can be made aware of this behavior
# and can push status/progress updates into the job while they work.
def job_wrapper(func):
    def wrapped(*args, **kwargs):
        def yo_dawg(request_context, before_request_funcs):
            with app.test_request_context(**request_context):
                for before_request_func in before_request_funcs:
                    before_request_func()
                def progress(amount, status_msg=""):
                    if not hasattr(g, "log"):
                        g.log = status_msg
                    elif status_msg:
                        g.log += "\n" + status_msg
                    status = {
                        "progress": amount,
                        "status": status_msg,
                        "log": g.log,
                        "complete": False
                    }
                    if r:
                        r.set(f"{g.session}/{jobid}/progress", json.dumps(status))
                    else:
                        job = db.session.query(BackgroundJob).filter(BackgroundJob.uuid == jobid).one_or_none()
                        if job:
                            job.progress = json.dumps(status)
                            db.session.add(job)
                            db.session.commit()
                g.progress = progress
                return func(*args, **kwargs)
        request_context = {
            "path": request.path,
            "base_url": request.base_url,
            "query_string": request.query_string,
            "method": request.method,
            "headers": dict(request.headers),
            "data": g.raw_data,
        }
        start_time = time.time()
        jobid = str(uuid.uuid4())
        def store_result(ret, session):
            if time.time() - start_time > 0.9 * config.circuitbreaker_timeout:
                data = {}
                if type(ret) is Response:
                    resp = ret
                elif type(ret) is tuple:
                    resp = Response(ret[0], ret[1])
                elif type(ret) is str:
                    resp = Response(ret)
                if resp.mimetype == "application/json":
                    data['data'] = resp.json
                else:
                    data['data'] = resp.data.decode('UTF-8')
                data['mimetype'] = resp.mimetype
                data['execution_time'] = time.time() - start_time
                data['headers'] = dict(resp.headers)
                data['status_code'] = resp.status_code
                stored = json.dumps(data)
                if r:
                    r.set(f"{session}/{jobid}/result", stored)
                    progress = r.get(f"{session}/{jobid}/progress")
                    if progress:
                        progress = json.loads(progress)
                    else:
                        progress = {}
                    progress['complete'] = True
                    r.set(f"{session}/{jobid}/progress", json.dumps(progress))
                else:
                    job = db.session.query(BackgroundJob).filter(BackgroundJob.uuid == jobid).one_or_none()
                    if not job:
                        job = BackgroundJob(uuid=jobid, progress=json.dumps({"complete": True}))
                    job.result = stored
                    progress = json.loads(job.progress)
                    progress['complete'] = True
                    job.progress = json.dumps(progress)
                    db.session.add(job)
                    db.session.commit()
        session = g.session
        result = pool.apply_async(yo_dawg, (request_context, app.before_request_funcs[None]), callback=lambda x: store_result(x, session))
        result.wait(timeout=config.circuitbreaker_timeout)
        if result.ready():
            return result.get()
        else:
            if r:
                r.set(f"{g.session}/{jobid}/progress", json.dumps({"complete": False}))
            else:
                job = BackgroundJob(uuid=jobid, session=g.session, progress=json.dumps({"complete": False}))
                db.session.add(job)
                db.session.commit()
            return jsonify(job=jobid), 202
    return wrapped

if config.enable_circuitbreaker:
    for key, val in app.view_functions.items():
        if val in [get_job, get_jobs]:
            continue
        app.view_functions[key] = job_wrapper(val)