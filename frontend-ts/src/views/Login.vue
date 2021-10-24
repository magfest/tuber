<template>
    <div class="card">
        <h3>Please Log In</h3>
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
        <Button type="button" @click="login">Login</button>
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
      })
    }
  }
})
export default class Login extends Vue {}
</script>
