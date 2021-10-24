import { User, Event } from '../../../lib/interfaces'

export type State = {
  initialSetup: boolean,
  loggedIn: boolean,
  user: User | null,
  event: Event | null,
  events: Event[],
}

export const state: State = {
  initialSetup: false,
  loggedIn: false,
  user: null,
  event: null,
  events: []
}
