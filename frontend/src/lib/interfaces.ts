interface Badge {
    id: number,
    event: number,
    badge_type: number,
    printed_number?: string,
    printed_name?: string,
    search_name?: string,
    first_name?: string,
    last_name?: string,
    legal_name?: string,
    legal_name_matches?: boolean,
    phone?: string,
    email: string,
    user?: number,
    uber_id?: string,
    departments?: [number],
    room_night_requests?: [number],
    room_night_assignments?: [number],
    room_night_approvals?: [number],
    hotel_room_requests?: [number]
}

interface Event {
    id: number,
    name: string,
    description: string
}

interface User {
    id: number,
    username: string,
    email: string,
    active: boolean,
    badges: [number],
    sessions: [number],
    grants: [number]
}

interface UserSession {
    session: string,
    user?: User,
    badge?: Badge,
}

interface Department {
    id: number,
    uber_id: string,
    description: string,
    event: number,
    name: string,
    badges: [number]
}

export {
    Badge,
    Event,
    User,
    UserSession,
    Department,
}