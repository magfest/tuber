import { GetterTree } from 'vuex'

import { RootState } from '@/store'

import { Badge } from '@/lib/interfaces'

import { State } from './state'

export type Getters = {
  badgeLookup(state: State): {[key:number]: Badge}
  badges(state: State): Badge[]
}

export const getters: GetterTree<State, RootState> & Getters = {
  badgeLookup: (state) => {
    const lookup: {[key:number]: Badge} = {}
    state.badges.forEach((badge: Badge) => {
      lookup[badge.id] = badge
    })
    return lookup
  },
  badges: (state) => state.badges
}
