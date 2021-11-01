import { Badge, Department } from '../../../lib/interfaces'

export type State = {
  badges: Badge[],
  departments: Department[]
}

export const state: State = {
  badges: [],
  departments: []
}
