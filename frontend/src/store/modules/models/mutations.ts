import { MutationTree } from 'vuex'

import { Badge, Department, BadgeType } from '../../../lib/interfaces'
import { ModelActionTypes } from './actions'

import { State } from './state'

export enum ModelMutationTypes {
  SET_BADGES = 'SET_BADGES',
  SET_DEPARTMENTS = 'SET_DEPARTMENTS',
  SET_BADGETYPES = 'SET_BADGETYPES'
}

export type Mutations<S = State> = {
  [ModelMutationTypes.SET_BADGES](state: S, badges: Badge[]): void;
  [ModelMutationTypes.SET_DEPARTMENTS](state: S, departments: Department[]): void;
  [ModelMutationTypes.SET_BADGETYPES](state: S, badgeTypes: BadgeType[]): void;
}

export const mutations: MutationTree<State> & Mutations = {
  [ModelMutationTypes.SET_BADGES] (state, badges) {
    state.badges = badges
  },
  [ModelMutationTypes.SET_DEPARTMENTS] (state, departments) {
    state.departments = departments
  },
  [ModelMutationTypes.SET_BADGETYPES] (state, badgeTypes) {
    state.badgeTypes = badgeTypes
  }
}
