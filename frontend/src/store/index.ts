import { createStore } from 'vuex'

import { store as app, AppStore, State as AppState } from './modules/app'
import { store as model, ModelStore, State as ModelState } from './modules/models'

const debug = import.meta.env.NODE_ENV !== 'production'

export type RootState = {
  app: AppState;
  model: ModelState;
};

export const store = createStore({
  modules: {
    app,
    model
  },
  strict: debug
})

export type Store = AppStore<Pick<RootState, 'app'>>
 & ModelStore<Pick<RootState, 'model'>>;

export function useStore (): Store {
  return store as Store
}
