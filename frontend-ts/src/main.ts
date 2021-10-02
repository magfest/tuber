import { createApp } from 'vue'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'

import 'primevue/resources/themes/saga-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

const app = createApp(App)

app.use(PrimeVue)
app.use(ToastService)

app.component('InputText', { name: 'InputText', ...InputText })
app.component('Button', { name: 'Button', ...Button })
app.component('Toast', { name: 'Toast', ...Toast })

app.mount('#app')
