from tuber import db

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    printed_number = db.Column(db.String(32), unique=False, nullable=True)
    printed_name = db.Column(db.String(256), nullable=False)
    search_name = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    legal_name = db.Column(db.String(256), nullable=False)
    legal_name_matches = db.Column(db.Boolean)
    email = db.Column(db.String(128), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    room_night_requests = db.relationship("RoomNightRequest")
    room_night_assignments = db.relationship("RoomNightAssignment")
    room_request = db.relationship("HotelRoomRequest")

    def __repr__(self):
        return '<Badge %r %r>' % (self.first_name, self.last_name)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    description = db.Column(db.String(256), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(256))

class BadgeToDepartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

class BadgeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return '<BadgeType %r>' % self.name

class RibbonType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return '<RibbonType %r>' % self.name

class RibbonToBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)

