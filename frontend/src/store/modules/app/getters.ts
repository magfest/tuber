import { GetterTree } from 'vuex'

import { RootState } from '@/store'

import { User, Event, Badge } from '@/lib/interfaces'

import { State } from './state'

export type Getters = {
    loggedIn(state: State): boolean | null;
    initialSetup(state: State): boolean | null;
    user(state: State): User | null;
    badge(state: State): Badge | null;
    event(state: State): Event | null;
    events(state: State): Event[];
    permissions(state: State): {[key:string]: string[]};
    departmentPermissions(state: State): {[key:string]: {[key:string]: string[]}};
}

export const getters: GetterTree<State, RootState> & Getters = {
  loggedIn: (state) => state.loggedIn,
  initialSetup: (state) => state.initialSetup,
  user: (state) => state.user,
  badge: (state) => state.badge,
  event: (state) => state.event,
  events: (state) => state.events,
  permissions: (state) => state.permissions,
  departmentPermissions: (state) => state.departmentPermissions
}
