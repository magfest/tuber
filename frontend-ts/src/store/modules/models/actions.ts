import { ActionTree, ActionContext } from 'vuex'

import { RootState } from '@/store'

import { State } from './state'
import { Mutations, ModelMutationTypes } from './mutations'

import { Badge } from '@/lib/interfaces'
import { get } from '@/lib/rest'

export enum ModelActionTypes {
  LOAD_BADGES = 'LOAD_BADGES'
}

type AugmentedActionContext = {
  commit<K extends keyof Mutations>(
    key: K,
    payload: Parameters<Mutations[K]>[1],
  ): ReturnType<Mutations[K]>;
} & Omit<ActionContext<State, RootState>, 'commit'>

export interface Actions {
  [ModelActionTypes.LOAD_BADGES]({ commit }: AugmentedActionContext): Promise<void>;
}

export const actions: ActionTree<State, RootState> & Actions = {
  async [ModelActionTypes.LOAD_BADGES] ({ commit, rootState }) {
    console.log('Getting badges', rootState)
    if (rootState.app.event) {
      return get('/api/event/' + rootState.app.event.id + '/badge').then((badges: Badge[]) => {
        commit(ModelMutationTypes.SET_BADGES, badges)
      })
    }
  }
}
