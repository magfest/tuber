import { createApp } from 'vue'
import App from './App.vue'
import { VueCookieNext } from 'vue-cookie-next'
import PrimeVue from 'primevue/config'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import ProgressBar from 'primevue/progressbar'

import 'primevue/resources/themes/saga-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

import store from './store'

const app = createApp(App)
app.use(VueCookieNext)
app.use(PrimeVue)
app.use(ToastService)
app.use(store)

app.component('InputText', { name: 'InputText', ...InputText })
app.component('Button', { name: 'Button', ...Button })
app.component('Toast', { name: 'Toast', ...Toast })
app.component('ProgressBar', { name: 'ProgressBar', ...ProgressBar })

app.mount('#app')
