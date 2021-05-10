from tuber import db

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), default="")
    active = db.Column(db.Boolean)
    badges = db.relationship("Badge")
    sessions = db.relationship("Session")
    grants = db.relationship("Grant")

    def __repr__(self):
        return '<User %r>' % self.username

class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    secret = db.Column(db.String(64))
    last_active = db.Column(db.DateTime)

    def __repr__(self):
        return '<Session %r>' % self.id

class Permission(db.Model):
    __tablename__ = "permission"
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(64), unique=True)
    role = db.Column(db.Integer, db.ForeignKey('role.id'))

class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(128))
    event = db.Column(db.Integer, nullable=True)

class Grant(db.Model):
    __tablename__ = "grant"
    # Null values become wildcards, i.e. if event is NULL, then the grant applies to all events
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    role = db.Column(db.Integer, nullable=True)
    department = db.Column(db.Integer, nullable=True)