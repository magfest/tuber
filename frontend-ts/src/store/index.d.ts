declare module '@vue/runtime-core' {
  // declare your own store states
  interface State {
    setup: Setup
  }

  // provide typings for `this.$store`
  interface ComponentCustomProperties {
    $store: Store<State>
  }
}
