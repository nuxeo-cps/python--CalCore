CalCore
=======
This is a Python implementation of a Calendaring system, supporting such 
things as personal and group calendars with meetings and resources, 
recurring events and iCal import/export.

Dependencies
-----------
- zope.interface, zope.schema, zope.i18nmessageid, zope.event from Zope3.  
- iCalendar from Max M and Codespeak.

If you are reading this, you probably downloaded the CalCore tgz. 
CalCore is also available as a Python Egg. You may want to install it
that way instead, it's easier.


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
at products that bundle CalCore with Zope support, such as CPSSharedCalendar
or CalCMF. Any such bundle should come with it's own installation instructions.

For your non-Zope Python product
--------------------------------
The easiest way to install CalCore is to use the EasyInstall utilities
from http://peak.telecommunity.com/DevCenter/EasyInstall .
With these you can just type:

  sudo easy_install calcore

And CalCore and all it's dependencies will be downloaded and installed.
If you don't want or can't use EasyInstall, you can install CalCore
from source with

   python setup.py install.

You also need to download and install all the dependencies listed above.


Running the tests
=================
You can run CalCores tests with:

  python test.py

Note that all dependencies need to be accessible on the python-path for this
to work, and also zope.testing.


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
