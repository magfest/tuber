Shifts
""""""

.. http:get:: /api/shifts

    Retrieve a list of shifts.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shifts

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

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/shifts/<id>

    Retrieve a single shift.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shifts/1

    **Example Response**

    .. sourcecode:: json
        
        {
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
    
.. http:post:: /api/shifts

    Create a new shift object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"job": 1, "schedule": 2, "slots": 4}' https://tuber.magfest.org/api/shifts

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "job": 1,
            "schedule": 2,
            "schedule_event": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "slots": 4,
            "filledslots": 0,
            "weighting": 1.0
        }
    
.. http:patch:: /api/shifts/<id>

    Update a shift.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X PATCH --header "Content-Type: application/json" --data '{"duration": 7200.0}' https://tuber.magfest.org/api/shifts/<id>

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "job": 1,
            "schedule": 2,
            "schedule_event": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 7200.0,
            "slots": 4,
            "filledslots": 0,
            "weighting": 1.0
        }

.. http:delete:: /api/shifts/<id>

    Delete a shift.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/shifts/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "job": 1,
            "schedule": 2,
            "schedule_event": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 7200.0,
            "slots": 4,
            "filledslots": 0,
            "weighting": 1.0
        }
