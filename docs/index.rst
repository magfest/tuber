Tuber
=====

Tuber is an event management system. It helps keep track of your event staff, their jobs and shifts, departments, and attendees.

.. http:get:: /api/hotels

    Retrieve a list of hotels.
    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/hotels

    **Example Response**

    .. sourcecode:: json
        
        [{
            id: 1,
            name: "The Gaylord",
            description: "An awesome venue in Maryland!"
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.