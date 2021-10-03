<template>
  <div id="app">
    <div class="app-container">
      <img alt="Vue logo" src="./assets/logo.png">
      <HelloWorld msg="Welcome to Your PrimeVue App"/>
      <form @submit.prevent="slow">
        <InputText name="nameinput" type="text"/>
        <Button type="submit" label="Submit"/>
      </form>
      <form @submit.prevent="fast">
        <InputText name="nameinput" type="text"/>
        <Button type="submit" label="Submit"/>
      </form>
      <LoadingBar ref="loadingbar"></LoadingBar>
    </div>

    <Toast/>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import LoadingBar from './components/LoadingBar.vue'
import { get } from './lib/rest'

@Options({
  data () {
    return {
    }
  },
  methods: {
    slow () {
      get('/api/slow', {}, this.$refs.loadingbar.update).then((response) => {
        this.$toast.add({
          severity: 'info',
          summary: 'All done!'
        })
      })
    },
    fast () {
      get('/api/fast', {}, this.$refs.loadingbar.update).then((response) => {
        this.$toast.add({
          severity: 'info',
          summary: 'All done!'
        })
      })
    }
  },
  components: {
    LoadingBar
  }
})
export default class App extends Vue {}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 60px;
}
.app-container {
  text-align: center;
}
body #app .p-button {
  margin-left: .2em;
}
form {
  margin-top: 2em;
}
</style>
