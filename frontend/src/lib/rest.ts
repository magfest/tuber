import { VueCookieNext } from 'vue-cookie-next'

interface ProgressTracker {
  update: (job: String, progress: Progress) => null,
  stop_job: (job: String) => null
}

interface Progress {
  amount: number,
  status: string,
  messages: string,
  active: boolean,
  definite: boolean
}

interface OptProgress {
  amount?: number,
  status?: string,
  messages?: string,
  active?: boolean,
  definite?: boolean,
  name?: string
}

async function wait (ms: number): Promise<null> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function setProgress (job: String, progress?: ProgressTracker, current?: OptProgress) {
  if (progress) {
    const defaultProgress = {
      amount: 0,
      status: '',
      messages: '',
      active: true,
      definite: false,
      name: ''
    }
    if (current) {
      Object.assign(defaultProgress, current)
    }
    if (defaultProgress.amount) {
      defaultProgress.definite = true
    }
    progress.update(job, defaultProgress)
  }
}

async function pollJob (response: Response, jobid: String, progressTracker?: ProgressTracker, name?: string): Promise<Response> {
  let delay = 100
  const url = response.headers.get('location')
  if (!url) {
    throw new Error('Could not find job id.')
  }
  let currentAmount = 0
  setProgress(jobid, progressTracker, {name: name})
  let job = await fetch(url)
  while (job.status === 202) {
    const progress = await job.json()
    if (currentAmount === progress.amount) {
      delay = delay * 1.5
    }
    let refresh = job.headers.get('Refresh')
    if (refresh !== null) {
      delay = parseFloat(refresh) * 1000
      delay = Math.max(100, delay)
    }
    currentAmount = progress.amount
    progress.name = name
    setProgress(jobid, progressTracker, progress)
    await wait(delay)
    job = await fetch(url)
  }
  if (job.status > 202) {
    setProgress(jobid, progressTracker, {amount: 1, status: "Failed ("+job.status+")", messages: await job.text(), name: name})
  }
  return job
}

async function restFetch (method: string, url: string, data?: any, progressTracker?: ProgressTracker, name?: string): Promise<any> {
  if (!data) {
    data = {}
  }
  let jobid = new Array(5).join().replace(/(.|$)/g, function(){return ((Math.random()*36)|0).toString(36);})
  setProgress(jobid, progressTracker, {name: name})

  const headers: { [key: string]: string } = {
    Accept: 'application/json',
    'CSRF-Token': VueCookieNext.getCookie('csrf_token')
  }

  if (method === 'GET') {
    const queryString = `?${Object.keys(data).map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`).join('&')}`
    url += queryString
  } else {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    method,
    headers,
    body: method === 'GET' ? null : JSON.stringify(data),
    credentials: 'include'
  })

  if (response.status === 200) {
    if (progressTracker) {
      progressTracker.stop_job(jobid)
    }
    return await response.json()
  } else if (response.status === 202) {
    const job = await pollJob(response, jobid, progressTracker, name)
    let result = await job.json()
    progressTracker?.stop_job(jobid)
    return result
  } else {
    const msg = await response.text()
    throw new Error(msg)
  }
}

async function get (url: string, data?: any, progressTracker?: ProgressTracker, name?: string): Promise<any> {
  return await restFetch('GET', url, data, progressTracker, name)
}

async function post (url: string, data?: any, progressTracker?: ProgressTracker, name?: string): Promise<any> {
  return await restFetch('POST', url, data, progressTracker, name)
}

async function patch (url: string, data?: any, progressTracker?: ProgressTracker, name?: string): Promise<any> {
  return await restFetch('PATCH', url, data, progressTracker, name)
}

async function del (url: string, data?: any, progressTracker?: ProgressTracker, name?: string): Promise<any> {
  return await restFetch('DELETE', url, data, progressTracker, name)
}

export {
  get,
  post,
  patch,
  del,
  Progress
}
