from tuber import db

class ChecklistEntryRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklistentry = db.Column(db.Integer, db.ForeignKey('checklist_entry.id'))
    role = db.Column(db.Integer, db.ForeignKey('role.id'))

class ChecklistEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String)
    description = db.Column(db.String)
    groupby = db.Column(db.String)
    roles = db.relationship("Role", secondary="checklist_entry_role")
    editable = db.Column(db.Boolean)
    starttime = db.Column(db.DateTime())
    endtime = db.Column(db.DateTime())
    active = db.Column(db.Boolean)
    action = db.Column(db.JSON)

class ChecklistStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklistentry = db.Column(db.Integer, db.ForeignKey('checklist_entry.id'))
    status = db.Column(db.String)
    role = db.Column(db.Integer, db.ForeignKey('role.id'))
    department = db.Column(db.Integer, db.ForeignKey('department.id'))
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))
    data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime())

class GoogleAPIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'))
    token = db.Column(db.String)
    name = db.Column(db.String)
    description = db.Column(db.String)

class GoogleDriveFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    googleapikey = db.Column(db.Integer, db.ForeignKey('google_api_key.id'))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String)
    name = db.Column(db.String)
    description = db.Column(db.String)
