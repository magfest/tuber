from tuber.models import *
from tuber.permissions import *
from flask import request
from sqlalchemy.orm import selectinload
from sqlalchemy import func

READ_PERMS = {"read", "write", "*", "searchname"}
WRITE_PERMS = {"write", "*"}


def paginate(query, model, event=None, department=None):
    count = request.args.get(
        "count", False, type=lambda x: x.lower() == 'true')
    sort = request.args.get("sort", "")
    order = request.args.get("order", "asc")
    limit = request.args.get("limit", 0, type=int)
    offset = request.args.get("offset", 0, type=int)
    page = request.args.get("page", 0, type=int)
    search = request.args.get("search", "", type=str)
    search_field = request.args.get("search_field", "", type=str)
    search_mode = request.args.get("search_mode", "contains", type=str)
    search_case_sensitive = request.args.get(
        "search_case_sensitive", False, type=lambda x: x.lower() == 'true')
    full = request.args.get(
        "full", False, type=lambda x: x.lower() == 'true')
    deep = request.args.get(
        "deep", False, type=lambda x: x.lower() == 'true')
    if page:
        offset = page*10
        if limit:
            offset = page*limit

    filters = []
    perms = model_permissions(model.__tablename__.lower())
    if not READ_PERMS.intersection(perms['*']):
        ids = [int(x) for x in perms.keys()
               if READ_PERMS.intersection(perms[x])]
        if not ids:
            raise PermissionDenied(
                f"User is not able to read any values in {model.__tablename__}")
        filters.append(model.id.in_(ids))
    if event:
        filters.append(model.event == event)
    if department:
        filters.append(model.department == department)
    if search_field:
        if hasattr(model, search_field):
            columns, relationships = model.get_fields()
            relationships = {x.key: x for x in relationships}
            if search_field in relationships:
                search_model = getattr(model, search_field)
                model.get_modelclasses()
                rel_model = model.modelclasses[relationships[search_field].target.name]
                search = [int(x) for x in search.split(",")]
                filters.append(search_model.any(rel_model.id.in_(search)))
            elif search_field in columns:
                col = columns[search_field]
                search_model = getattr(model, search_field)
                if isinstance(col.type, Boolean):
                    search = search.lower() in ["true", "yes", "1"]
                    assert search_mode in ["equals", "notEquals"]
                elif isinstance(col.type, String):
                    if not search_case_sensitive:
                        search_model = func.lower(
                            getattr(model, search_field))
                        search = search.lower()
                elif isinstance(col.type, Integer):
                    search = int(search)
                    assert search_mode in ["equals", "notEquals"]
                else:
                    raise AttributeError(
                        f"Searching {type(col.type)} is unsupported.")
                if search_mode == "contains":
                    filters.append(search_model.contains(
                        search, autoescape=True))
                elif search_mode == "startswith":
                    filters.append(search_model.startswith(
                        search, autoescape=True))
                elif search_mode == "endswith":
                    filters.append(search_model.endswith(
                        search, autoescape=True))
                elif search_mode == "equals":
                    filters.append(search_model == search)
                elif search_mode == "notEquals":
                    filters.append(search_model != search)
            else:
                raise AttributeError(
                    f"Could not locate search_field {search_field} in model {model.__name__}")
    for key, val in request.args.items():
        if hasattr(model, key):
            filters.append(getattr(model, key) == val)
    rows = query.filter(*filters)
    if full:
        columns, relationships = model.get_fields()
        for relation in relationships:
            rows = rows.options(selectinload(
                getattr(model, relation.key)))
    if hasattr(model, sort):
        print(f"Sorting on {sort}")
        if order == "asc":
            rows = rows.order_by(getattr(model, sort))
        else:
            rows = rows.order_by(getattr(model, sort).desc())
    if count:
        return rows
    if limit:
        rows = rows.offset(offset).limit(limit)
    elif offset:
        rows = rows.offset(offset).limit(10)
    return rows
