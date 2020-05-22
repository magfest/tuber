Shifts
^^^^^^

.. http:get:: /api/events/<id>/jobs/available

    Retrieve the list of shifts that are available to either the current user or a specific badge.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/events/<id>/jobs/available

    **Example Response**

    .. sourcecode:: json
        
        [
            {
                "job": {
                    "id": 1,
                    "name": "Do the thing",
                    "description": "",
                    "department": null,
                    "documentation": "",
                    "method": {},
                    "signuprules": {},
                    "sticky": false,
                    "schedules": [],
                    "scheduleevents": [],
                    "roles": [],
                    "shifts": [1]
                },
                "shifts": [
                    {
                        "blocks": [
                            "Shift is full."
                        ],
                        "id": 1,
                        "job": 1,
                        "schedule": null,
                        "schedule_event": null,
                        "starttime": "2020-05-22T21:15:52.159726",
                        "duration": 3600.0,
                        "slots": 4,
                        "filledslots": 0,
                        "weighting": 1.0
                    }
                ]
            }
        ]

    :query string badge: If provided then the result will be the shifts available to the given badge.

.. http:post:: /api/events/<id>/shifts/<id>/signup

    Sign up for the given shift. If you want to sign up a different badge then the post body should be an object with key badge set the the desired badge id.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" --header 'Content-Type: application/json' -X POST --data '{"badge": 4}' https://tuber.magfest.org/api/events/<id>/shifts/<id>/signup

    **Example Response**

    .. sourcecode:: json
        
        {
            "shift": {
                "id": 1,
                "job": 1,
                "schedule": null,
                "schedule_event": null,
                "starttime": "2020-05-22T21:15:52.159726",
                "duration": 3600.0,
                "slots": 4,
                "filledslots": 0,
                "weighting": 1.0
            },
            "shift_signup": {
                "id": 1,
                "badge": 1,
                "job": 1,
                "shift": 1,
                "schedule": null,
                "scheduleevent": null,
                "starttime": "2020-05-22T21:15:52.159726",
                "duration": 3600.0
            },
            "shift_assignment": {
                "id": 1,
                "badge": 1,
                "shift": 1,
                "signuptime": "2020-05-22T21:15:52.159726"
            }
        }

.. http:post:: /api/events/<id>/jobs/<id>/dryrun

    This endpoint lets you check what the resulting shifts based on a hypothetical job definition. Calling this endpoint will not commit anything to the database, but will let you see what would have resulted from a PATCH to the corresponding job.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" --header 'Content-Type: application/json' -X POST --data '{"method": {"name": "copy"}}' https://tuber.magfest.org/api/events/<id>/jobs/<id>/dryrun

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "job": 1,
            "schedule": null,
            "schedule_event": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "slots": 4,
            "filledslots": 0,
            "weighting": 1.0
        }]

.. include:: api/shifts/schedule.rst
.. include:: api/shifts/scheduleevents.rst
.. include:: api/shifts/jobs.rst
.. include:: api/shifts/shifts.rst
.. include:: api/shifts/shiftassignments.rst
.. include:: api/shifts/shiftsignups.rst
  