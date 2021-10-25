<template>
    <div class="card">
        <Toast />
        <h3>Please Log In</h3>
        <form @action.prevent>
          <div class="field grid">
              <label for="username" class="col-fixed" style="width:100px">Username</label>
              <div class="col">
                  <InputText id="username" v-model="user.username" type="text" />
              </div>
          </div>
          <div class="field grid">
              <label for="password" class="col-fixed" style="width:100px">Password</label>
              <div class="col">
                  <InputText id="password" v-model="user.password" type="password" />
              </div>
          </div>
          <Button type="submit" @click="login">Login</button>
        </form>
    </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { AppActionTypes } from '../store/modules/app/actions'

@Options({
  name: 'Login',
  components: {
  },
  data: () => ({
    user: {
      username: '',
      password: ''
    }
  }),
  methods: {
    login: async function () {
      this.$store.dispatch(AppActionTypes.LOGIN, this.user).then(() => {
        if (this.$route.name === 'logout') {
          this.$router.push('/')
        }
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Login Failed', detail: 'Incorrect username or password. Please try again.' })
      })
    }
  }
})
export default class Login extends Vue {}
</script>
