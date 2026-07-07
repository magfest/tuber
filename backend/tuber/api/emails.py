from tuber import app, aws
from flask import request, Response, stream_with_context
from tuber.models import *
from tuber.database import db
from tuber.permissions import *
from sqlalchemy.orm import joinedload
import datetime
import re
import jinja2
import jinja2.meta
import lupa
from tuber.api import *
from tuber.models import *

# Every top-level name an email filter or template can reference.
CONTEXT_KEYS = {
    "badge", "event", "roommate_requests", "roommate_anti_requests",
    "requested_nights", "assigned_nights", "approved_nights",
    "approving_depts", "hotel_rooms", "hotel_room_nights", "has_edge_night",
    "hotel_request",
}


def referenced_symbols(code, templates):
    """Context keys referenced by the Lua filter and Jinja templates.

    Jinja sources are parsed to an AST (jinja2.meta); Lua is scanned lexically
    for `context.name` / `context["name"]`. Dynamic Lua access we can't see
    through falls back to the full key set."""
    symbols = set()
    for source in templates:
        try:
            ast = jinja2.Environment().parse(source or '')
            symbols |= jinja2.meta.find_undeclared_variables(ast)
        except Exception:
            pass  # unparseable template renders as an error anyway
    code = code or ''
    if code.strip():
        # The context arrives as the filter function's parameter, under
        # whatever name the author chose: function(context), function(c), ...
        params = set(re.findall(r'function\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)', code))
        if not params:
            return set(CONTEXT_KEYS)
        for param in params:
            escaped = re.escape(param)
            symbols |= set(re.findall(
                r'\b' + escaped + r'\s*(?:\.\s*|\[\s*["\'])([A-Za-z_][A-Za-z0-9_]*)',
                code))
            # Dynamic indexing, iteration, or aliasing defeats the lexical
            # scan — load everything rather than guess.
            if re.search(r'\b' + escaped + r'\s*\[\s*[^"\'\s]', code) or \
                    re.search(r'python\.iter\s*\(\s*' + escaped + r'\s*\)', code) or \
                    re.search(r'=\s*' + escaped + r'\b', code):
                return set(CONTEXT_KEYS)
    return symbols & CONTEXT_KEYS


def get_email_context(badge, tables, needed=None):
    """Build the filter/template context for one badge. With `needed` (a set
       of CONTEXT_KEYS), only those parts are computed — a large win when a
       preview's filter only touches cheap fields."""
    if needed is None:
        needed = CONTEXT_KEYS
    event = tables['Event']
    request = tables['HotelRoomRequest'].get(badge.id, HotelRoomRequest(declined=True))
    context = {
        "badge": badge,
        "event": event,
        "hotel_request": request,
    }
    if "hotel_room_nights" in needed:
        context["hotel_room_nights"] = tables['HotelRoomNight']
    if "roommate_requests" in needed:
        context["roommate_requests"] = [x.public_name for x in request.roommate_requests]
    if "roommate_anti_requests" in needed:
        context["roommate_anti_requests"] = [x.public_name for x in request.roommate_anti_requests]
    if "requested_nights" in needed:
        requested_nights = [x.room_night for x in request.room_night_requests if x.requested]
        requested_nights.sort()
        context["requested_nights"] = requested_nights
    if "assigned_nights" in needed:
        assigned_nights = [x.room_night for x in request.room_night_assignments]
        assigned_nights.sort()
        context["assigned_nights"] = assigned_nights
    if "has_edge_night" in needed:
        context["has_edge_night"] = any([tables['HotelRoomNight'][x.room_night].restricted
                                         for x in request.room_night_requests if x.requested])

    if "hotel_rooms" in needed:
        hotel_room_ids = list(set([x.hotel_room for x in request.room_night_assignments]))
        hotel_rooms = []
        for room_id in hotel_room_ids:
            room = tables['HotelRoom'][room_id]
            assignments = list(room.room_night_assignments)
            assignments.sort(key=lambda x: tables['HotelRoomNight'][x.room_night].date)
            start_night = assignments[0].room_night
            end_night = assignments[-1].room_night
            checkout_day = HotelRoomNight(
                name=(tables['HotelRoomNight'][end_night].date + datetime.timedelta(days=1)).strftime("%A"),
                date=tables['HotelRoomNight'][end_night].date + datetime.timedelta(days=1)
            )
            roommates = {x.id: {"badge": tables['Badge'][x.id], "nights": []} for x in room.roommates}
            for i in assignments:
                roommates[i.badge]['nights'].append(i.room_night)
            for roommate in roommates:
                roommates[roommate]['nights'].sort()
            hotel_rooms.append({
                "roommates": roommates,
                "hotel_block": room.hotel_block,
                "hotel_block_name": tables['HotelRoomBlock'].get(room.hotel_block).name if room.hotel_block in tables['HotelRoomBlock'] else "unknown",
                "messages": room.messages,
                "completed": room.completed,
                "start_night": start_night,
                "end_night": end_night,
                "checkout_day": checkout_day,
            })
        context["hotel_rooms"] = hotel_rooms

    if {"approved_nights", "approving_depts"} & needed:
        approvals = [x.room_night for x in request.room_night_approvals if x.approved]
        # Event-level manual approvals have no department (and a department that
        # was deleted leaves a dangling NULL) — only name the ones that exist.
        approving_dept_ids = [x.department for x in request.room_night_approvals
                              if x.approved and x.department is not None]
        approving_depts = [tables['Department'][x].name for x in set(approving_dept_ids)
                           if x in tables['Department']]
        approved_nights = [x.room_night for x in request.room_night_requests if x.requested and ((not tables['HotelRoomNight'][x.room_night].restricted) or (x.room_night in approvals))]
        approved_nights.sort()
        context["approved_nights"] = approved_nights
        context["approving_depts"] = ", ".join(approving_depts)
    return context


def summarize_value(value, depth=0):
    """JSON-safe compact summary of a context value for display in the UI."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 120 else value[:117] + '...'
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, Badge):
        return value.public_name
    if isinstance(value, HotelRoomNight):
        return value.name
    if isinstance(value, HotelRoomRequest):
        return {"declined": value.declined, "hotel_block": value.hotel_block,
                "notes": summarize_value(value.notes, depth + 1)}
    if isinstance(value, Event):
        return value.name
    if depth >= 3:
        return str(value)[:80]
    if isinstance(value, dict):
        items = list(value.items())[:12]
        summary = {str(k): summarize_value(v, depth + 1) for k, v in items}
        if len(value) > 12:
            summary["..."] = f"+{len(value) - 12} more"
        return summary
    if isinstance(value, (list, tuple, set)):
        items = [summarize_value(x, depth + 1) for x in list(value)[:12]]
        if len(value) > 12:
            items.append(f"+{len(value) - 12} more")
        return items
    return str(value)[:120]

def build_email_tables(event_id, badge_ids=None):
    """The per-event lookup tables the email context is built from.

    With badge_ids, the expensive tables are scoped to those badges plus the
    occupants of their rooms (needed for roommate names) — a cheap path for
    rendering a preview for a single attendee."""
    event = db.query(Event).filter(Event.id == event_id).one()
    badge_query = db.query(Badge).filter(Badge.event == event_id)
    request_query = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event_id) \
        .options(joinedload(HotelRoomRequest.room_night_assignments)) \
        .options(joinedload(HotelRoomRequest.room_night_approvals)) \
        .options(joinedload(HotelRoomRequest.room_night_requests)) \
        .options(joinedload(HotelRoomRequest.roommate_requests)) \
        .options(joinedload(HotelRoomRequest.roommate_anti_requests))
    room_query = db.query(HotelRoom).filter(HotelRoom.event == event_id) \
        .options(joinedload(HotelRoom.room_night_assignments)) \
        .options(joinedload(HotelRoom.roommates))
    if badge_ids is not None:
        room_ids = {x.hotel_room for x in db.query(RoomNightAssignment).filter(
            RoomNightAssignment.badge.in_(badge_ids),
            RoomNightAssignment.hotel_room != None).all()}
        occupant_ids = set(badge_ids)
        if room_ids:
            occupant_ids.update(x.badge for x in db.query(RoomNightAssignment).filter(
                RoomNightAssignment.hotel_room.in_(room_ids)).all() if x.badge)
        badge_query = badge_query.filter(Badge.id.in_(occupant_ids))
        request_query = request_query.filter(HotelRoomRequest.badge.in_(occupant_ids))
        room_query = room_query.filter(HotelRoom.id.in_(room_ids))
    badges = badge_query.all()
    tables = {
        "Badge": {x.id: x for x in badges},
        "HotelRoomNight": {x.id: x for x in db.query(HotelRoomNight).filter(HotelRoomNight.event == event_id).all()},
        "HotelRoomRequest": {x.badge: x for x in request_query.all()},
        "Department": {x.id: x for x in db.query(Department).filter(Department.event == event_id).all()},
        "HotelRoom": {x.id: x for x in room_query.all()},
        "HotelRoomBlock": {x.id: x for x in db.query(HotelRoomBlock).filter(HotelRoomBlock.event == event_id).all()},
        "Event": event,
    }
    return badges, tables


def generate_emails(email):
    source = db.query(EmailSource).filter(EmailSource.id == email.source).one()

    L = lupa.LuaRuntime(register_eval=False)
    filter = L.execute(email.code)
    subject_template = jinja2.Template(email.subject)
    body_template = jinja2.Template(email.body)

    badges, tables = build_email_tables(email.event)

    for badge in badges:
        context = get_email_context(badge, tables)
        if filter(context):
            subject = subject_template.render(**context)
            body = body_template.render(**context)
            yield [badge.id, badge.email, source.address, subject, body]

@app.route('/api/event/<int:event>/email/preview', methods=['POST'])
def email_preview(event):
    """Evaluate a draft email against the event's attendees: who the Lua
       filter matches, and the rendered subject/body for one of them."""
    if not check_permission('email.*.write', event=event):
        return "Permission Denied", 403
    code = request.json.get('code') or ''
    subject = request.json.get('subject') or ''
    body = request.json.get('body') or ''
    preview_badge_id = request.json.get('badge')
    show = request.json.get('show', 'matched')

    def render_for(badge, tables):
        """Rendered subject/body plus a full variables card for one badge."""
        preview = {"badge": badge.id, "name": badge.public_name,
                   "email": badge.email}
        render_error = None
        context = get_email_context(badge, tables)
        variables = {key: summarize_value(value)
                     for key, value in sorted(context.items())}
        try:
            preview["subject"] = jinja2.Template(subject).render(**context)
            preview["body"] = jinja2.Template(body).render(**context)
        except Exception as e:
            render_error = str(e)
        return preview, variables, render_error

    # Template-only edits don't change who matches, so the frontend asks for a
    # render against one attendee — scoped queries instead of a full pass over
    # every attendee's context and the Lua filter.
    if not request.json.get('evaluate_filter', True) and preview_badge_id:
        badges, tables = build_email_tables(event, badge_ids=[preview_badge_id])
        badge = tables["Badge"].get(preview_badge_id)
        if not badge:
            return "Could not locate badge", 404
        result = {"render_only": True}
        result["preview"], result["variables"], result["render_error"] = \
            render_for(badge, tables)
        return jsonify(result)

    badges, tables = build_email_tables(event)
    symbols = referenced_symbols(code, [subject, body])
    filter_symbols = sorted(referenced_symbols(code, []) - {"badge", "event"})
    result = {
        "total": len(badges),
        "matched_count": 0,
        "attendees": [],
        "showing": show if show in ("matched", "unmatched") else "matched",
        "symbols": filter_symbols,
        "filter_errors": [],
        "preview": None,
        "variables": None,
        "render_error": None,
    }

    filter = None
    if code.strip():
        try:
            L = lupa.LuaRuntime(register_eval=False)
            filter = L.execute(code)
            if not callable(filter):
                raise ValueError("The filter code must return a function.")
        except Exception as e:
            result["filter_errors"].append(str(e))
            return jsonify(result)

    contexts = {}
    matched_badges = []
    unmatched_badges = []
    for badge in badges:
        try:
            # Only compute the parts of the context the filter and templates
            # actually reference — the full context is much more expensive.
            context = get_email_context(badge, tables, needed=symbols)
            contexts[badge.id] = context
            matched = bool(filter(context)) if filter else False
        except Exception as e:
            if len(result["filter_errors"]) < 5:
                result["filter_errors"].append(
                    f"{badge.public_name}: {e}")
            continue
        if matched:
            matched_badges.append(badge)
        else:
            unmatched_badges.append(badge)
    result["matched_count"] = len(matched_badges)

    shown = matched_badges if result["showing"] == "matched" else unmatched_badges
    for badge in shown[:1000]:
        context = contexts[badge.id]
        result["attendees"].append({
            "id": badge.id,
            "name": badge.public_name,
            "email": badge.email,
            "pertinent": {sym: summarize_value(context.get(sym))
                          for sym in filter_symbols},
        })
    result["truncated"] = max(0, len(shown) - 1000)

    preview_badge = None
    if preview_badge_id:
        preview_badge = next(
            (x for x in badges if x.id == preview_badge_id), None)
    if not preview_badge and matched_badges:
        preview_badge = matched_badges[0]
    if preview_badge:
        result["preview"], result["variables"], result["render_error"] = \
            render_for(preview_badge, tables)
    return jsonify(result)


@app.route('/api/event/<int:event>/email/import', methods=['POST'])
def email_import(event):
    """Copy email templates and/or sources from another event. Copies are
       created inactive so nothing sends until reviewed; items whose name
       already exists here are skipped."""
    if not check_permission('email.*.write', event=event):
        return "Permission Denied", 403
    from_event = int(request.json.get('from_event', 0))
    if not from_event or from_event == event:
        return "Pick a different event to import from.", 400
    if not check_permission('email.*.read', event=from_event):
        return "Permission Denied for source event", 403
    if not db.query(Event).filter(Event.id == from_event).one_or_none():
        return "Could not locate source event", 404
    include_emails = bool(request.json.get('emails', True))
    include_sources = bool(request.json.get('sources', True))

    counts = {"emails": 0, "sources": 0, "skipped": []}
    # Map source ids in the origin event to ids here (existing name matches
    # or fresh copies) so imported emails keep pointing at the right source.
    source_map = {}
    target_sources = {x.name: x.id for x in db.query(EmailSource).filter(
        EmailSource.event == event).all()}
    for source in db.query(EmailSource).filter(
            EmailSource.event == from_event).all():
        if source.name in target_sources:
            source_map[source.id] = target_sources[source.name]
            if include_sources:
                counts["skipped"].append(f"source: {source.name}")
            continue
        if not include_sources:
            continue
        copy = EmailSource(
            event=event, name=source.name, description=source.description,
            address=source.address, region=source.region,
            ses_access_key=source.ses_access_key,
            ses_secret_key=source.ses_secret_key, active=False)
        db.add(copy)
        db.flush()
        source_map[source.id] = copy.id
        counts["sources"] += 1

    if include_emails:
        target_emails = {x.name for x in db.query(Email).filter(
            Email.event == event).all()}
        for email in db.query(Email).filter(Email.event == from_event).all():
            if email.name in target_emails:
                counts["skipped"].append(f"email: {email.name}")
                continue
            db.add(Email(
                event=event, name=email.name, description=email.description,
                code=email.code, subject=email.subject, body=email.body,
                active=False, send_once=email.send_once,
                source=source_map.get(email.source)))
            counts["emails"] += 1
    db.commit()
    return jsonify(counts)


@app.route('/api/event/<int:event>/email/<int:email>/csv')
def email_csv(event, email):
    if not check_permission('email.*.read', event=event):
        return "Permission Denied", 403
    email = db.query(Email).filter(Event.id == event, Email.id == email).one_or_none()
    if not email:
        return "Could not find requested email {}".format(email), 404

    def stream_emails():
        yield "Badge ID,To,From,Subject,Body\n"
        for i in generate_emails(email):
            yield '"{}","{}","{}","{}","{}"\n'.format(*i)

    headers = {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=emails.csv",
    }
    return Response(stream_with_context(stream_emails()), headers=headers)
email_csv.generator = True

@app.route('/api/event/<int:event>/email/<int:email>/trigger', methods=['POST'])
def api_email_trigger(event, email):
    if not check_permission('email.*.send', event=event):
        return "Permission Denied", 403
    email = db.query(Email).filter(Email.id == email).one_or_none()
    if not email:
        return "Could not find requested email {}".format(request.json['email']), 404
    if not email.active:
        return "Email must be activated before triggering.", 400
    source = db.query(EmailSource).filter(EmailSource.id == email.source).one_or_none()
    if not source:
        return "Could not find EmailSource to send email from", 400
    if not source.active:
        return "The email source for this email is inactive.", 400

    def stream_emails():
        yield '{'
        for badge_id, badge_email, source_address, subject, body in generate_emails(email):
            if email.send_once:
                receipts = db.query(EmailReceipt).filter(EmailReceipt.event == event, EmailReceipt.email == email.id, EmailReceipt.badge == badge_id).all()
                if receipts:
                    continue
            try:
                aws.send_email(badge_email, body, subject, source_address, source.region, source.ses_access_key, source.ses_secret_key)
            except RuntimeError as e:
                print(e.response['Error']['Message'])
            else:
                receipt = EmailReceipt(event=event, email=email.id, badge=badge_id, source=source.id, to_address=badge_email, from_address=source.address, subject=subject, body=body, timestamp=datetime.datetime.now())
                db.add(receipt)
                db.commit()
            yield '"{}": true,'.format(badge_id)
        yield '}'
    headers = {
        "Content-Type": "application/json",
        "Content-Disposition": "attachment; filename=emails.json",
    }
    return Response(stream_with_context(stream_emails()), headers=headers)
api_email_trigger.generator = True