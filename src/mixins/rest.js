import Vue from 'vue';

function json(response) {
  return response.json();
}

function post(url, data) {
  if (data === undefined) {
    data = {};
  }
  const promise = new Promise(((resolve, reject) => {
    data.csrf_token = window.$cookies.get('csrf_token');
    fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      credentials: 'include',
    }).then(json).then((data) => {
      resolve(data);
    }).catch((error) => {
      reject(error);
    });
  }));
  return promise;
}

function dodelete(url, data) {
  if (data === undefined) {
    data = {};
  }
  const promise = new Promise(((resolve, reject) => {
    data.csrf_token = window.$cookies.get('csrf_token');
    fetch(url, {
      method: 'DELETE',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      credentials: 'include',
    }).then(json).then((data) => {
      resolve(data);
    }).catch((error) => {
      reject(error);
    });
  }));
  return promise;
}

function get(url, data) {
  if (data === undefined) {
    data = {};
  }
  const promise = new Promise(((resolve, reject) => {
    data.csrf_token = window.$cookies.get('csrf_token');

    const queryString = `?${Object.keys(data).map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`).join('&')}`;
    const fullUrl = url + queryString;
    fetch(fullUrl, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      credentials: 'include',
    }).then(json).then((data) => {
      resolve(data);
    }).catch((error) => {
      reject(error);
    });
  }));
  return promise;
}

Vue.mixin({ methods: { post, get, dodelete } });

export { post, get, dodelete };
