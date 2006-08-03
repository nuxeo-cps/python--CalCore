#!/usr/bin/env python

from setuptools import setup

setup(name='calcore',
      package_dir={'': 'src'},
      packages=['calcore'],
      version='2.1.0',
      install_requires=['zope.interface >= 3.0',
                        'zope.schema >= 3.0',
                        'zope.i18nmessageid >= 3.0',
                        'zope.event >= 3.0',
                        'icalendar >= 0.10'],
      dependency_links=['http://download.zope.org/distribution/',
                        'http://codespeak.net/icalendar/eggs/'],
      
      # metadata for upload to PyPI
      author='Martijn Faassen, Infrae;Lennart Regebro, Nuxeo',
      author_email='lregebro@nuxeo.com',
      description='Calendaring system',
      license='GPL2',
      keywords='calendar icalendar',
      url='http://www.cps-project.org/sections/projects/calendar_server ',
      long_description="""CalCore is an advanced, flexible calendaring component for Python. It
        allows the Python developer do write advanced calendaring applications
        either using their own event storage or integrating with external
        calendar servers.
        
        Features of the CalCore include among others:
        
        * Support for making private calendars, shared calendars, resource
        booking and more.
        * integration with iCalendar clients (Apple iCal, Mozilla Sunbird,
        KOrganizer...) using the iCalendar protocol,
        * invitation workflow,
        * meeting support, including helper functions to look for free time,
        * recurring event support (thanks to SchoolTools recurrence
        implementation, http://www.schooltool.org),
        * etc.
        
        CalCore is being used as the core of Nuxeos CalZope and
        CPSSharedCalendar products, products for integrating with Zope and CPS.
        These products provide a complete web-based user interface to the
        CalCore calendaring.""",
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Operating System :: OS Independent',
                   'Topic :: Office/Business :: Groupware'],
      platforms='All',
      )
