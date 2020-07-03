<template>
  <div class="container">
    <b-form @submit="onSubmit" @reset="onReset">
      <b-form-group
        id="username-form-group"
        label="Username"
        label-for="username-input"
        description="Username address used for login to Tuber"
      >
        <b-form-input
          id="username-input"
          v-model="form.username"
          required
          placeholder="Enter username"
        />
      </b-form-group>
      <b-form-group
        id="password-form-group"
        label="Password"
        label-for="password-input"
        description="Never share your password with others"
      >
        <b-form-input
          id="password-input"
          v-model="form.password"
          type="password"
          required
        />
      </b-form-group>
      <b-btn
        variant="success"
        type="submit"
      >Login</b-btn>
      <b-btn
        variant="danger"
        type="reset"
      >Cancel</b-btn>
    </b-form>
  </div>
</template>

<script>
  import axios from 'axios';

  export default {
    name: 'Login',
    data(){
      return {
        form: {
          username: '',
          password: ''
        }
      }
    },

    methods: {
      onSubmit(evt){
        evt.preventDefault()
        axios.post(
          'login',
          {
            username: this.form.username,
            password: this.form.password
          }
        )
      },

      onReset(evt){
        evt.preventDefault()
        this.form.username = '';
        this.form.password = '';
      }
    }
  };
</script>

<style scoped>

</style>
