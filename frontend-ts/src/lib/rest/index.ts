import { VueCookieNext } from 'vue-cookie-next'

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
  definite?: boolean
}

async function wait (ms: number): Promise<null> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function setProgress (progress?: (n: Progress) => any, current?: OptProgress) {
  if (progress) {
    const defaultProgress = {
      amount: 0,
      status: '',
      messages: '',
      active: true,
      definite: false
    }
    if (current) {
      Object.assign(defaultProgress, current)
    }
    if (defaultProgress.amount) {
      defaultProgress.definite = true
    }
    progress(defaultProgress)
  }
}

async function pollJob (response: Response, progressCB?: (n: Progress) => any): Promise<Response> {
  let delay = 100
  const url = response.headers.get('location')
  if (!url) {
    throw new Error('Could not find job id.')
  }
  let currentAmount = 0
  setProgress(progressCB)
  let job = await fetch(url)
  while (job.status === 202) {
    const progress = await job.json()
    if (currentAmount === progress.amount) {
      delay = delay * 1.5
    }
    currentAmount = progress.amount
    setProgress(progressCB, progress)
    await wait(delay)
    job = await fetch(url)
  }
  setProgress(progressCB, { active: false })
  return job
}

async function restFetch (method: string, url:string, data?: any, progressCB?: (n: Progress) => any): Promise<any> {
  if (!data) {
    data = {}
  }
  setProgress(progressCB, { active: true })

  if (method === 'GET') {
    const queryString = `?${Object.keys(data).map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`).join('&')}`
    url += queryString
  }
  const response = await fetch(url, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      "CSRF-Token": VueCookieNext.getCookie('csrf_token')
    },
    credentials: 'include'
  })

  if (response.status === 200) {
    setProgress(progressCB, { active: false })
    return await response.json()
  } else if (response.status === 202) {
    const job = await pollJob(response, progressCB)
    return await job.json()
  } else {
    throw new Error('GET: ' + url + ' ' + response.status)
  }
}

async function get (url:string, data?: any, progressCB?: (n: Progress) => any): Promise<any> {
  return await restFetch('GET', url, data, progressCB)
}

async function post (url:string, data?: any, progressCB?: (n: Progress) => any): Promise<any> {
  return await restFetch('POST', url, data, progressCB)
}

async function patch (url:string, data?: any, progressCB?: (n: Progress) => any): Promise<any> {
  return await restFetch('PATCH', url, data, progressCB)
}

async function del (url:string, data?: any, progressCB?: (n: Progress) => any): Promise<any> {
  return await restFetch('DELETE', url, data, progressCB)
}

export {
  get,
  post,
  patch,
  del,
  Progress
}
