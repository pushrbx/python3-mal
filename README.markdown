| Build Status |                                                                              |
|--------------|------------------------------------------------------------------------------|
| Travis       | [![Travis Build Status][travis-build-svg]][travis-build-link]                |         |


python3-mal [![pypi download][pypi-version-svg]][pypi-link] [![pypi download][pypi-format-svg]][pypi-link]
==========

Provides programmatic access to MyAnimeList data.
This is a fork of python-mal. It uses lxml instead of beautifulsoup, and it's working with python 3.
There are automatic travis and teamcity builds on every last sunday of the month to ensure that the package is working fine with the current version of MAL.

Dependencies
============

- python 3.* (tested with 3.7 and 3.8)
- pytz
- requests
- lxml
- nose (only if you want to run tests, though!)
- cssselect

Installation
============

After cloning the repository, navigate to the directory and run `python setup.py install`.

Getting Started
===============

The `myanimelist.session.Session` class handles requests to MAL, so you'll want to create one first:

    from myanimelist.session import Session
    s = Session()

Then if you want to fetch an anime, say, Cowboy Bebop:
  
    bebop = s.anime(1)
    print bebop

Objects in python-mal are lazy-loading: they won't go out and fetch MAL info until you first-request it. So here, if you want to retrieve, say, the things related to Cowboy Bebop:

    for how_related,items in bebop.related.iteritems():
      print how_related
      print "============="
      for item in items:
        print item
      print ""

You'll note that there's a pause while Cowboy Bebop's information is fetched from MAL.

Documentation
=============

To find out more about what `python-mal` is capable of, [visit the docs here](http://python-mal.readthedocs.org/en/latest/index.html). 

Testing
=======

Testing requires `nose`. To run the tests that come with python-mal:

  1. Navigate to the python-mal directory
  2. Create a textfile named `credentials.txt` and put your MAL username and password in it, separated by a comma, or set environment variables named `MAL_USERNAME` and `MAL_PASSWORD` with the appropriate values.
  3. Run `nosetests`.

Make sure you don't spam the tests too quickly! One of the tests involves POSTing invalid credentials to MAL, so you're likely to be IP-banned if you do this too much in too short a span of time.

Differences from the original repo
===================================

- Instead of beautiful soup this module uses lxml
- There are scheduled tests every sunday.
- I've removed some of the functionalities: popular tags parsing and favourite parsing on user profiles because they were unstable.

Change log
==========
0.2.7 - Adapted MAL changes: characters and staff on datasheets have absolute urls. Staff table has been changed to multiple table elements.     
0.2.6 - added broadcast time parsing for currently aired anime shows and added some minor fixes.    
0.2.5 - added promotion video parsing on anime datasheets     
0.2.4 - Adapted to the new MAL ssl enforcement     
0.2.3.1 - upgraded to requests 2.11   
0.2.3.0 - performance improvements in xpath queries.     
0.2.2 - adapted to new SEO url rule changes and DOM changes on MAL.     
0.2.1 - replaced beautifulsoup with lxml.      

<!-- Badges -->
[travis-build-svg]: https://travis-ci.org/pushrbx/python3-mal.svg
[teamcity-build-svg]: https://ci.pushrbx.net/app/rest/builds/buildType:(id:Python3mal_Build)/statusIcon.svg
[pypi-format-svg]: https://img.shields.io/pypi/format/python3-mal.svg
[pypi-version-svg]: https://img.shields.io/pypi/v/python3-mal.svg
[pypi-link]: https://pypi.python.org/pypi/python3-mal
[travis-build-link]: https://travis-ci.org/pushrbx/python3-mal
[teamcity-build-link]: https://ci.pushrbx.net/viewType.html?buildTypeId=Python3mal_Build&guest=1
