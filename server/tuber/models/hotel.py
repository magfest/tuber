class HotelRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('badge.id'))
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return '<BadgeType %r>' % self.name

class HotelRoomNight(db.Model):
    pass

class BadgeToRoomNight(db.Model):
    id = db.Column(db.Integer, primary_key=True)