import Vue from 'vue';

function restFetch(method, url, data) {
  if (data === undefined) {
    data = {};
  }
  data.csrf_token = window.$cookies.get('csrf_token');
  if (method === 'GET') {
    const queryString = `?${Object.keys(data).map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`).join('&')}`;
    url += queryString;
    return fetch(url, {
      method,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    }).then(response => response.json());
  }
  return fetch(url, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    credentials: 'include',
  }).then(response => response.json());
}

const schema = {
  events: {
    url: '/api/events',
  },
  users: {
    url: '/api/users',
  },
  badges: {
    url: '/api/events/<event>/badges',
  },
  departments: {
    url: '/api/events/<event>/departments',
  },
  emails: {
    url: '/api/events/<event>/emails',
  },
  email_sources: {
    url: '/api/events/<event>/email_sources',
  },
  grants: {
    url: '/api/grants',
  },
  roles: {
    url: '/api/roles',
  },
  permissions: {
    url: '/api/permissions',
  },
};

function get(url, data) {
  return restFetch('GET', url, data);
}

function post(url, data) {
  return restFetch('POST', url, data);
}

function list(endpoint) {
  const url = schema[endpoint].url.replace('<event>', this.$store.getters.event.id);
  return restFetch('GET', url);
}

function load(endpoint, id) {
  const url = schema[endpoint].url.replace('<event>', this.$store.getters.event.id);
  return restFetch('GET', `${url}/${id}`);
}

function dump(endpoint) {
  const url = schema[endpoint].url.replace('<event>', this.$store.getters.event.id);
  return new Promise((resolve, reject) => {
    restFetch('GET', url, { full: true }).then((result) => {
      const mapping = {};
      for (let i = 0; i < result.length; i += 1) {
        mapping[result[i].id] = result[i];
      }
      resolve(mapping);
    }).catch(() => {
      reject(new Error(`Failed to dump ${endpoint}`));
    });
  });
}

function save(endpoint, data) {
  const url = schema[endpoint].url.replace('<event>', this.$store.getters.event.id);
  if (Object.prototype.hasOwnProperty.call(data, 'id')) {
    // Already has id, therefore this is an update.
    return restFetch('PATCH', `${url}/${data.id}`, data).then(() => {
      if (Object.prototype.hasOwnProperty.call(this.$asyncComputed, endpoint)) {
        this.$asyncComputed[endpoint].update();
      }
    });
  }
  // Doesn't have an id, therefore this is creating an object.
  return restFetch('POST', url, data).then(() => {
    if (Object.prototype.hasOwnProperty.call(this.$asyncComputed, endpoint)) {
      this.$asyncComputed[endpoint].update();
    }
  });
}

function remove(endpoint, data) {
  const url = schema[endpoint].url.replace('<event>', this.$store.getters.event.id);
  return restFetch('DELETE', `${url}/${data.id}`).then(() => {
    if (Object.prototype.hasOwnProperty.call(this.$asyncComputed, endpoint)) {
      this.$asyncComputed[endpoint].update();
    }
  });
}

function mapAsync(endpoints) {
  const functions = {};
  for (let i = 0; i < endpoints.length; i += 1) {
    functions[endpoints[i]] = {
      get() {
        const url = schema[endpoints[i]].url.replace('<event>', this.$store.getters.event.id);
        if (this.$store.getters.event.id === undefined) {
          return new Promise((resolve) => {
            resolve([]);
          });
        }
        return restFetch('GET', url);
      },
      default: [],
    };
  }
  return functions;
}

function mapAsyncDump(endpoints) {
  const functions = {};
  for (let i = 0; i < endpoints.length; i += 1) {
    functions[endpoints[i]] = {
      get() {
        const url = schema[endpoints[i]].url.replace('<event>', this.$store.getters.event.id);
        if (this.$store.getters.event.id === undefined) {
          return new Promise((resolve) => {
            resolve([]);
          });
        }
        return restFetch('GET', url, { full: true });
      },
      default: [],
    };
  }
  return functions;
}

function mapAsyncObjects(endpoints) {
  const functions = {};
  for (let i = 0; i < endpoints.length; i += 1) {
    functions[endpoints[i]] = {
      get() {
        const url = schema[endpoints[i]].url.replace('<event>', this.$store.getters.event.id);
        return new Promise((resolve, reject) => {
          if (this.$store.getters.event.id === undefined) {
            resolve({});
          }
          restFetch('GET', url, { full: true }).then((result) => {
            const mapping = {};
            for (let i = 0; i < result.length; i += 1) {
              mapping[result[i].id] = result[i];
            }
            resolve(mapping);
          }).catch(() => {
            reject(new Error(`Failed to dump ${endpoints[i]}`));
          });
        });
      },
      default: {},
    };
  }
  return functions;
}

Vue.mixin({
  methods: {
    restFetch, mapAsync, mapAsyncObjects, save, remove, load, dump, list, get, mapAsyncDump, post,
  },
});

export {
  restFetch, mapAsync, mapAsyncObjects, save, remove, load, dump, list, get, mapAsyncDump, post,
};
