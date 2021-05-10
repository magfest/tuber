from tuber import db

class BackgroundJob(db.Model):
    __tablename__ = "background_job"
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)
    uuid = db.Column(db.String, nullable=False)
    progress = db.Column(db.JSON)
    result = db.Column(db.JSON)