from tuber import db

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    printed_number = db.Column(db.String(32), unique=False, nullable=True)
    printed_name = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    legal_name = db.Column(db.String(256), nullable=False)
    legal_name_matches = db.Column(db.Booleon)
    email = db.Column(db.String(128), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return '<Badge %r %r>' % (self.first_name, self.last_name)

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
    pass

class Group(db.Model):
    pass
