<template>
  <div class="card">
    <h3>Welcome to Tuber!</h3>
    <p>Tuber is an open source events management system, and will handle registration, volunteers, and more!</p>
    <p>It appears this server is being set up for the first time. This wizard will guide you through configuring your new server. If this is not what you expect please confirm your installation has access to its database.</p>
    <div class="grid justify-content-between">
      <div></div>
      <Button label="Continue" @click="$emit('nextPage')" icon="pi pi-angle-right" iconPos="right" />
    </div>
  </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'

export default class SetupWelcome extends Vue {}
</script>
