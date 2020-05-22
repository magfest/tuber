Jobs
""""

.. http:get:: /api/events/1/jobs

    Retrieve a list of jobs.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/events/1/jobs

    **Example Response**

    .. sourcecode:: json
        
        [{
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
            "shifts": []
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/events/1/jobs/<id>

    Retrieve a single job.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/events/1/jobs/1

    **Example Response**

    .. sourcecode:: json
        
        {
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
            "shifts": []
        }
    
.. http:post:: /api/events/1/jobs

    Create a new job object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"name": "Do the thing"}' https://tuber.magfest.org/api/events/1/jobs

    **Example Response**

    .. sourcecode:: json
        
        {
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
            "shifts": []
        }
    
.. http:patch:: /api/events/1/jobs/<id>

    Update a job.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X PATCH --header "Content-Type: application/json" --data '{"description": "Really Cool"}' https://tuber.magfest.org/api/events/1/jobs/<id>

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "name": "Do the thing",
            "description": "Really Cool",
            "department": null,
            "documentation": "",
            "method": {},
            "signuprules": {},
            "sticky": false,
            "schedules": [],
            "scheduleevents": [],
            "roles": [],
            "shifts": []
        }

.. http:delete:: /api/events/1/jobs/<id>

    Delete a job.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/events/1/jobs/1

    **Example Response**

    .. sourcecode:: json
        
        {
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
            "shifts": []
        }
