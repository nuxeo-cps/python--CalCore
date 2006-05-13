CalCore
=======
This is a Python implementation of a Calendaring system, supporting such 
things as personal and group calendars with meetings and resources, 
recurring events and iCal import/export.

Dependencies
-----------
- zope.interface, zope.schema and zope.i18nmessageid from Zope3.
- iCalendar from Max M and Codespeak.

You should have recieved CalCore in a bundle that includes all dependencies.
If for some reason you do not want to use a bundle, the dependencies can be
found here:

zope.interface     svn://svn.zope.org/repos/main/Zope3/tags/ZopeX3-3.0.0/src/zope/interface
zope.schema        svn://svn.zope.org/repos/main/Zope3/tags/ZopeX3-3.0.0/src/zope/schema
zope.i18nmessageid svn://svn.zope.org/repos/main/Zope3/tags/ZopeX3-3.0.0/src/zope/i18nmessageid
iCalendar          svn:http://codespeak.net/svn/iCalendar/tag/iCalendar-0.10



Installation
============
CalCore and it's dependencies all need to be installed on the Python 
path to be used. This can be achieved in several different ways. Which
way you want to use depends largely on how you want to use CalCore.

As a Zope 2 product
-------------------
CalCore installs as a Zope 2 product by simply copying directory into your 
Zope instance Products directory. We recommend you call the directory 
'CalCore' to avoid conflicts.  Zope 2 will on restart discover CalCore and it 
will automatically be inserted into your Python path.

However, we strongly recommend that you for Zope usage should take a look
at products that bundle CalCore with Zope support, such as CPSSharedCalendar.
Any such bundle should come with it's own installation instructions.

From your non-Zope Python product
---------------------------------
If you recieved CalCore as a part of a CalCore python distribution
(named CalCore-bundle-x.x.x.tgz) this can be installed with
the command python setup.py install.

This will install CalCore and all it's dependencies.


Running the tests
=================
You can run CalCores tests with:

  python test.py

Note that all dependencies need to be accessible on the python-path for this
to work, including zope.testing:
svn://svn.zope.org/repos/main/Zope3/tags/ZopeX3-3.0.0/src/zope/testing


Other
=====
For more information, see the doc directory. These examples are doctests,
so their API documentation should be correct. There is also an interfaces.py
module describing the API, see src/calcore/interfaces.py.


Contributors
============
CalCore development was financed by Nuxeo <http://www.nuxeo.com/>.

The main authors were:
- Martijn Faassen faassen@infrae.com
- Lennart Regebro regebro@nuxeo.com

CalCore uses a testrunner and a recurrent event implementation from
the Schoolbell project, which can be found here:

http://www.schooltool.org


