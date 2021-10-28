import { MutationTree } from 'vuex'

import { User, Event, Badge } from '../../../lib/interfaces'

import { State } from './state'

export enum AppMutationTypes {
    SET_LOGIN = 'SET_LOGIN',
    SET_USER = 'SET_USER',
    SET_BADGE = 'SET_BADGE',
    SET_EVENT = 'SET_EVENT',
    SET_EVENTS = 'SET_EVENTS',
    SET_INITIAL_SETUP = 'SET_INITIAL_SETUP',
    SET_PERMISSIONS = 'SET_PERMISSIONS'
}

export type Mutations<S = State> = {
    [AppMutationTypes.SET_LOGIN](state: S, loggedIn: boolean): void;
    [AppMutationTypes.SET_USER](state: S, user: User | null): void;
    [AppMutationTypes.SET_BADGE](state: S, badge: Badge | null): void;
    [AppMutationTypes.SET_EVENT](state: S, event: Event | null): void;
    [AppMutationTypes.SET_EVENTS](state: S, events: Event[]): void;
    [AppMutationTypes.SET_INITIAL_SETUP](state: S, initialSetup: boolean): void;
    [AppMutationTypes.SET_PERMISSIONS](state: S, permissions: {event: {[key:string]: string[]}, department: {[key:string]: {[key:string]: string[]}}}): void;
}

export const mutations: MutationTree<State> & Mutations = {
  [AppMutationTypes.SET_LOGIN] (state, loggedIn) {
    state.loggedIn = loggedIn
  },
  [AppMutationTypes.SET_USER] (state, user) {
    state.user = user
  },
  [AppMutationTypes.SET_BADGE] (state, badge) {
    if (badge) {
      state.events.forEach((event) => {
        if (badge.event === event.id) {
          state.event = event
        }
      })
    }
    state.badge = badge
  },
  [AppMutationTypes.SET_EVENT] (state, event) {
    state.event = event
  },
  [AppMutationTypes.SET_EVENTS] (state, events) {
    state.events = events
  },
  [AppMutationTypes.SET_INITIAL_SETUP] (state, initialSetup) {
    state.initialSetup = initialSetup
  },
  [AppMutationTypes.SET_PERMISSIONS] (state, permissions) {
    state.departmentPermissions = permissions.department
    state.permissions = permissions.event
  }
}
