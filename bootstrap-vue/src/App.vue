<template>
  <div id="app" class="d-flex flex-column">
    <div class="backgroundImage" :style="{'background-image': `url(${imageUrl})`}"></div>
    <Navbar/>
    <router-view class="slow mt-3 container"/>
    <Footer class="mt-auto"/>
  </div>
</template>

<script>
  import axios from 'axios';
  import Navbar from './components/Navbar/Navbar';
  import Footer from "./components/Footer"; 


  export default {
    components: { Navbar, Footer },
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
    },

      computed: {
    imageUrl() {
      return require("@/assets/magfestwave.png");
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
  opacity: 0.1;
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