from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema
from flask import g, request, jsonify
from sqlalchemy import or_
import datetime

class ChecklistEntrySchema(ModelSchema):
    class Meta:
        model = ChecklistEntry
        sqla_session = db.session
        fields = ['id', 'event', 'name', 'description', 'groupby', 'roles', 'editable', 'starttime', 'endtime', 'active', 'action']

register_crud("checklistentries", ChecklistEntrySchema())

class ChecklistStatusSchema(ModelSchema):
    class Meta:
        model = ChecklistStatus
        sqla_session = db.session
        fields = ['id', 'checklistentry', 'status', 'role', 'department', 'badge', 'data', 'timestamp']

register_crud("checkliststatuses", ChecklistStatusSchema())

class GoogleAPIKeySchema(ModelSchema):
    class Meta:
        model = GoogleAPIKey
        sqla_session = db.session
        fields = ['id', 'event', 'token', 'name', 'description']

register_crud("googleapikeys", GoogleAPIKeySchema())

class GoogleDriveFolderSchema(ModelSchema):
    class Meta:
        model = GoogleDriveFolder
        sqla_session = db.session
        fields = ['id', 'googleapikey', 'user', 'token', 'name', 'description']

register_crud("googledrivefolders", GoogleDriveFolderSchema())

@app.route("/api/events/<int:event>/checklistentries/<int:checklistentry>/createform", methods=["POST"])
def create_google_form(event, checklistentry):
    return "Not yet implemented", 501

@app.route("/api/events/<int:event>/checkliststatuses/<int:checkliststatus>/complete", methods=["POST"])
def complete_checklist(event, checkliststatus):
    return "Not yet implemented", 501

@app.route("/api/events/<int:event>/departments/<int:department>/checklist", methods=["GET"])
def get_department_checklist(event, department):
    return "Not yet implemented", 501

@app.route("/api/events/<int:event>/badges/<int:badge>/checklist", methods=["GET"])
def get_badge_checklist(event, badge):
    return "Not yet implemented", 501

@app.route("/api/events/<int:event>/googledrivefolders/<int:googledrivefolder>/authorize", methods=["POST"])
def authorize_googledrive_folder(event, googledrivefolder):
    return "Not yet implemented", 501