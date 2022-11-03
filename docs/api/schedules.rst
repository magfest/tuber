Schedules
"""""""""

.. http:get:: /api/events/<id>/schedules

    Retrieve a list of schedules.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/events/1/schedules

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "name": "Panel 1 Schedule",
            "description": "The schedule for our largest panel room",
            "tags": {}
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/events/<id>/schedules/<id>

    Retrieve a single schedule.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/events/1/schedules/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Panel 1 Schedule",
            "description": "The schedule for our largest panel room",
            "tags": {}
        }
    
.. http:post:: /api/events/<id>/schedules

    Create a new schedule object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"name": "New Schedule"}' https://tuber.magfest.org/api/events/1/schedules

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "New Schedule",
            "description": "",
            "tags": null
        }
    
.. http:patch:: /api/events/<id>/schedules/<id>

    Update a schedule.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X PATCH --header "Content-Type: application/json" --data '{"description": "Really Cool"}' https://tuber.magfest.org/api/events/1/schedules/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "New Schedule",
            "description": "Really Cool",
            "tags": null
        }

.. http:delete:: /api/events/<id>/schedules/<id>

    Delete a schedule.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/events/1/schedules/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "New Schedule",
            "description": "Really Cool",
            "tags": null
        }
