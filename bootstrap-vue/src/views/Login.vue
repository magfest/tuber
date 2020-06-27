<template>
  <div class="container">
    <b-form @submit="onSubmit" @reset="onReset">
      <b-form-group
        id="email-form-group"
        label="Email"
        label-for="email-input"
        description="Email address used for login to Tuber"
      >
        <b-form-input
          id="email-input"
          v-model="form.email"
          type="email"
          required
          placeholder="Enter Email"
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
          email: '',
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
            username: this.form.email,
            password: this.form.password
          }
        )
      },

      onReset(evt){
        evt.preventDefault()
        this.form.email = '';
        this.form.password = '';
      }
    }
  };
</script>

<style scoped>

</style>
