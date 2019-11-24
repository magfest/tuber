from tuber import db

class HotelRoomRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    declined = db.Column(db.Boolean, nullable=True)
    prefer_department = db.Column(db.Boolean, nullable=True)
    preferred_department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    notes = db.Column(db.String(512), nullable=True)
    prefer_single_gender = db.Column(db.Boolean, nullable=True)
    preferred_gender = db.Column(db.String(64), nullable=True)
    noise_level = db.Column(db.String(64), nullable=True)
    smoke_sensitive = db.Column(db.Boolean, nullable=True)
    sleep_time = db.Column(db.String(64), nullable=True)
    room_night_justification = db.Column(db.String(512), nullable=True)

class HotelRoomBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'))
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(256), nullable=True)
    rooms = db.relationship("HotelRoom")

class HotelRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    notes = db.Column(db.String(512), nullable=True)
    messages = db.Column(db.String(512), nullable=True)
    hotel_block = db.Column(db.Integer, db.ForeignKey('hotel_room_block.id'), nullable=False)
    hotel_location = db.Column(db.Integer, db.ForeignKey('hotel_location.id'), nullable=False)
    completed = db.Column(db.Boolean)

class HotelRoommateRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    requested = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)

class HotelAntiRoommateRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    requested = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)

class HotelLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    address = db.Column(db.String(128), nullable=False)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    rooms = db.relationship("HotelRoom")

class HotelRoomNight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    restricted = db.Column(db.Boolean, nullable=False, default=False)
    restriction_type = db.Column(db.String(64), nullable=True)
    hidden = db.Column(db.Boolean, nullable=False, default=False)
    requests = db.relationship("RoomNightRequest")
    assignments = db.relationship("RoomNightAssignment")
    approvals = db.relationship("RoomNightApproval")

class RoomNightRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    requested = db.Column(db.Boolean)
    room_night = db.Column(db.Integer, db.ForeignKey('hotel_room_night.id'), nullable=False)

class RoomNightAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))
    room_night = db.Column(db.Integer, db.ForeignKey('hotel_room_night.id'), nullable=False)
    hotel_room = db.Column(db.Integer, db.ForeignKey('hotel_room.id'))

class RoomNightApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    room_night = db.Column(db.Integer, db.ForeignKey('hotel_room_night.id'), nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    approved = db.Column(db.Boolean, nullable=False)
