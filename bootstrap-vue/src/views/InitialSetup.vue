<template>
  <div>
    <b-form @submit="setup">
      <b-form-group
        label="Username"
        label-for="username-input"
        description="Username for initial admin account"
      >
        <b-form-input
          id="username-input"
          v-model="username"
          required
        ></b-form-input>
      </b-form-group>
      <b-form-group
        label="Password"
        label-for="password-input"
      >
        <b-form-input
          id="password-input"
          v-model="password"
          type="password"
          required
        />
      </b-form-group>
      <b-form-group
        label="Email"
        label-for="email-input"
        description="Email for admin account"
      >
        <b-form-input
          id="email-input"
          type="email"
          v-model="email"
          required
        />
      </b-form-group>
      <div class="d-flex">
        <b-btn class="ml-auto" variant="success" type="submit">
          Create Admin Account
        </b-btn>
      </div>
    </b-form>
  </div>
</template>

<script>
  import axios from 'axios';

  export default {
    name: 'InitialSetup',
    data(){
      return {
        username: '',
        password: '',
        email: ''
      }
    },

    methods: {
      setup(evt){
        evt.preventDefault();
        axios.post('/initial_setup', {
          username: this.username,
          password: this.password,
          email: this.email
        })
          .then(response => {
            this.$notify({
              group: 'main',
              title: 'Success',
              text: 'Initial setup complete'
            })
            this.$emit('setup')
          })
          .catch(() => {
            this.$notify({
              group: 'main',
              title: 'error',
              text: 'Something went wrong during initial setup'
            })
          })
      }
    }

  };
</script>

<style scoped>

</style>
