import { Store } from '../store'

declare module '@vue/runtime-core' {
  // declare your own store states
  interface State {
    app: App
  }

  // provide typings for `this.$store`
  interface ComponentCustomProperties {
    $store: Store
  }
}
