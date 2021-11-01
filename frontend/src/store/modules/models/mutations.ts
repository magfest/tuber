import { MutationTree } from 'vuex'

import { Badge, Department } from '../../../lib/interfaces'

import { State } from './state'

export enum ModelMutationTypes {
  SET_BADGES = 'SET_BADGES',
  SET_DEPARTMENTS = 'SET_DEPARTMENTS',
}

export type Mutations<S = State> = {
  [ModelMutationTypes.SET_BADGES](state: S, badges: Badge[]): void;
  [ModelMutationTypes.SET_DEPARTMENTS](state: S, departments: Department[]): void;
}

export const mutations: MutationTree<State> & Mutations = {
  [ModelMutationTypes.SET_BADGES] (state, badges) {
    state.badges = badges
  },
  [ModelMutationTypes.SET_DEPARTMENTS] (state, departments) {
    state.departments = departments
  }
}
