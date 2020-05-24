Schedule Events
"""""""""""""""

.. http:get:: /api/scheduleevents

    Retrieve a list of scheduleevents.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/scheduleevents

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "name": "Someone's panel",
            "description": "",
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "schedule": 1
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/scheduleevents/<id>

    Retrieve a single scheduleevent.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/scheduleevents/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Someone's panel",
            "description": "",
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "schedule": 1
        }
    
.. http:post:: /api/scheduleevents

    Create a new scheduleevent object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"name": "Someone's panel"}' https://tuber.magfest.org/api/scheduleevents

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Someone's panel",
            "description": "",
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "schedule": 1
        }
    
.. http:patch:: /api/scheduleevents/<id>

    Update a scheduleevent.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X PATCH --header "Content-Type: application/json" --data '{"description": "Really Cool"}' https://tuber.magfest.org/api/scheduleevents/<id>

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Someone's panel",
            "description": "Really Cool",
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "schedule": 1
        }

.. http:delete:: /api/scheduleevents/<id>

    Delete a scheduleevent.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/scheduleevents/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Someone's panel",
            "description": "",
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0,
            "schedule": 1
        }
