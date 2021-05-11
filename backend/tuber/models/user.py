from tuber import db

class User(db.Model):
    __tablename__ = "user"
    def __perms__(self, g):
        if g.user.id == self.id:
            return {"self"}
        return set()
    __url__ = "/api/user"
    id = db.Column(db.Integer, primary_key=True)
    id.allow_r = {"self"}
    username = db.Column(db.String(80), unique=True, nullable=False)
    username.allow_rw = {"self"}
    email = db.Column(db.String(120), unique=True, nullable=False)
    email.allow_rw = {"self"}
    password = db.Column(db.String(128), default="")
    password.hidden = True
    active = db.Column(db.Boolean)
    active.allow_r = {"self"}
    badges = db.relationship("Badge")
    badges.allow_r = {"self"}
    sessions = db.relationship("Session")
    sessions.allow_r = {"self"}
    grants = db.relationship("Grant")
    grants.allow_r = {"self"}

class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    secret = db.Column(db.String(64))
    secret.hidden = True
    last_active = db.Column(db.DateTime)

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