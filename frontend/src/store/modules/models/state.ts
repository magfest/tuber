import { Badge, Department, BadgeType } from '../../../lib/interfaces'

export type State = {
  badges: Badge[],
  departments: Department[],
  badgeTypes: BadgeType[]
}

export const state: State = {
  badges: [],
  departments: [],
  badgeTypes: []
}
