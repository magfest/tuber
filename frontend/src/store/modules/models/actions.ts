import { ActionTree, ActionContext } from 'vuex'

import { RootState } from '@/store'

import { State } from './state'
import { Mutations, ModelMutationTypes } from './mutations'

import { Badge, Department, BadgeType } from '@/lib/interfaces'
import { get } from '@/lib/rest'

export enum ModelActionTypes {
  LOAD_DEPARTMENTS = 'LOAD_DEPARTMENTS',
  LOAD_BADGETYPES = 'LOAD_BADGETYPES'
}

type AugmentedActionContext = {
  commit<K extends keyof Mutations>(
    key: K,
    payload: Parameters<Mutations[K]>[1],
  ): ReturnType<Mutations[K]>;
} & Omit<ActionContext<State, RootState>, 'commit'>

export interface Actions {
  [ModelActionTypes.LOAD_DEPARTMENTS]({ commit }: AugmentedActionContext): Promise<void>;
  [ModelActionTypes.LOAD_BADGETYPES]({ commit }: AugmentedActionContext): Promise<void>;
}

export const actions: ActionTree<State, RootState> & Actions = {
  async [ModelActionTypes.LOAD_DEPARTMENTS] ({ commit, rootState }) {
    if (rootState.app.event) {
      return get('/api/event/' + rootState.app.event.id + '/department').then((departments: Department[]) => {
        commit(ModelMutationTypes.SET_DEPARTMENTS, departments)
      })
    }
  },
  async [ModelActionTypes.LOAD_BADGETYPES] ({ commit, rootState }) {
    if (rootState.app.event) {
      return get('/api/event/' + rootState.app.event.id + '/badge_type').then((badgetypes: BadgeType[]) => {
        commit(ModelMutationTypes.SET_BADGETYPES, badgetypes)
      })
    }
  }
}
