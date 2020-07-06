<template>
  <div id="app" class="d-flex flex-column">
    <div class="backgroundImage" :style="{'background-image': `url(${imageUrl})`}"></div>
    <notifications group="main"/>
    <Navbar/>
    <div class="mt-3 container">
      <InitialSetup v-if="initialSetup" @setup="checkSetup"/>
      <router-view class="slow" v-else/>
    </div>
    <Footer class="mt-auto"/>
  </div>
</template>

<script>
  import axios from 'axios';
  import Navbar from './components/Navbar/Navbar';
  import Footer from "./components/Footer";
  import InitialSetup from './views/InitialSetup';


  export default {
    components: { InitialSetup, Navbar, Footer },
    data(){
      return {
        initialSetup: true,
      }
    },

    mounted(){
      this.checkLogin();
      this.checkSetup();
    },

    computed: {
      imageUrl() {
        return require("@/assets/magfestwave.png");
      }
    },

    methods: {
      checkLogin(){
        axios.get('check_login')
          .then(() => {
            this.$store.dispatch('events/getEvents')
          })
          .catch((e) => {
            if (this.$route.name !== 'Login'){
              this.$router.push({name: 'Login'})
            }
          })
      },

      checkSetup(){
        axios.get('check_initial_setup')
          .then(response => {
            this.initialSetup = response.data
          })
      }
    }

  }

</script>

<style>
.backgroundImage {
  background-repeat: no-repeat;
  background-attachment: fixed;
  background-size: contain;
  background-position: center;
  content: "";
  opacity: 0.04;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  position: absolute;
  z-index: -1;
}

#app{
  min-height: 100vh;
  position: relative;
}

.slow {
  animation: slow 1s ease forwards;
}

@keyframes slow {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

</style>
