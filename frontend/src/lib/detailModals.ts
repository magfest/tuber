/* Deep-linkable detail modals.
 *
 * Two global query params work on every page: ?attendee=<badgeId> opens the
 * attendee modal and ?room=<roomId> opens the room modal. Opening pushes a
 * history entry (so Back closes the modal) and closing replaces the query,
 * which makes any modal state shareable as a URL.
 *
 * DetailModalHost (mounted once in App.vue) watches these params and renders
 * the modals; AttendeeName/RoomName call the helpers below from anywhere.
 */
import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'

function openDetail (router: Router, route: RouteLocationNormalizedLoaded, key: string, id: number | string) {
  const query = Object.assign({}, route.query)
  if (String(query[key]) === String(id)) {
    return
  }
  query[key] = String(id)
  router.push({ query })
}

function closeDetail (router: Router, route: RouteLocationNormalizedLoaded, key: string) {
  if (!(key in route.query)) {
    return
  }
  const query = Object.assign({}, route.query)
  delete query[key]
  router.replace({ query })
}

function openAttendee (router: Router, route: RouteLocationNormalizedLoaded, badgeId: number | string) {
  openDetail(router, route, 'attendee', badgeId)
}

function openRoom (router: Router, route: RouteLocationNormalizedLoaded, roomId: number | string) {
  openDetail(router, route, 'room', roomId)
}

export {
  openAttendee,
  openRoom,
  closeDetail
}
