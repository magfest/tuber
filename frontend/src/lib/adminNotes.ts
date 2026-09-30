import { patch } from './rest'

// Admin-only notes live behind their own endpoints: they are hidden from the
// generic API and left out of every export, so this is the only way to change
// them. Both resolve with {id, admin_notes} as saved.
export function saveRequestAdminNote (eventId: number, requestId: number, text: string): Promise<any> {
  return patch('/api/event/' + eventId + '/hotel/request/' + requestId + '/admin_notes',
    { admin_notes: text })
}

export function saveRoomAdminNote (eventId: number, roomId: number, text: string): Promise<any> {
  return patch('/api/event/' + eventId + '/hotel/room/' + roomId + '/admin_notes',
    { admin_notes: text })
}
