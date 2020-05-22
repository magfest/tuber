Shifts
^^^^^^

.. http:get:: /api/shifts

    Retrieve a list of shifts.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/shifts

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.
