#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2005 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Recurrence rules.

$Id$
"""

import datetime
import calendar
from sets import Set

from zope.interface import implements

from interfaces import Unchanged
from interfaces import IDailyRecurrenceRule, IWeeklyRecurrenceRule,\
     IMonthlyRecurrenceRule, IYearlyRecurrenceRule, IRecurrenceRule, \
     IBasicRecurrenceRule, INoRecurrenceRule

# CalCore specific modifications:
# - convert to old-style objects (get rid of property())
# - got rid of some import dependencies

class BasicRecurrenceRule:
    """An abstract base class that implements common behaviour."""

    implements(IBasicRecurrenceRule)

    #interval = property(lambda self: self._interval)
    #count = property(lambda self: self._count)
    #until = property(lambda self: self._until)
    #exceptions = property(lambda self: self._exceptions)

    # A string that represents the recurrence frequency in iCalendar.
    # Must be overridden by subclasses.
    ical_freq = None

    def __init__(self, interval=1, count=None, until=None, exceptions=()):
        self.interval = interval
        self.count = count
        self.until = until
        self.exceptions = tuple(exceptions) # XXX I'd prefer a set.
        self._validate()

    def _validate(self):
        if self.count is not None and self.until is not None:
            raise ValueError("count and until cannot be both set (%s, %s)"
                             % (self.count, self.until))
        if not self.interval >= 1:
            raise ValueError("interval must be a positive integer (got %r)"
                             % (self.interval, ))
        for ex in self.exceptions:
            if not isinstance(ex, datetime.date):
                raise ValueError("Exceptions must be a sequence of"
                                 " datetime.dates (got %r in exceptions)"
                                 % (ex, ))

    def replace(self, interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged):
        if interval is Unchanged:
            interval = self.interval
        if count is Unchanged:
            count = self.count
        if until is Unchanged:
            until = self.until
        if exceptions is Unchanged:
            exceptions = self.exceptions
        return self.__class__(interval, count, until, exceptions)

    def __repr__(self):
        return '%s(%r, %r, %r, %r)' % (self.__class__.__name__, self.interval,
                                       self.count, self.until,
                                       self.exceptions)

    def _tupleForComparison(self):
        return (self.__class__.__name__, self.interval, self.count,
                self.until, tuple(self.exceptions))

    def __eq__(self, other):
        """See if self == other."""
        if isinstance(other, BasicRecurrenceRule):
            return self._tupleForComparison() == other._tupleForComparison()
        else:
            return False

    def __ne__(self, other):
        """See if self != other."""
        return not self == other

    def __hash__(self):
        """Return the hash value of this recurrence rule.

        It is guaranteed that if recurrence rules compare equal, hash will
        return the same value.
        """
        return hash(self._tupleForComparison())

    def apply(self, event, enddate=None):
        """Generator that generates dates of recurrences"""
        if enddate:
            assert isinstance(enddate, datetime.date), "enddate must be a date"
            assert not isinstance(enddate, datetime.datetime), \
                    "enddate must be a date, not a datetime"
        cur = event.dtstart.date()
        count = 0
        while True:
            if ((enddate and cur > enddate) or
                (self.count is not None and count >= self.count) or
                (self.until and cur > self.until)):
                break
            if cur not in self.exceptions:
                yield cur
            count += 1
            cur = self._nextRecurrence(cur)

    def _nextRecurrence(self, date):
        """Add the basic step of recurrence to the date."""
        return date + self.interval * date.resolution

    def iCalRepresentation(self, dtstart):
        """See IRecurrenceRule"""
        assert self.ical_freq, 'RecurrenceRule.ical_freq must be overridden'

        if self.count:
            args = 'COUNT=%d;' % self.count
        elif self.until:
            args = 'UNTIL=%s;' % ical_datetime(self.until)
        else:
            args = ''
        extra_args = self._iCalArgs(dtstart)
        if extra_args is not None:
            args += extra_args + ';'

        result = ['RRULE:FREQ=%s;%sINTERVAL=%d'
                  % (self.ical_freq, args, self.interval)]

        if self.exceptions:
            # Exceptions should include the exact time portion as well
            # (this was implemented in revision 1860), however,
            # Mozilla Calendar refuses to work with such exceptions.
            dates = ','.join([ical_date(d) for d in self.exceptions])
            result.append('EXDATE;VALUE=DATE:' + dates)
        return result

    def _iCalArgs(self, dtstart):
        """Return extra iCal arguments as a string.

        Should be overridden by child classes that have specific arguments.
        The returned string must not include the semicolon separator.
        If None is returned, no arguments are inserted.
        """
        pass

class NoRecurrenceRule(BasicRecurrenceRule):
    """This only happens once"""
    implements(INoRecurrenceRule)

    def apply(self, event, enddate=None):
        """Generator that generates dates of recurrences"""
        yield event.dtstart.date()
        
    # XXX implement all the ical stuff


class DailyRecurrenceRule(BasicRecurrenceRule):
    """Daily recurrence rule."""
    implements(IDailyRecurrenceRule)

    ical_freq = 'DAILY'


class YearlyRecurrenceRule(BasicRecurrenceRule):
    """Yearly recurrence rule."""
    implements(IYearlyRecurrenceRule)

    ical_freq = 'YEARLY'

    def _nextRecurrence(self, date):
        """Adds the basic step of recurrence to the date"""
        nextyear = date.year + self.interval
        return date.replace(year=nextyear)

    def _iCalArgs(self, dtstart):
        """Return iCalendar parameters specific to monthly recurrence."""
        # KOrganizer wants explicit BYMONTH and BYMONTHDAY arguments.
        # Maybe it is a good idea to add them for the sake of explicitness.


class WeeklyRecurrenceRule(BasicRecurrenceRule):
    """Weekly recurrence rule."""

    implements(IWeeklyRecurrenceRule)

    #weekdays = property(lambda self: self._weekdays)

    ical_freq = 'WEEKLY'

    def __init__(self, interval=1, count=None, until=None, exceptions=(),
                 weekdays=()):
        self.interval = interval
        self.count = count
        self.until = until
        self.exceptions = tuple(exceptions)
        self.weekdays = tuple(weekdays)
        self._validate()

    def __repr__(self):
        return '%s(%r, %r, %r, %r, %r)' % (
            self.__class__.__name__, self.interval,
            self.count, self.until, self.exceptions, self.weekdays)

    def _validate(self):
        BasicRecurrenceRule._validate(self)
        for dow in self.weekdays:
            if not isinstance(dow, int) or not 0 <= dow <= 6:
                raise ValueError("Day of week must be an integer 0..6 (got %r)"
                                 % (dow, ))

    def replace(self, interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged, weekdays=Unchanged, monthly=Unchanged):
        if interval is Unchanged:
            interval = self.interval
        if count is Unchanged:
            count = self.count
        if until is Unchanged:
            until = self.until
        if exceptions is Unchanged:
            exceptions = self.exceptions
        if weekdays is Unchanged:
            weekdays = self.weekdays
        return self.__class__(interval, count, until, exceptions, weekdays)

    def _tupleForComparison(self):
        return (self.__class__.__name__, self.interval, self.count,
                self.until, self.exceptions, self.weekdays)

    def apply(self, event, enddate=None):
        """Generate dates of recurrences."""
        if enddate:
            assert isinstance(enddate, datetime.date), "enddate must be a date"
            assert not isinstance(enddate, datetime.datetime), \
                    "enddate must be a date, not a datetime"
        cur = start = event.dtstart.date()
        count = 0
        weekdays = Set(self.weekdays)
        weekdays.add(event.dtstart.weekday())
        while True:
            if ((enddate and cur > enddate) or
                (self.count is not None and count >= self.count) or
                (self.until and cur > self.until)):
                return
            # Check that this is the correct week and
            # the desired weekday
            if (weekspan(start, cur) % self.interval == 0 and
                cur.weekday() in weekdays):
                if cur not in self.exceptions:
                    yield cur
                count += 1
            cur = self._nextRecurrence(cur)

    def _nextRecurrence(self, date):
        """Add the basic step of recurrence to the date."""
        return date + date.resolution

    def _iCalArgs(self, dtstart):
        """Return iCalendar parameters specific to monthly recurrence."""
        if self.weekdays:
            return 'BYDAY=' + ','.join([ical_weekdays[weekday]
                                        for weekday in self.weekdays])


class MonthlyRecurrenceRule(BasicRecurrenceRule):
    """Monthly recurrence rule.

    Immutable hashable object.
    """
    implements(IMonthlyRecurrenceRule)

    #monthly = property(lambda self: self._monthly)

    ical_freq = 'MONTHLY'

    def __init__(self, interval=1, count=None, until=None, exceptions=(),
                 monthly="monthday"):
        self.interval = interval
        self.count = count
        self.until = until
        self.exceptions = tuple(exceptions)
        self.monthly = monthly
        self._validate()

    def __repr__(self):
        return '%s(%r, %r, %r, %r, %r)' % (
            self.__class__.__name__, self.interval,
            self.count, self.until, self.exceptions, self.monthly)

    def _validate(self):
        BasicRecurrenceRule._validate(self)
        if self.monthly not in ("monthday", "weekday", "lastweekday"):
            raise ValueError("monthly must be one of 'monthday', 'weekday',"
                             " 'lastweekday'. Got %r" % (self.monthly, ))

    def replace(self, interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged, weekdays=Unchanged, monthly=Unchanged):
        if interval is Unchanged:
            interval = self.interval
        if count is Unchanged:
            count = self.count
        if until is Unchanged:
            until = self.until
        if exceptions is Unchanged:
            exceptions = tuple(self.exceptions)
        if monthly is Unchanged:
            monthly = self.monthly
        return self.__class__(interval, count, until, exceptions, monthly)

    def _tupleForComparison(self):
        return (self.__class__.__name__, self.interval, self.count,
                self.until, self.exceptions, self.monthly)

    def _nextRecurrence(self, date):
        """Add basic step of recurrence to the date."""
        year = date.year
        month = date.month
        while True:
            year, month = divmod(year * 12 + month - 1 + self.interval, 12)
            month += 1 # convert 0..11 to 1..12
            try:
                return date.replace(year=year, month=month)
            except ValueError:
                continue

    def apply(self, event, enddate=None):
        if enddate:
            assert isinstance(enddate, datetime.date), "enddate must be a date"
            assert not isinstance(enddate, datetime.datetime), \
                    "enddate must be a date, not a datetime"
        if self.monthly == 'monthday':
            for date in BasicRecurrenceRule.apply(self, event, enddate):
                yield date
        elif self.monthly == 'weekday':
            for date in self._applyWeekday(event, enddate):
                yield date
        elif self.monthly == 'lastweekday':
            for date in self._applyLastWeekday(event, enddate):
                yield date

    def _applyWeekday(self, event, enddate=None):
        """Generator that generates dates of recurrences."""
        cur = start = event.dtstart.date()
        count = 0
        year = start.year
        month = start.month
        weekday = start.weekday()
        index = (start.day - 1) / 7 + 1

        while True:
            cur = monthindex(year, month, index, weekday)
            if ((enddate and cur > enddate) or
                (self.count is not None and count >= self.count) or
                (self.until and cur > self.until)):
                break
            if cur not in self.exceptions:
                yield cur
            count += 1
            # Next month, please.
            year, month = divmod(year * 12 + month + self.interval - 1, 12)
            month += 1

    def _applyLastWeekday(self, event, enddate=None):
        """Generator that generates dates of recurrences."""
        cur = start = event.dtstart.date()
        count = 0
        year = start.year
        month = start.month
        weekday = start.weekday()
        daysinmonth = calendar.monthrange(year, month)[1]
        index = (start.day - daysinmonth - 1) / 7

        while True:
            cur = monthindex(year, month, index, weekday)
            if ((enddate and cur > enddate) or
                (self.count is not None and count >= self.count) or
                (self.until and cur > self.until)):
                break
            if cur not in self.exceptions:
                yield cur
            count += 1
            # Next month, please.
            year, month = divmod(year * 12 + month + self.interval - 1, 12)
            month += 1

    def _iCalArgs(self, dtstart):
        """Return iCalendar parameters specific to monthly recurrence."""
        if self.monthly == 'monthday':
            return 'BYMONTHDAY=%d' % dtstart.day
        elif self.monthly == 'weekday':
            week = (dtstart.day - 1) / 7 + 1
            return 'BYDAY=%d%s' % (week, ical_weekdays[dtstart.weekday()])
        elif self.monthly == 'lastweekday':
            return 'BYDAY=-1%s' % ical_weekdays[dtstart.weekday()]
        else:
            raise NotImplementedError(self.monthly)


#
# Calendaring functions
#


def weekspan(first, second):
    """Return the distance in weeks between dates.

    For days in the same ISO week, the result is 0.
    For days in adjacent weeks, it is 1, etc.
    """
    firstmonday = first - datetime.timedelta(first.weekday())
    secondmonday = second - datetime.timedelta(second.weekday())
    return (secondmonday - firstmonday).days / 7


def monthindex(year, month, index, weekday):
    """Return the (index)th weekday of the month in a year.

    May return a date beyond month if index is too big.
    """
    # make corrections for the negative index
    # if index is negative, we're really interested in the next month's
    # first weekday, minus n weeks
    if index < 0:
        yeardelta, month = divmod(month, 12)
        year += yeardelta
        month += 1
        index += 1

    # find first weekday
    for day in range(1, 8):
        if datetime.date(year, month, day).weekday() == weekday:
            break

    # calculate the timedelta to the index-th
    shift = (index - 1) * datetime.timedelta(7)

    # return the result
    return datetime.date(year, month, day) + shift

# from schoolbell.calendar.icalendar

ical_weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

def ical_date(value):
    """Format a date as an iCalendar DATE value.

        >>> ical_date(datetime.date(2004, 3, 4))
        '20040304'
    """
    return value.strftime("%Y%m%d")

def ical_datetime(value):
    """Format a datetime as an iCalendar DATETIME value.

        >>> ical_datetime(datetime.datetime(2004, 12, 16, 10, 45, 07))
        '20041216T104507'

    """
    return value.strftime('%Y%m%dT%H%M%S')
