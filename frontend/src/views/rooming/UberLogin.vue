<template>
<div>
  <h3 v-if="!showForm">Please wait while we authenticate your session against Uber...</h3>
  <div v-else class="card">
      <h3>Please provide your staffing information to log in to the rooming system</h3>

  </div>
</div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { mapGetters } from 'vuex'
import { post } from '../../lib/rest'
import { AppActionTypes } from '../../store/modules/app/actions'

export default {
  name: 'uber-login',
  components: {
  },
  data () {
    return {
      showForm: false
    }
  },
  computed: {
    ...mapGetters([
      'event'
    ]),
    uberID () {
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.has('id')) {
        return urlParams.get('id')
      } else {
        return null
      }
    },
    eventID () {
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.has('event')) {
        return urlParams.get('event')
      } else {
        return null
      }
    }
  },
  watch: {
    uberID () {
      this.uberlogin()
    }
  },
  mounted () {
    this.uberlogin()
  },
  methods: {
    uberlogin () {
      post('/api/uber/' + this.eventID + '/login', { token: this.uberID }).then((session) => {
        this.$store.dispatch(AppActionTypes.GET_LOGGED_IN)
        this.$router.push('/rooming/request')
      }).catch((e) => {
        this.showForm = true
      })
    }
  }
}
</script>
