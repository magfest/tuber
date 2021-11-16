import { GetterTree } from 'vuex'

import { RootState } from '@/store'

import { Badge, Department, BadgeType } from '@/lib/interfaces'

import { State } from './state'

export type Getters = {
  badgeLookup(state: State): {[key:number]: Badge},
  badges(state: State): Badge[],
  departmentLookup(state: State): {[key:number]: Department},
  departments(state: State): Department[],
  badgeTypes(state: State): BadgeType[],
  badgeTypeLookup(state: State): {[key:number]: BadgeType}
}

export const getters: GetterTree<State, RootState> & Getters = {
  badgeLookup: (state) => {
    const lookup: {[key:number]: Badge} = {}
    state.badges.forEach((badge: Badge) => {
      lookup[badge.id] = badge
    })
    return lookup
  },
  badges: (state) => state.badges,
  departmentLookup: (state) => {
    const lookup: {[key:number]: Department} = {}
    state.departments.forEach((department: Department) => {
      lookup[department.id] = department
    })
    return lookup
  },
  departments: (state) => state.departments,
  badgeTypes: (state) => state.badgeTypes,
  badgeTypeLookup: (state) => {
    const lookup: {[key:number]: BadgeType} = {}
    state.badgeTypes.forEach((badgeType: BadgeType) => {
      lookup[badgeType.id] = badgeType
    })
    return lookup
  }

}
