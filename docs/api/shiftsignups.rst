Shift Signups
"""""""""""""

.. http:get:: /api/shiftsignups

    Retrieve a list of shiftsignups.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shiftsignups

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "badge": 1,
            "job": 1,
            "shift": 1,
            "schedule": null,
            "scheduleevent": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/shiftsignups/<id>

    Retrieve a single shiftsignup.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shiftsignups/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "job": 1,
            "shift": 1,
            "schedule": null,
            "scheduleevent": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0
        }
    
.. http:post:: /api/shiftsignups

    Create a new shiftsignup object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"shift": 2}' https://tuber.magfest.org/api/shiftsignups

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "job": 1,
            "shift": 2,
            "schedule": null,
            "scheduleevent": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0
        }
    
.. http:patch:: /api/shiftsignups/<id>

    Update a shiftsignup.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X PATCH --header "Content-Type: application/json" --data '{"shift": 1}' https://tuber.magfest.org/api/shiftsignups/<id>

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "job": 1,
            "shift": 1,
            "schedule": null,
            "scheduleevent": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0
        }

.. http:delete:: /api/shiftsignups/<id>

    Delete a shiftsignup.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/shiftsignups/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "job": 1,
            "shift": 1,
            "schedule": null,
            "scheduleevent": null,
            "starttime": "2020-05-22T21:15:52.159726",
            "duration": 3600.0
        }
