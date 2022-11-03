Shift Assignments
"""""""""""""""""

.. http:get:: /api/shiftassignments

    Retrieve a list of shiftassignments.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shiftassignments

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "badge": 1,
            "shift": 1,
            "signuptime": "2020-05-22T21:15:52.159726"
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

.. http:get:: /api/shiftassignments/<id>

    Retrieve a single shiftassignment.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shiftassignments/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "shift": 1,
            "signuptime": "2020-05-22T21:15:52.159726"
        }
    
.. http:post:: /api/shiftassignments

    Create a new shiftassignment object.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X POST --header "Content-Type: application/json" --data '{"badge": 1, "shift": 1}' https://tuber.magfest.org/api/shiftassignments

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "shift": 1,
            "signuptime": "2020-05-22T21:15:52.159726"
        }
    
.. http:delete:: /api/shiftassignments/<id>

    Delete a shiftassignment.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" -X DELETE https://tuber.magfest.org/api/shiftassignments/1

    **Example Response**

    .. sourcecode:: json
        
        {
            "id": 1,
            "badge": 1,
            "shift": 1,
            "signuptime": "2020-05-22T21:15:52.159726"
        }
