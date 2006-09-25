# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

from zope.interface import Interface, Attribute
from zope.schema import TextLine, Datetime, Date, Text, Object, Choice
from zope.schema import List, Set, Int, Bool
from calcore.schema import Timedelta

try:
    from zope.i18nmessageid import MessageFactory
except ImportError:
    from zope.i18nmessageid import MessageIDFactory as MessageFactory
_ = MessageFactory("calendar")

class IStorageManager(Interface):
    # MANIPULATORS

    def setStorage(storage_id):
        """Set the storage for events.
        """

    def createEvent(unique_id, dtstart, duration,
                    title, description='', location='', status='TENTATIVE',
                    organizer=None, allday=False, transparent=False,
                    access='PUBLIC'):
        """Create an event.

        unique_id - unique id of event, if left None, autogenerate
        dtstart - start datetime of event
        duration - timedelta of event
        description - description of event
        location - location of event
        status - event status (TENTATIVE, CONFIRMED, CANCELLED)
        organizer - attendee that is organizing this event.
        allday - whether this event is all day or not
        transparent - transparent or opaque
        access - access class (PUBLIC, PRIVATE, CONFIDENTIAL)
        unique_id - optional unique id to use for the event
        """

    def deleteEvent(event):
        """Delete event from storage.
        """

    # ACCESSORS
    def getEvent(event_id):
        """Get an event.

        If event cannot be found, a KeyError will be raised.

        This returns ICalendarEvents.
        """

    def hasEvent(event_id):
        """Returns True if event with given id exists.
        """

    def getEvents(period, search_criteria=None):
        """Get events in a particular period. Don't expand recurrent events.

        period - start datetime, end datetime (half-open time interval)

        It is allowed to put in an open search (datetime, None) as a period.
        This will return all relevant events that exist.

        Filter by search criteria if these are supplied.

        This returns ICalendarEvents. Recurrent events are not expanded.
        """

    def getOccurrences(period, search_criteria=None):
        """Get calendar occurrences in particular period.

        Calendar recurrences are very simple objects that refer back to
        the original event responsible for its creation.

        For non-recurrent events, there is only a single occurrence. An
        recurrent event can have multiple occurrrences, however.

        period - start datetime, end datetime (half-open time interval)

        It is not allowed to put in open search into the indefinite future
        (datetime, None) for period, as this may result in infinite
        events being generated, causing the program to hang.

        Filter by search criteria if these are supplied.

        This returns ICalendarOccurrences.
        """

    def getOccurrencesSegmented(period, search_criteria=None):
        """Like getOccurrences, but segmented by day.

        Split up occurrences that are into multiple ones, one for
        each day.
        """

    def getBlockedPeriods(attendees, period, time_period):
        """Get all periods blocked for people in a particular period.

        The list returned will be sorted. Overlapping periods will be
        merged.

        period - a start datetime, end datetime tuple
        time_period - a start time, end time tuple
        """

    def getFreePeriods(attendees, period, time_period,
                     minimum_duration=None):
        """Get all the free periods available for people in period.

        period - a start datetime, end datetime tuple
        time_period - a start time, end time tuple, only look for free
          slots between these times in a day.
        minimum_duration - optional mininum duration of free slot we're
          interested in.
        """

class IStorage(Interface):
    """A storage contains events.
    """
    # MANIPULATORS
    def createEvent(unique_id, spec):
        """Create event.

        If unique_id is None, a unique id will be generated by the storage.

        spec is an IEventSpecification object which describes the event.
        """

    def deleteEvent(event):
        """Delete event from storage.
        """

    # ACCESSORS
    def getStorageId():
        """Return storage id (should be unique per storage manager).
        """

    def getEvent(event_id):
        """Get an event given event_id.

        If event cannot be found, a KeyError will be raised.
        """

    def getEvents(period, search_criteria):
        """Get all events in a period.

        Search by search criteria.
        """

    def getOccurrences(period, search_criteria):
        """Get all occurrences of event in period.

        Period must be bounded.
        """

class ISearchCriteria(Interface):
    """Event search criteria.
    """
    # any attribute can be None, in which case it is matched with any value

    attendee = Attribute('Attendee')
    participation_status = Attribute('Participation Status')
    participation_role = Attribute('Participation role')
    categories = Attribute('Categories')
    organizer = Attribute('Organizer')

    def clone(attendee=None,
              participation_status=None,
              participation_role=None,
              categories=None,
              organizer=None):
        """Clone these search criteria, overriding any specified as arguments.
        """

class IAttendee(Interface):
    # MANIPULATORS
    def createEvent(**kw):
        """Attendee creates an event.

        dtstart - start of event (datetime)
        duration - duration of event (timedelta)
        description - description of event
        status - event status
        allday - whether event is all-day or not
        transparent - transparent or opaque
        access - access class (PUBLIC, PRIVATE, CONFIDENTIAL)
        """

    # ACCESSORS
    def getAttendeeId():
        """Get unique attendee id.
        """

    def getAttendeeType():
        """Return calendar user type. One of:

        INDIVIDUAL
        GROUP
        RESOURCE
        ROOM
        UNKNOWN
        """

    def getEvents(period, search_criteria=None):
        """Get all events in period for this attendee.

        period - startdatetime, enddatetime tuple for period
        search_criteria - criteria to filter on.
        """

    def getOccurrences(period, search_criteria=None):
        """Get all occurrences of event for this attendee.

        period - startdatetime, enddatetime tuple for period, bounded
        search_criteria - criteria to filter on.
        """

    def getOrganizedEvents():
        """Get all events organized by this attendee.
        """

class IAttendeeSource(Interface):
    """Retrieve attendees from a source.
    """
    def getAttendee(attendee_id):
        """Retrieve an attendee by attendee_id.
        """

    def getCurrentUserAttendeeId():
        """Retrieve the attendee id for the current user.

        If there is no current user, this returns None.
        """

    def getCurrentUserAttendee():
        """Retrieve the attendee object for the current user.

        If there is no current user, this returns None.
        """

    def findByName(query_str, attendee_type=None):
        """Search attendees.
        query_str - should contain part of the name
        attendee_type - optionally filter on attendee_type
        Returns a list of attendee objects which match.
        None matches all, '' matches nothing.
        """

    def getAttendeesOfType(attendee_type):
        """Retrieve all attendees of a certain type.

        May not be implemented for all types if this is turns out
        to be an unscalable solution. Use findByName instead in that case.
        """

    def getAttendeeTypes():
        """Returns all the attendee types that are valid for this source"""

    def getAttendeeFromSpec(vcaladdress):
        """Finds an attendee from an iCalendar vCalAddress specification.

        iCalendar specifies the attendee with an MAILTO: uri, and paramseters
        like CUTYPE. This method allows you to override the conversion from
        iCalendar specification to attendees.

        Returns None when no attendee is found.
        """

class ICalendar(Interface):
    # MANIPULATORS
    def addAttendee(attendee):
        """Add an attendee to this calendar.

        Events for this attendee will then be shown in the calendar.
        """

    def removeAttendee(attendee):
        """Remove an attendee from this calendar.

        Events for this attendee will no longer be shown in the calendar.
        """

    def getMainAttendeeId():
        """Attendee id for which this calendar is the main calendar"""

    def getMainAttendee():
        """Returns the attendee for which this calendar is the main calendar

        When adding an event for the calendar, you need to know in which
        calendar you are creating it, so that the attendee is automatically
        invited to the event
        """

    def import_(self, text, period=(None, None), search_criteria=None):
        """Given iCalendar text, import events.

        This overwrites existing event data where necessary,
        and creates new events and removes existing events. What is
        an existing event depends on the period and search_criteria;
        by default this is all events in the calendar.
        """

    # ACCESSORS

    def getEvent(event_id):
        """Get event by id.

        If event cannot be found, a KeyError will be raised.
        """

    def hasEvent(event_id):
        """Return True only if event with event_id can be found.
        """

    def getEvents(period, search_criteria):
        """Get all events.
        """

    def getOccurrences(period, search_criteria):
        """Get all occurrences of event in period. Period must be bounded.
        """

    def getEventsInDay(date):
        """Get all events on a day, indicated by date.
        """

    def getRecentYears():
        """Get relevant years (this year and a range around it), numerically.
        """

    def getCurrentYear():
        """Get this year.
        """

    def getToday():
        """Get datetime representing today.
        """

    def export(period=(None, None), search_criteria=None):
        """Export this calendar as iCalendar data.

        This exports the events in the calendar as iCalendar data.
        The period and search_criteria can optionally be specified;
        by default all events in the calendar are exported.
        """

Unchanged = object() # marker

class IRecurrenceRule(Interface):
    """Base interface of the recurrence rules.

    Recurrence rules are stored as attributes of ICalendarEvent.
    """
    # regebro: Schoolbells recurrencerules are immutable. gintas said
    # on #schooltool that it was a legacy thing, so I changed it.
    # No recurrence is now a rule as well. Moved out the basic fields.

    def replace(interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged):
        """Return a copy of this recurrence rule with new specified fields."""

    def __eq__(other):
        """See if self == other."""

    def __ne__(other):
        """See if self != other."""

    def apply(event, enddate=None):
        """Apply this rule to an event.

        This is a generator that returns the dates on which the event should
        recur.  Be careful when iterating over these dates -- rules that do not
        have either 'until' or 'count' attributes will go on forever.

        The optional enddate attribute can be used to set a range on the dates
        generated by this function (inclusive).
        """

    def iCalRepresentation(dtstart):
        """Return the rule in iCalendar format.

        Returns a list of strings, each corresponding to a line of iCalendar.
        The first line is for the recurrence rule itself, the following ones
        (if any) describe exception dates.

        dtstart is a datetime representing the date that the recurring
        event starts on.
        """

class INoRecurrenceRule(IRecurrenceRule):
    """Interface for things that doens't recurr"""

class IBasicRecurrenceRule(IRecurrenceRule):
    """Common fields for most recurrences"""
    interval = Int(
        title=_("Interval"),
        min=1,
        description=_("""
        Interval of recurrence (a positive integer).

        For example, to indicate that an event occurs every second day,
        you would create a DailyRecurrenceRule witl interval equal to 2.
        """))

    count = Int(
        title=_("Count"),
        required=False,
        description=_("""
        Number of times the event is repeated.

        Can be None or an integer value.  If count is not None then
        until must be None.  If both count and until are None the
        event repeats forever.
        """))

    until = Date(
        title=_("Until"),
        required=False,
        description=_("""
        The date of the last recurrence of the event.

        Can be None or a datetime.date instance.  If until is not None
        then count must be None.  If both count and until are None the
        event repeats forever.
        """))

    # The Zope3 forms don't handle this well.. It's all very strange and
    # not very reproducable.You seem to get different errors every time.
    # So, exceptions are commented out for now.
    #exceptions = List(
        #title=_("Exceptions",
        #value_type=Date(),
        #description=_("""
        #A list of days when this event does not occur.

        #Values in this list must be instances of datetime.date.
        #"""))

class IDailyRecurrenceRule(IBasicRecurrenceRule):
    """Daily recurrence."""


class IYearlyRecurrenceRule(IBasicRecurrenceRule):
    """Yearly recurrence."""


class IWeeklyRecurrenceRule(IBasicRecurrenceRule):
    """Weekly recurrence."""

    # NB! Change from SchoolTool: This used to be a set if Ints, but there are
    # no widgets for that (and it makes little sense,as we then would just have
    # a list of numbers. I had expected Sets of vocabularies to work, but it
    # seems not. A unique list is however for all practical uses the same as a
    # set, and it works.
    weekdays = Set(
        title=_("Weekdays"),
        value_type=Choice(title=_("Weekday"),
                          vocabulary="CalendarWeekdays"),
        description=_("""
        A set of weekdays when this event occurs.

        Weekdays are represented as integers from 0 (Monday) to 6 (Sunday).
        This is what the `calendar` and `datetime` modules use.

        The event repeats on the weekday of the first occurence even
        if that weekday is not in this set.
        """))

    def replace(interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged, weekdays=Unchanged):
        """Return a copy of this recurrence rule with new specified fields."""


class IMonthlyRecurrenceRule(IBasicRecurrenceRule):
    """Monthly recurrence."""

    monthly = Choice(
        title=_("Behaviour"),
        vocabulary="CalendarMontlyRecurrenceType",
        description=_("""
        Specification of monthly occurence behaviour.

        Can be one of three values: 'monthday', 'weekday', 'lastweekday'.

        'monthday'    specifies that the event recurs on the same day of month
                      (e.g., 25th day of a month).

        'weekday'     specifies that the event recurs on the same week
                      within a month on the same weekday, indexed from the
                      first (e.g. 3rd Friday of a month).

        'lastweekday' specifies that the event recurs on the same week
                      within a month on the same weekday, indexed from the
                      end of month (e.g. 2nd last Friday of a month).
        """))

    def replace(interval=Unchanged, count=Unchanged, until=Unchanged,
                exceptions=Unchanged, monthly=Unchanged):
        """Return a copy of this recurrence rule with new specified fields."""

class ITimed(Interface):
    """Timed period.

    This is a base interface for both ICalendarEvent as well as
    ICalendarOccurrence. It just contains a dtstart and a duration.
    """

    dtstart = Datetime(
        title=_("Start"),
        description=_("""
        Date and time when this event starts.
        """))

    duration = Timedelta(
        title=_("Duration"),
        description=_("""
        The duration of this event.
        """))

class ICalendarEvent(ITimed):
    """Calendar event

    This has the minimum amount of fields an event must have to be usable
    in the calendar, such as title and recurrence.

    API mostly taken from schoolbell, though some is split into
    an ITimed base interface.
    """

    unique_id = TextLine(
        title=_("UID"),
        description=_("""
        A globally unique id for this calendar event.

        iCalendar (RFC 2445) recommeds using the RFC 822 addr-spec syntax
        for unique IDs.  Put the current timestamp and a random number
        on the left of the @ sign, and put the hostname on the right.
        """))

    title = TextLine(
        title=_("Title"),
        description=_("""The title of the event."""))

    description = Text(
        title=_("Description"),
        required=False,
        description=_("""A description of the event."""))

    recurrence = Object(
        title=_("Recurrence"),
        schema=IRecurrenceRule,
        required=False,
        description=_("""
        The recurrence rule.
        """))

    location = TextLine(
        title=_("Location"),
        required=False,
        description=_("""The location where this event takes place."""))

    allday = Bool(
        title=_("All Day Event"),
        required=False)

    def export(private=False):
        """Returns an icalendar.Event() object for ical export.

        By setting private to True, only the time and date will be exported"""

    # we're not supporting the schoolbell event comparison semantics yet.

##     def __eq__(other):
##         """See if self == other."""

##     def __ne__(other):
##         """See if self != other."""

##     def __lt__(other):
##         """See if self < other."""

##     def __gt__(other):
##         """See if self > other."""

##     def __le__(other):
##         """See if self <= other."""

##     def __ge__(other):
##         """See if self >= other."""

    # we're not supporting hasOccurrences() yet

##     def hasOccurrences():
##         """Does the event have any occurrences?

##         Normally all events have at least one occurrence.  However if you have
##         a repeating event that repeats a finite number of times, and all those
##         repetitions are listed as exceptions, then hasOccurrences() will return
##         False.  There are other corner cases as well (e.g. a recurring event
##         with until date that is earlier than dtstart).
##         """

class ICalendarOccurrence(ITimed):
    """An occurrence on a calendar. This stands in for a real event.

    All real information can be found in the original event.
    """

    original = Object(
        title=_("Original"),
        schema=ICalendarEvent,
        description=_("""
        The event that generated this occurrence.
        """))

class IExtendedCalendarEvent(ICalendarEvent):
    """A calendar event extending the schema of ICalendarEvent.
    """
    categories = Set(
        title=_("Categories"),
        description=_("""
        Categories this event is in.
        """),
        value_type=Text(),
        required=False)

    status = Choice(
        title=_("Status"),
        vocabulary="CalendarEventStatus",
        description=_("""
        Event status.
        """),
        required=True)

    transparent = Bool(
        title=_("Transparent"),
        description=_("""
        If an event is set to be transparent, this means this event
        does not block other events.
        """),
        required=False)

    access = Choice(
        title=_('Access'),
        vocabulary="CalendarEventAccess",
        description=_("""
        Event access indicator.
        """),
        required=True)

    document = TextLine(
        title=_("Document"),
        required=False,
        description=_("""A string pointing to a document."""))

class IEventSpecification(IExtendedCalendarEvent):
    """Structure used to pass around the specification of an event.

    It has the structure of an IExtendedCalendar event but is only
    used internally to pass around information.
    """

    # XXX There is also an organizer and an an attendees attribute, but I'm not
    # sure how to specify them at the moment. Organizer should be an Attendee
    # object. Attendees is a dictionary with Attendee objects as keys, and
    # values are a (role, status) tuple, wich must have a valid participation
    # role and a valid participation status. Attendees defaults to {},
    # organizer defaults to None.
    # XXX again: One possibility of cleaning this up is to include a subset
    # of IInvitableCalendarEvent, and the organizer and attendees with methods
    # instead of as parameters to __init__(). //regebro

    def setOnObject(o):
        """Set data as attributes on event object.
        """

    def willModify(o):
        """Checks if the event specification will modify the object.
        """

class IInvitableCalendarEvent(IExtendedCalendarEvent):

    # MANIPULATORS
    def invite(attendees):
        """Invite attendees to invite.
        """

    def setParticipationStatus(attendee, status):
        """Set participation status of attendee for this event.

        If not set, the default participation role is NEEDS-ACTION.

        If the participation status is set to None, the attendee is
        removed from this event.
        """

    def setParticipationRole(attendee, role):
        """Set the role of this participant in the event.

        Needs to be one of:

        CHAIR
        REQ-PARTICIPANT
        OPT-PARTICIPANT
        NON-PARTICIPANT

        If not set, the default participation role is REQ-PARTICIPANT.
        """

    # ACCESSORS
    def getStorageId():
        """Get storage this event is stored in.
        """

    def getEventId():
        """Get the event id for this event (storage-unique).
        """

    def getOrganizerId():
        """Get organizer id for event (in storage-terms)>
        """

    def inCategory(category):
        """Returns true if the event is in a certain category.
        """

    def getAttendeeIds(participation_status=None, participation_role=None):
        """Get the list of participants this event has as attendee_ids.

        You must turn to the attendee source to turn these ids into attendee
        objects.

        If participation_status or role not None, filter on that basis.
        """

    def hasAttendee(attendee):
        """Returns true if this attendee is associated with the event.
        """

    def getParticipationStatus(attendee):
        """Get the participation status of this attendee in the event.

        A participation status of None is returned if the attendee does
        not yet participate in the event.
        """

    def getParticipationRole(attendee):
        """Get the role of this attendee in the event.

        Returns a string with one of:

        CHAIR
        REQ-PARTICIPANT
        OPT-PARTICIPANT
        NON-PARTICIPANT
        """

    def __hash__():
        """Hash value for this event.
        """

#########
# Events
#########

# This could be done with zope.app.event, but I don't want to introduce
# zope.app.event as a dependency. It's not packaged as an egg, for starters.

# Having events for events makes for confusing nomenclature...

class IEventEvent(Interface):
    """Base calendar event event"""

    event = Attribute("The calendar event of the event.")

class IEventCreatedEvent(IEventEvent):
    """A calendar event has been created"""

class IEventModifiedEvent(IEventEvent):
    """A calendar event has been modified"""

class IEventDeletedEvent(IEventEvent):
    """A calendar event has been deleted"""

class IEventParticipationChangeEvent(IEventModifiedEvent):
    """A change in participation status for an attendee"""

    attendee = Attribute("The attendee whose status changed.")
    old_status = Attribute("The previous status.")
    old_status = Attribute("The new status.")
