<template>
  <div id="app">
    <div class="app-container">
      <img alt="Vue logo" src="./assets/logo.png">
      <HelloWorld msg="Welcome to Your PrimeVue App"/>
      <form @submit.prevent="greet">
        <InputText name="nameinput" type="text" v-model="text"/>
        <Button type="submit" label="Submit"/>
        <h3>{{message}}</h3>
      </form>
    </div>

    <Toast/>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import HelloWorld from './components/HelloWorld.vue'

@Options({
  data () {
    return {
      message: null,
      text: null
    }
  },
  methods: {
    greet () {
      this.$toast.add({ severity: 'info', summary: 'Hello ' + this.text })
      this.message = 'Hello ' + this.text
    }
  },
  components: {
    HelloWorld
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
