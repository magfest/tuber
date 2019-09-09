from tuber import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), default="wat")
    active = db.Column(db.Boolean)

    def __repr__(self):
        return '<User %r>' % self.username

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_active = db.Column(db.DateTime)

    def __repr__(self):
        return '<Session %r>' % self.id