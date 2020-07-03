<template>
  <div id="app">
    <Navbar/>
    <router-view class="container mt-3"/>
  </div>
</template>

<script>
  import axios from 'axios';
  import Navbar from './components/Navbar/Navbar';

  export default {
    components: { Navbar },
    data(){
      return {
      }
    },

    mounted(){
      axios.get('check_login')
        .then(() => {
          this.$store.dispatch('events/getEvents')
        })
        .catch((e) => {
          if (this.$route.name !== 'Login'){
            this.$router.push({name: 'Login'})
          }
        })
    }
  }
</script>

<style lang="scss">
</style>
