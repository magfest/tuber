import { User, Event, Badge } from '../../../lib/interfaces'

export type State = {
  initialSetup: boolean,
  loggedIn: boolean,
  user: User | null,
  badge: Badge | null,
  event: Event | null,
  events: Event[],
  permissions: {[key:string]: string[]},
  departmentPermissions: {[key:string]: {[key:string]: string[]}}
}

export const state: State = {
  initialSetup: false,
  loggedIn: false,
  user: null,
  badge: null,
  event: null,
  events: [],
  permissions: {},
  departmentPermissions: {}
}
