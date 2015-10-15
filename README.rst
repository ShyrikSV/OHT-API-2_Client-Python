OneHourTranslation API Library for Python
=========================================

.. image:: https://secure.travis-ci.org/ShyrikSV/OHT-API-2_Client-Python.png
   :target: http://travis-ci.org/ShyrikSV/OHT-API-2_Client-Python

One Hour Translation™ provides translation, proofreading and transcription services worldwide. The following API library allows customers to submit and monitor jobs automatically and remotely. 

`More at website <https://www.onehourtranslation.com/translation/about-us>`_   

Dependencies
------------

requests `here <https://github.com/kennethreitz/requests>`_ >= 2.7.0 

Structure
---------

File structure::

  OhtApi2.py/ - contain OHT API implementation class
  test/
    test_oht.py/ - unit tests for OhtApi class
   
For testing used `Travic-CI <https://travis-ci.org/>`_

Some words about testing:
	* Tests save some state information (we know it's not quite right, but creating new projects on OHT server for each test is not quite right as well)
	* There is no mock, because we need to check real answer from server - this class is a part of system, and when server API will be change (if ever) tests will show it.
	* Private and public keys pass as environment variables ('PubKey' and 'PrivKey') - if you fork pass your own keys please.
	
Starters' Guide
---------------

First of all, you must to obtain private and public keys:

1. Register as a customer on `One Hour Translation <https://www.onehourtranslation.com/auth/register>`_
2. Request your `API Keys <https://www.onehourtranslation.com/profile/apiKeys>`_

or use sandbox for playing with API:

1. Register as a customer on `One Hour Translation Sandbox <http://www.sandbox.onehourtranslation.com/auth/register>`_
2. Request your `snadbox API Keys <http://www.sandbox.onehourtranslation.com/profile/apiKeys>`_

Almost each method of **OhtApi** class return namedtuple (with type *oht_response*) with such structure:

**status** - namedtuple:

	*code* - request status code

	*msg* - request status message, "ok" for OK

**results** - namedtuple, fields list depend on kind of query

**errors** - list of errors

For more details see doc comments for each method.

The API Library must be configured before calling any API method:

.. code-block:: python

	>>> from OhtApi2 import OhtApi
	>>> oht = OhtApi(YOUR_PUBLIK_KEY, YOUR_PRIVATE_KEY, True) # True for use sandbox
	>>> print(oht.account_details())
	oht_response(status=oht_response(code=0, msg='ok'), errors=[], results=oht_response(account_username='YOU_ACCOUNT_NAME', credits='98610.5200', role='customer', account_id='YOUR_ID'))
	...

**OhtApi** class has build-in URLs for product and sandbox API or you can change them if need. Whenever instance is created or URL is change, it try to check URL availability.
	
Where to go from here
---------------------

1. Use doc comments in **OhtApi** class
2. See *test_oht.py* for code example
3. Visit official website `API Developers Guide <https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions>`_
