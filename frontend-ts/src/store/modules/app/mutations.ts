import { MutationTree } from 'vuex'

import { User, Event } from '../../../lib/interfaces'

import { State } from './state'

export enum AppMutationTypes {
    SET_LOGIN = 'SET_LOGIN',
    SET_USER = 'SET_USER',
    SET_EVENT = 'SET_EVENT',
    SET_EVENTS = 'SET_EVENTS',
    SET_INITIAL_SETUP = 'SET_INITIAL_SETUP'
}

export type Mutations<S = State> = {
    [AppMutationTypes.SET_LOGIN](state: S, payload: boolean): void;
    [AppMutationTypes.SET_USER](state: S, payload: User | null): void;
    [AppMutationTypes.SET_EVENT](state: S, payload: Event | null): void;
    [AppMutationTypes.SET_EVENTS](state: S, payload: Event[]): void;
    [AppMutationTypes.SET_INITIAL_SETUP](state: S, payload: boolean): void;
}

export const mutations: MutationTree<State> & Mutations = {
  [AppMutationTypes.SET_LOGIN] (state, loggedIn) {
    state.loggedIn = loggedIn
  },
  [AppMutationTypes.SET_USER] (state, user) {
    state.user = user
  },
  [AppMutationTypes.SET_EVENT] (state, event) {
    state.event = event
  },
  [AppMutationTypes.SET_EVENTS] (state, events) {
    state.events = events
  },
  [AppMutationTypes.SET_INITIAL_SETUP] (state, initialSetup) {
    state.initialSetup = initialSetup
  }
}
