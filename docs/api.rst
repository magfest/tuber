Tuber API
=========

Endpoints
---------

Hotels
^^^^^^

.. http:get:: /api/hotels

    Retrieve a list of hotels.

    **Example Request**

    .. tabs::

        .. code-tab:: bash

            $ curl -H "X-Auth-Token: <Token>" https://tuber.magfest.org/api/hotels

    **Example Response**

    .. sourcecode:: json
        
        [{
            "id": 1,
            "name": "The Gaylord",
            "description": "An awesome venue in Maryland!"
        }]

    :query string full: If true returns a list of objects. If false, returns a list of id numbers.

Resources
---------

Hotels
^^^^^^

.. automodule:: tuber.api.hotels
    :members:

Emails
^^^^^^

.. automodule:: tuber.api.emails
    :members:
