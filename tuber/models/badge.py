from tuber import db

class BadgeToDepartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    printed_number = db.Column(db.String(32), unique=False, nullable=True)
    printed_name = db.Column(db.String(256), nullable=False)
    search_name = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    legal_name = db.Column(db.String(256), nullable=False)
    legal_name_matches = db.Column(db.Boolean)
    email = db.Column(db.String(128), unique=False, nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    departments = db.relationship("Department", secondary="badge_to_department", back_populates="badges")
    room_night_requests = db.relationship("RoomNightRequest")
    room_night_assignments = db.relationship("RoomNightAssignment")
    room_request = db.relationship("HotelRoomRequest")

    def __repr__(self):
        return '<Badge %r %r>' % (self.first_name, self.last_name)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    description = db.Column(db.String(256), nullable=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(256))
    badges = db.relationship("Badge", secondary="badge_to_department", back_populates="departments")
