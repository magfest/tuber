from tuber import db

class BadgeToDepartment(db.Model):
    __tablename__ = "badge_to_department"
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

class Badge(db.Model):
    __tablename__ = "badge"
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    badge_type = db.Column(db.Integer, db.ForeignKey('badge_type.id'))
    printed_number = db.Column(db.String(32))
    printed_name = db.Column(db.String(256))
    search_name = db.Column(db.String(256))
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    legal_name = db.Column(db.String(256), nullable=False)
    legal_name_matches = db.Column(db.Boolean)
    phone = db.Column(db.String(64))
    email = db.Column(db.String(128))
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    departments = db.relationship("Department", secondary="badge_to_department", back_populates="badges")
    room_night_requests = db.relationship("RoomNightRequest")
    room_night_assignments = db.relationship("RoomNightAssignment")
    room_night_approvals = db.relationship("RoomNightApproval")
    hotel_room_request = db.relationship("HotelRoomRequest")

    def __repr__(self):
        return '<Badge %r %r>' % (self.first_name, self.last_name)

class Department(db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    uber_id = db.Column(db.String(128), unique=True, nullable=True)
    description = db.Column(db.String(256), nullable=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(256))
    badges = db.relationship("Badge", secondary="badge_to_department", back_populates="departments")

class BadgeType(db.Model):
    __tablename__ = "badge_type"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return '<BadgeType %r>' % self.name

class RibbonType(db.Model):
    __tablename__ = "ribbon_type"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return '<RibbonType %r>' % self.name

class RibbonToBadge(db.Model):
    __tablename__ = "ribbon_to_badge"
    id = db.Column(db.Integer, primary_key=True)
    ribbon = db.Column(db.Integer, db.ForeignKey('ribbon_type.id'))
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))