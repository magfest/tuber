<template>
    <form @submit.prevent>
        <div class="field">
            <label for="un">Username</label><br>
            <InputText id="un" autocomplete="off" v-model="user.username" /><br>
        </div><br>

        <div class="field">
            <label for="em">Email</label><br>
            <InputText id="em" autocomplete="off" v-model="user.email" /><br>
        </div><br>

        <div class="field">
            <label for="pa">Password</label><br>
            <InputText id="pa" type="password" autocomplete="new-password" v-model="newPassword" /><br>
            <small>Enter new password to reset it</small>
        </div><br>

        <div class="field">
            <label for="active">Active</label><br>
            <Checkbox id="active" v-model="user.active" :binary="true" /><br>
        </div><br>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'

export default {
  name: 'UserForm',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    newPassword: '',
    user: {
      username: '',
      email: '',
      active: false
    }
  }),
  computed: {
    ...mapGetters([
    ]),
    url () {
      if (this.id) {
        return '/api/user/' + this.id
      }
      return '/api/user'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    load () {
      if (this.id) {
        get(this.url).then((user) => {
          this.user = user
        })
      }
    },
    async save () {
      try {
        let newuser = {}
        if (this.id) {
          newuser = await patch(this.url, this.user)
        } else {
          newuser = await post(this.url, this.user)
        }
        if (this.newPassword) {
          await post('/api/change_password/' + newuser.id, { password: this.newPassword })
        }
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      }
    }
  },
  watch: {
  }
}
</script>
