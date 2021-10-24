import { GetterTree } from 'vuex'

import { RootState } from '@/store'

import { User, Event } from '@/lib/interfaces'

import { State } from './state'

export type Getters = {
    loggedIn(state: State): boolean;
    initialSetup(state: State): boolean;
    user(state: State): User | null;
    event(state: State): Event | null;
    events(state: State): Event[];
}

export const getters: GetterTree<State, RootState> & Getters = {
  loggedIn: (state) => state.loggedIn,
  initialSetup: (state) => state.initialSetup,
  user: (state) => state.user,
  event: (state) => state.event,
  events: (state) => state.events
}
