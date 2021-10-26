import { ActionTree, ActionContext } from 'vuex'

import { RootState } from '@/store'

import { State } from './state'
import { Mutations, AppMutationTypes } from './mutations'

import { Event, UserSession } from '@/lib/interfaces'
import { get, post } from '@/lib/rest'

export enum AppActionTypes {
    GET_INITIAL_SETUP = 'GET_INITIAL_SETUP',
    GET_LOGGED_IN = 'GET_LOGGED_IN',
    GET_EVENTS = 'GET_EVENTS',
    LOGOUT = 'LOGOUT',
    LOGIN = 'LOGIN',
    GET_PERMISSIONS = 'GET_PERMISSIONS'
}

type AugmentedActionContext = {
  commit<K extends keyof Mutations>(
    key: K,
    payload: Parameters<Mutations[K]>[1],
  ): ReturnType<Mutations[K]>;
} & Omit<ActionContext<State, RootState>, 'commit'>

export interface Actions {
    [AppActionTypes.GET_INITIAL_SETUP]({ commit }: AugmentedActionContext): Promise<void>;
    [AppActionTypes.GET_LOGGED_IN]({ commit }: AugmentedActionContext): Promise<void>;
    [AppActionTypes.GET_EVENTS]({ commit }: AugmentedActionContext): Promise<void>;
    [AppActionTypes.LOGOUT]({ dispatch }: AugmentedActionContext): Promise<void>;
    [AppActionTypes.LOGIN]({ dispatch }: AugmentedActionContext, user: {username: string, password: string}): Promise<void>;
    [AppActionTypes.GET_PERMISSIONS]({ dispatch }: AugmentedActionContext): Promise<void>;
}

export const actions: ActionTree<State, RootState> & Actions = {
  async [AppActionTypes.GET_INITIAL_SETUP] ({ commit }) {
    return get('/api/check_initial_setup').then((initialSetup: boolean) => {
      commit(AppMutationTypes.SET_INITIAL_SETUP, initialSetup)
    }).catch(() => {
      commit(AppMutationTypes.SET_INITIAL_SETUP, false)
    })
  },
  async [AppActionTypes.GET_LOGGED_IN] ({ commit, dispatch }) {
    return get('/api/check_login').then((userSession: UserSession) => {
      commit(AppMutationTypes.SET_USER, userSession.user)
      dispatch(AppActionTypes.GET_PERMISSIONS).then(() => {
        commit(AppMutationTypes.SET_LOGIN, true)
      })
    }).catch(() => {
      commit(AppMutationTypes.SET_LOGIN, false)
      commit(AppMutationTypes.SET_USER, null)
      dispatch(AppActionTypes.GET_PERMISSIONS)
    })
  },
  async [AppActionTypes.GET_EVENTS] ({ commit }) {
    return get('/api/event').then((events: Event[]) => {
      commit(AppMutationTypes.SET_EVENTS, events)
      if (events.length > 0) {
        commit(AppMutationTypes.SET_EVENT, events[0])
      } else {
        commit(AppMutationTypes.SET_EVENT, null)
      }
    }).catch(() => {
      commit(AppMutationTypes.SET_EVENT, null)
    })
  },
  async [AppActionTypes.LOGOUT] ({ dispatch }) {
    return post('/api/logout').then(() => {
      dispatch(AppActionTypes.GET_LOGGED_IN)
    })
  },
  async [AppActionTypes.LOGIN] ({ dispatch }, user: {username: string, password: string}) {
    return post('/api/login', user).then(() => {
      dispatch(AppActionTypes.GET_LOGGED_IN)
    })
  },
  async [AppActionTypes.GET_PERMISSIONS] ({ state, commit }) {
    if (state.user) {
      return get('/api/user/permissions').then((permissions) => {
        commit(AppMutationTypes.SET_PERMISSIONS, permissions)
      })
    } else {
      commit(AppMutationTypes.SET_PERMISSIONS, { event: {}, department: {} })
    }
  }
}
