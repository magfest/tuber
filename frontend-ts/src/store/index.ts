import { createStore } from 'vuex'

import { store as app, AppStore, State as AppState } from './modules/app'

const debug = process.env.NODE_ENV !== 'production'

export type RootState = {
  app: AppState;
};

export const store = createStore({
  modules: {
    app
  },
  strict: debug
})

export type Store = AppStore<Pick<RootState, 'app'>>;

export function useStore (): Store {
  return store as Store
}
