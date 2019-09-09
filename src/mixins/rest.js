import Vue from 'vue';

function json(response) {
  return response.json();
}

const post = function (url, data) {
  data.csrf_token = window.$cookies.get('csrf_token');
  const promise = new Promise(((resolve, reject) => {
    fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }).then(json).then((data) => {
      resolve(data);
    }).catch((error) => {
      reject(error);
    });
  }));
  return promise;
};

Vue.mixin({ methods: { post } });

export default { post };
