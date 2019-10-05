from tuber import db

class HotelRoomBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'))
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(256), nullable=True)

class HotelRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(256), nullable=True)
    disable_autofill = db.Column(db.Boolean, nullable=False, default=True)
    hotel_block = db.Column(db.Integer, db.ForeignKey('hotel_room_block.id'), nullable=False)
    hotel_location = db.Column(db.Integer, db.ForeignKey('hotel_location.id'), nullable=False)

#    def __repr__(self):
#        return '<BadgeType %r>' % self.name

# This will use the Permissions API
#class HotelBlockManager(db.Model):

class HotelRoommateRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    requested = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)

class HotelAntiRoommateRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disallower = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    disallowed = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)

class HotelLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    address = db.Column(db.String(128), nullable=False)

class HotelRoomNight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    restricted = db.Column(db.Boolean, nullable=False, default=False)

class BadgeToRoomNight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    room_block = db.Column(db.Integer, db.ForeignKey('hotel_room_block.id'), nullable=False)
    room_night = db.Column(db.Integer, db.ForeignKey('hotel_room_night.id'), nullable=False)
    justification = db.Column(db.String(512), nullable=True)
    justification_approved = db.Column(db.Boolean, nullable=True, default=False)
