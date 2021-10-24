<template>
  <div class="card">
    <h3>Create an Admin User</h3>
    <p>This user will have full access to the server, and can be used to create additional users.</p>
    <div class="field grid">
        <label for="username" class="col-fixed" style="width:100px">Username</label>
        <div class="col">
            <InputText id="username" v-model="user.username" type="text" />
        </div>
    </div>
    <div class="field grid">
        <label for="email" class="col-fixed" style="width:100px">Email</label>
        <div class="col">
            <InputText id="email" v-model="user.email" type="text" />
        </div>
    </div>
    <div class="field grid">
        <label for="password" class="col-fixed" style="width:100px">Password</label>
        <div class="col">
            <InputText id="password" v-model="user.password" type="password" />
        </div>
    </div>
    <div class="grid justify-content-between">
      <div></div>
      <Button label="Continue" @click="createUser" icon="pi pi-angle-right" iconPos="right" />
    </div>
  </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { post } from '../../lib/rest'
import { AppActionTypes } from '../../store/modules/app/actions'

@Options({
  name: 'SetupUser',
  data: () => ({
    user: {
      username: '',
      email: '',
      password: ''
    }
  }),
  methods: {
    createUser: async function () {
      try {
        await post('/api/initial_setup', this.user)
        await this.$store.dispatch(AppActionTypes.LOGIN, { username: this.user.username, password: this.user.password })
        this.$emit('nextPage')
      } catch (e) {
        console.log('Failed to setup user!', e)
      } finally {
        console.log('resetting')
      }
    }
  }
})
export default class SetupUser extends Vue {}
</script>
