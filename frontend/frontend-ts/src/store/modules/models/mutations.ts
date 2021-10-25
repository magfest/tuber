import { MutationTree } from 'vuex'

import { Badge } from '../../../lib/interfaces'

import { State } from './state'

export enum ModelMutationTypes {
  SET_BADGES = 'SET_BADGES',
}

export type Mutations<S = State> = {
  [ModelMutationTypes.SET_BADGES](state: S, badges: Badge[]): void;
}

export const mutations: MutationTree<State> & Mutations = {
  [ModelMutationTypes.SET_BADGES] (state, badges) {
    state.badges = badges
  }
}
