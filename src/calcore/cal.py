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

from logging import getLogger
from datetime import datetime, timedelta, date, time
import socket # to get hostname
combine = datetime.combine
from types import ListType, TupleType

import icalendar
from sets import Set

from calcore import util, recurrent

from zope.interface import implements
from interfaces import IAttendee, IAttendeeSource,\
     IStorageManager, IStorage, IInvitableCalendarEvent, ICalendar,\
     ISearchCriteria, ICalendarOccurrence, ITimed, IEventSpecification
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.event import notify
from events import *

try:
    from zope.i18nmessageid import MessageFactory
except ImportError:
    from zope.i18nmessageid import MessageIDFactory as MessageFactory
_ = MessageFactory("calendar")

_marker = object()

class EventSpecification:
    """Structure used to pass around the specification of an event.

    This is only used temporarily in the implementation, and is
    never stored.

    attendees is a list of tuples, (attendee, role, status)
    """
    implements(IEventSpecification)

    def __init__(self, dtstart, duration,
                 title='',
                 description='',
                 location='',
                 status='TENTATIVE',
                 organizer=None,
                 recurrence=None,
                 allday=False,
                 categories=None,
                 transparent=False,
                 access='PUBLIC',
                 document=None,
                 attendees=[]):
        self.dtstart = dtstart
        self.duration = duration
        self.title = title
        self.description = description
        self.status = status
        self.location = location
        self.organizer = organizer
        self.recurrence = recurrence
        self.allday = allday
        if categories is None:
            categories = Set()
        self.categories = categories
        self.transparent = transparent
        self.access = access
        self.document = document
        self.attendees = attendees

    def setOnObject(self, o):
        """Set this specification on underlying object.
        """
        for name, value in self.__dict__.items():
            if name not in ('organizer', 'attendees'):
                if getattr(o, name, _marker) != value:
                    setattr(o, name, value)
                    modified = True
        if self.organizer is not None:
            o._setParticipationStatus(self.organizer, 'ACCEPTED')
            o.setParticipationRole(self.organizer, 'REQ-PARTICIPANT')
            o._organizer_id = self.organizer.getAttendeeId()
        else:
            o._organizer_id = None

        if self.attendees:
            for (attendee, role, status) in self.attendees:
                o.setParticipationRole(attendee, role)
                o._setParticipationStatus(attendee, status)

    def willModify(self, o):
        """Checks is this specification would modify the object.
        """
        for name, value in self.__dict__.items():
            if name not in ('organizer', 'attendees'):
                if getattr(o, name, _marker) != value:
                    return True
        if (self.organizer is not None and
            o._organizer_id != self.organizer.getAttendeeId() or
            o.getParticipationStatus(self.organizer) != 'ACCEPTED' or
            o.getParticipationRole(self.organizer) != 'REQ-PARTICIPANT'):
            return True

        if self.attendees:
            for (attendee, role, status) in self.attendees:
               if (o.getParticipationStatus(attendee) != status or
                   o.getParticipationRole(attendee) != 'REQ-PARTICIPANT'):
                   return True


class StorageManagerBase:

    implements(IStorageManager)

    def __init__(self):
        self._storage = None

    # MANIPULATORS

    def setStorage(self, storage):
        self._storage = storage

    def createEvent(self, unique_id=None, **kw):
        return self.createEventFromSpecification(unique_id, 
                                                 EventSpecification(**kw))

    def createEventFromSpecification(self, unique_id, spec):
        event = self._storage.createEvent(unique_id, spec)
        notify(EventCreatedEvent(event))
        return event

    def deleteEvent(self, event):
        self._storage.deleteEvent(event)
        notify(EventDeletedEvent(event))

    # ACCESSORS

    def getEvent(self, event_id):
        return self._storage.getEvent(event_id)

    def hasEvent(self, event_id):
        try:
            self.getEvent(event_id)
            return True
        except KeyError:
            return False

    def getEvents(self, period, search_criteria=None):
        return self._storage.getEvents(period, search_criteria)

    def getOccurrences(self, period, search_criteria=None):
        return self._storage.getOccurrences(period, search_criteria)

    def getOccurrencesSegmented(self, period, search_criteria=None):
        return segmentOccurrences(period,
                                  self.getOccurrences(period, search_criteria))

    def getBlockedPeriods(self, attendees, period, time_period):
        # XXX need to check for events that an attendee is interested
        # in, but not actively participating
        blocked_periods = {}
        begins, ends = period
        time_begins, time_ends = time_period
        for attendee in attendees:
            search_criteria = SearchCriteria(attendees=[attendee])
            for occ in self.getOccurrencesSegmented(period, search_criteria):
                # transparent or canceled events don't count
                if (occ.original.transparent or
                    occ.original.status == 'CANCELED'):
                    continue
                # And neither does events you are not going to:
                if (occ.original.getParticipationStatus(attendee) in
                    ['DECLINED', 'DELEGATED']):
                    continue
                dtstart = occ.dtstart
                dtend = dtstart + occ.duration
                if dtend < begins:
                    continue
                if dtstart >= ends:
                    continue
                day_start = combine(dtstart.date(), time_begins)
                if dtstart < day_start:
                    dtstart = day_start
                # since we're segmenting occurrences, this is safe
                day_end = combine(dtstart.date(), time_ends)
                if dtend >= day_end:
                    dtend = day_end
                blocked_periods[(dtstart, dtend)] = None
        blocked_periods = blocked_periods.keys()
        # also block all periods outside time_period
        d = begins.date()
        end_d = ends.date()
        if ends.time() == time(0, 0):
            end_d -= timedelta(days=1)
        while d <= end_d:
            blocked_periods.append((combine(d, time(0, 0)),
                                    combine(d, time_begins)))
            next_day = d + timedelta(days=1)
            blocked_periods.append((combine(d, time_ends),
                                    combine(next_day, time(0, 0))))
            d = next_day
        return util.removeOverlaps(blocked_periods)


    def getFreePeriods(self, attendees, period, time_period,
                     minimal_duration=None):
        blocked_periods = self.getBlockedPeriods(
            attendees, period, time_period)
        begins, ends = period
        time_begins, time_ends = time_period
        # now find out any unblocked periods
        free_periods = []
        if begins < combine(begins.date(), time_begins):
            begins = combine(begins.date(), time_begins)
        if ends > combine(ends.date(), time_ends):
            ends = combine(ends.date(), time_ends)

        last_block_begins = begins
        for dtstart, dtend in blocked_periods:
            if dtstart.time() >= time_begins and last_block_begins != dtstart:
                if (minimal_duration is None or
                    (dtstart - last_block_begins) >= minimal_duration):
                    free_periods.append((last_block_begins, dtstart))
            last_block_begins = dtend
        if last_block_begins != ends:
            if (minimal_duration is None or
                (ends - last_block_begins) >= minimal_duration):
                free_periods.append((last_block_begins, ends))
        return free_periods

class StorageManager(StorageManagerBase):
    pass

class StorageBase:
    """Minimalistic implementation of a storage.
    """
    implements(IStorage)

    def __init__(self, storage_id, hostname=None):
        self._storage_id = storage_id
        self._events = self._initEvents()
        self._hostname = hostname or socket.getfqdn()

    def _initEvents(self):
        raise NotImplementedError

    def _eventFactory(self, event_id, spec):
        raise NotImplementedError

    # MANIPULATORS
    def createEvent(self, unique_id, spec):
        if unique_id is None:
            unique_id = addrspec_unique_id(
                '%s-%s' %
                (self._storage_id, len(self._events)), self._hostname)
        event = self._eventFactory(unique_id, spec)
        self._events[unique_id] = event
        return event

    def deleteEvent(self, event):
        del self._events[event.unique_id]

    # ACCESSORS

    def getStorageId(self):
        return self._storage_id

    def getEvent(self, event_id):
        return self._events[event_id]

    def getEvents(self, period, search_criteria):
        events = self._getMatchingEvents(search_criteria)
        return [event for event in events if inPeriod(event, period)]

    def getOccurrences(self, period, search_criteria):
        assertPeriodBounded(period)
        events = self._getMatchingEvents(search_criteria)
        result = []
        for event in events:
            result.extend(event.expand(period))
        return result

    # PRIVATE

    def _getMatchingEvents(self, search_criteria):
        if search_criteria is None:
            search_criteria = NullSearchCriteria()

        result = []
        for event in self._events.values():
            if search_criteria._match(event):
                result.append(event)
        return result

class MemoryStorage(StorageBase):
    def _initEvents(self):
        return {}

    def _eventFactory(self, event_id, spec):
        return Event(event_id, spec)

class SearchCriteria:
    implements(ISearchCriteria)

    def __init__(self,
                 attendees=None,
                 participation_status=None,
                 participation_role=None,
                 categories=None,
                 organizer=None):
        if (attendees is not None and
           not isinstance(attendees,(ListType, TupleType))):
            attendees = [attendees]
        self.attendees = attendees
        self.participation_status = participation_status
        self.participation_role = participation_role
        self.categories = categories
        self.organizer = organizer

    def clone(self, attendees=None, participation_status=None,
              participation_role=None, categories=None, organizer=None):
        if (attendees is not None and
           not isinstance(attendees,(ListType, TupleType))):
            attendees = [attendees]
        attendees = self.attendees or attendees
        participation_status = (self.participation_status or
                                participation_status)
        participation_role = self.participation_role or participation_role
        categories = self.categories or categories
        organizer = self.organizer or organizer
        return SearchCriteria(attendees, participation_status,
                              participation_role, categories, organizer)

    # this method is not part of ISearchCriteria, as other storages may
    # implement altogether different ways to fetch relevant events.
    def _match(self, event):
        if self.categories is not None:
            for category in self.categories:
                if event.inCategory(category):
                    break
            else:
                return False

        if (self.organizer is not None and
            event.getOrganizerId() != self.organizer.getAttendeeId()):
            return False

        if self.attendees is None:
            return True

        for attendee in self.attendees:
            if not event.hasAttendee(attendee):
                continue

            if (self.participation_status is not None and
                self.participation_status !=
                event.getParticipationStatus(attendee)):
                continue

            if (self.participation_role is not None and
                self.participation_role !=
                event.getParticipationRole(attendee)):
                continue

            #This attendee matched
            return True

        # No attendee matched
        return False


class NullSearchCriteria(SearchCriteria):
    def __init__(self):
        SearchCriteria.__init__(self)

class EventBase:
    implements(IInvitableCalendarEvent)

    def __init__(self, unique_id, spec):
        self.unique_id = unique_id
        self._participation_state = self._initParticipationState()
        self._participation_role = self._initParticipationRole()

        spec.setOnObject(self)

        if self.allday:
            self.alldayAdjust()

    def _initParticipationState(self):
        raise NotImplementedError

    def _initParticipationRole(self):
        raise NotImplementedError

    # MANIPULATORS

    def invite(self, attendees):
        for attendee in attendees:
            if self.getParticipationStatus(attendee) is None:
                self.setParticipationStatus(attendee, 'NEEDS-ACTION')
                self.setParticipationRole(attendee, 'REQ-PARTICIPANT')

    def setParticipationStatus(self, attendee, status):
        assert status in [None, 'NEEDS-ACTION', 'ACCEPTED', 'DECLINED',
                          'TENTATIVE', 'DELEGATED']
        old_status = self.getParticipationStatus(attendee)
        if old_status == status:
            return
        self._setParticipationStatus(attendee, status)
        notify(EventParticipationChangeEvent(self, attendee, old_status, status))

    def _setParticipationStatus(self, attendee, status):
        # implementation specific overriding
        attendee_id = attendee.getAttendeeId()
        if status is None:
            del self._participation_state[attendee_id]
            del self._participation_role[attendee_id]
            return
        self._participation_state[attendee_id] = status

    def setParticipationRole(self, attendee, role):
        assert role in ['CHAIR', 'REQ-PARTICIPANT', 'OPT-PARTICIPANT',
                        'NON-PARTICIPANT']
        self._participation_role[attendee.getAttendeeId()] = role

    def alldayAdjust(self):
        self.dtstart = combine(self.dtstart.date(), time(0, 0))
        if self.duration is None:
            # 1 day event
            self.duration = timedelta(days=1)
        else:
            # Adjust upwards
            days = self.duration.days
            rest = self.duration - timedelta(days)
            if rest != timedelta(0) or days == 0:
                days += 1
            self.duration = timedelta(days=days)

    # ACCESSORS

    def getOrganizerId(self):
        return self._organizer_id

    def inCategory(self, category):
        return category in self.categories

    def getAttendeeIds(self,
                       participation_status=None, participation_role=None):
        result = []
        for attendee_id, status in self._participation_state.items():
            if (participation_status is not None and
                participation_status != status):
                continue
            if (participation_role is not None and
                participation_role != self._participation_role[attendee_id]):
                continue
            result.append(attendee_id)
        return result

    def hasAttendee(self, attendee):
        return self.getParticipationStatus(attendee) is not None

    def getParticipationStatus(self, attendee):
        return self._participation_state.get(
            attendee.getAttendeeId())

    def getParticipationRole(self, attendee):
        return self._participation_role.get(
            attendee.getAttendeeId())

    def __hash__(self):
        return hash(self.unique_id)

    def __cmp__(self, other):
        # sort first on start datetime, then on public id
        if not isinstance(other, EventBase):
            return 1
        return cmp(
            (self.dtstart, self.unique_id),
            (other.dtstart, self.unique_id))

    def expand(self, period):
        """Returns ICalendarOccurrences for this event in period."""
        # if we don't have a recurrence, we only generate a single occurrence
        if self.recurrence is None:
            if not inPeriod(self, period):
                return []
            return [Occurrence(self.dtstart, self.duration, self)]

        result = []
        enddate = period[1].date()
        for d in self.recurrence.apply(self, enddate):
            dtstart = self.dtstart
            dtstart = combine(d, dtstart.time())
            # must be in right period
            if not inPeriod(Timed(dtstart, self.duration), period):
                continue
            result.append(Occurrence(dtstart, self.duration, self))
        return result

    def export(self, private=False):
        """Exports the event as an icalendar.Event.

        Setting private to True will hide all information except date/time
        information. This should be used for private events when exporting
        is done by somebody who does not have full rights to the event
        """

        e = icalendar.Event()
        if not self.allday:
            e.add('dtstart', self.dtstart)
            # exporting duration directly instead of dtend
            # seems to confuse some clients, like KOrganizer,
            # so calculate dtend instead
            e.add('dtend', self.dtstart + self.duration)
        else:
            # all day event
            # create dtstart with VALUE=DATE property
            dtstart_prop = icalendar.vDate(self.dtstart.date())
            dtstart_prop.params['VALUE'] = icalendar.vText('DATE')
            e.add('dtstart', dtstart_prop, encode=0)
            # now create dtend with VALUE=DATE property
            dtend = self.dtstart + self.duration
            dtend_prop = icalendar.vDate(dtend)
            dtend_prop.params['VALUE'] = icalendar.vText('DATE')
            e.add('dtend', dtend_prop, encode=0)
        if self.recurrence is not None:
            r = self.recurrence
            d = {'freq': r.ical_freq, 'interval': r.interval}
            if r.count is not None:
                d['count'] = r.count
            if r.until is not None:
                d['until'] = r.until
            e.add('rrule', icalendar.vRecur(d))
        if self.transparent:
            e.add('transp', 'TRANSPARENT')
        else:
            e.add('transp', 'OPAQUE')
        e.add('uid', self.unique_id)
        e.add('class', self.access)
        if private:
            # Hide all non-time information as it may be sensitive.
            e.add('summary', _("Private Event"))
            return e

        e.add('summary', self.title)
        if self.description:
            e.add('description', self.description)
        if self.location:
            e.add('location', self.location)
        if self.categories:
            e.set_inline('categories', list(self.categories))
        if self.document:
            e.add('attach', self.document)
        e.add('status', self.status)
        return e


class Timed:
    implements(ITimed)

    def __init__(self, dtstart, duration):
        self.dtstart = dtstart
        self.duration = duration

class Event(EventBase):
    def _initParticipationState(self):
        return {}

    def _initParticipationRole(self):
        return {}

class Occurrence:
    implements(ICalendarOccurrence)

    def __init__(self, dtstart, duration, original):
        self.dtstart = dtstart
        self.duration = duration
        self.original = original

class AttendeeBase:
    implements(IAttendee)

    def __init__(self, attendee_id, name, attendee_type):
        self._attendee_id = attendee_id
        self._name = name
        self._attendee_type = attendee_type

    # MANIPULATORS

    def createEvent(self, **kw):
        kw['organizer'] = self
        return self._getStorageManager().createEvent(unique_id=None, **kw)

    # ACCESSORS

    def getAttendeeId(self):
        return self._attendee_id

    def getAttendeeType(self):
        return self._attendee_type

    def getEvents(self, period, search_criteria=None):
        if search_criteria is None:
            search_criteria = SearchCriteria(attendees=[self])
        else:
            search_criteria = search_criteria.clone(attendees=[self])
        return self._getStorageManager().getEvents(
            period, search_criteria)

    def getOccurrences(self, period, search_criteria=None):
        if search_criteria is None:
            search_criteria = SearchCriteria(attendees=[self])
        else:
            search_criteria = search_criteria.clone(attendees=[self])
        return self._getStorageManager().getOccurrences(
            period, search_criteria)

    def getOrganizedEvents(self, search_criteria=None):
        if search_criteria is None:
            search_criteria = SearchCriteria(organizer=self)
        else:
            search_criteria = search_criteria.clone(organizer=self)
        return self._getStorageManager().getEvents(
            (None, None), search_criteria)

    def _getStorageManager(self):
        raise NotImplementedError

class Attendee(AttendeeBase):
    def __init__(self, storage_manager, attendee_id,
                 name, attendee_type):
        AttendeeBase.__init__(
            self, attendee_id, name, attendee_type)
        self._storage_manager = storage_manager

    def _getStorageManager(self):
        return self._storage_manager

ical_weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

class CalendarBase:
    implements(ICalendar)

    _logger = getLogger('calcore.CalendarBase')

    def __init__(self):
        self._attendees = self._initAttendees()

    def _initAttendees(self):
        return {}

    # MANIPULATORS

    def addAttendee(self, attendee):
        self._attendees[attendee.getAttendeeId()] = None

    def removeAttendee(self, attendee):
        del self._attendees[attendee.getAttendeeId()]

    def getMainAttendeeId(self):
        attendee_keys = self._attendees.keys()
        if len(attendee_keys) == 0:
            return None
        return attendee_keys[0]

    def getMainAttendee(self):
        attendee_id = self.getMainAttendeeId()
        if attendee_id is None:
            return None
        source = self._getAttendeeSource()
        return source.getAttendee(attendee_id)

    def import_(self, text, period=(None, None), search_criteria=None,
                synchronize=0):
        """Given iCalendar text, import events.

        This overwrites existing event data where necessary,
        and creates new events. If synchronize is set to 1,
        it also removes existing events. This is used when the
        iCalendar client is assumed to have retrieved the calendar
        first, as when you are using it via WebDAV.
        """
        self._logger.log(5, 'import_ raw ical text: \n\n%s\n\n', text)
        # repair text with proper line endings if necessary
        text = self._repairText(text)
        # get all events (to use when we import)
        events = self.getEvents(period, search_criteria)
        # make a set of their unique_ids
        known_uids = Set([event.unique_id for event in events])
        # now parse iCalendar text
        ical = icalendar.Calendar.from_string(text)
        if ical is None:
            return
        ical_uids = Set()
        # now walk through all events
        for e in ical.walk('VEVENT'):
            uid = e.decoded('UID')
            # we have to have uid
            assert uid is not None
            ical_uids.add(uid)
            # edit existing event
            if uid in known_uids:
                self._importExistingEvent(uid, e)
            else:
                if not self.hasEvent(uid):
                    # this uid is really new, so import it
                    self._importNewEvent(uid, e)
                else:
                    # this uid exists already, but is not in our calendar,
                    # so refuse to modify it
                    continue
        if synchronize:
            # now for all uids that were in known_uids but not in
            # ical_uids, we need to remove the related events
            removed_uids = known_uids - ical_uids
            for uid in removed_uids:
                self._deleteEvent(self.getEvent(uid))

    def _importExistingEvent(self, uid, e):
        event = self.getEvent(uid)
        spec = self._importEventSpecification(e)
        if spec.willModify(event):
            spec.setOnObject(event)
            notify(EventModifiedEvent(event))

    def _importNewEvent(self, uid, e):
        m = self._getStorageManager()
        spec = self._importEventSpecification(e)
        m.createEventFromSpecification(uid, spec)

    def _importEventSpecification(self, e):
        """Given an iCalendar event object, create event specification.
        """
        asrc = self._getAttendeeSource()

        kw = {}
        kw['dtstart'], kw['duration'], kw['allday'] =\
                       self._getDtstartDuration(e)

        kw['title'] = e.decoded('SUMMARY', '')
        kw['description'] = e.decoded('DESCRIPTION', '')
        kw['location'] = e.decoded('LOCATION', '')
        kw['status'] = e.decoded('STATUS', 'TENTATIVE')
        # XXX we make the first attendee of the calendar the organizer.
        # this is perhaps slightly bogus
        if e.has_key('ORGANIZER'):
            organizer = asrc.getAttendeeFromSpec(e['organizer'])
        else:
            organizer = None

        if organizer is None:
            organizer = self._getDefaultOrganizer()

        kw['organizer'] = organizer

        if e.has_key('ATTENDEE'):
            attendees = []
            attendee_list = e['ATTENDEE']
            if not isinstance(attendee_list, ListType):
                attendee_list = [attendee_list]
            for attendee_spec in attendee_list:
                attendee = asrc.getAttendeeFromSpec(attendee_spec)
                status = attendee_spec.params.get('PARTSTAT', 'NEEDS-ACTION')
                role = attendee_spec.params.get('ROLE', 'REQ-PARTICIPANT')
                attendees.append((attendee, role, status))
            kw['attendees'] = attendees

        kw['categories'] = self._getCategories(e)
        kw['transparent'] = e.decoded('TRANSP', 'OPAQUE') == 'TRANSPARENT'
        kw['access'] = e.decoded('CLASS', 'PUBLIC')
        kw['document'] = e.decoded('ATTACH', None)
        rrule = e.decoded('RRULE', None)
        if rrule is not None:
            kw['recurrence'] = self._getRecurrenceRule(rrule)
        else:
            kw['recurrence'] = None
        return EventSpecification(**kw)

    def _getDefaultOrganizer(self):
        return self.getMainAttendee()

    def _deleteEvent(self, event):
        self._getStorageManager().deleteEvent(event)

    def _getDtstartDuration(self, component):
        dtstart = component.decoded('DTSTART', None)
        dtend = component.decoded('DTEND', None)
        duration = component.decoded('DURATION', None)
        if duration is not None and dtend is not None:
            # too much info: set duration back to None to recompute it and
            # ensure consistency
            self._logger.warning("Invalid iCalendar data: Event '%s' has both "
                                 "dtend and duration. Ignoring the duration." %
                                 component.decoded('UID'))
            duration = None
        assert dtstart is not None
        assert ((dtend is None and duration is not None) or
                (dtend is not None and duration is None) or
                (dtend is None and duration is None))
        allday = False
        # if we're just getting a date, we assume allday events and
        # convert the date into a datetime
        if type(dtstart) is date:
            dtstart = combine(dtstart, time(0, 0))
            allday = True
        else:
            dtstart = float_datetime(dtstart)
        if dtend is not None:
            if type(dtend) is date:
                dtend = combine(dtend, time(0, 0))
            else:
                dtend = float_datetime(dtend)
            duration = dtend - dtstart
        else:
            if duration is None:
                # no duration, no dtend, follow iCalendar rules
                if type(dtstart) is date:
                    dtend = combine(dtend, time(0, 0) + timedelta(days=1))
                else:
                    dtend = dtstart
                duration = dtend - dtstart
        return dtstart, duration, allday

    def _getRecurrenceRule(self, rrule):
        freq = rrule['FREQ'][0]
        if freq == 'DAILY':
            r = recurrent.DailyRecurrenceRule()
        elif freq == 'YEARLY':
            r = recurrent.YearlyRecurrenceRule()
        elif freq == 'WEEKLY':
            byday = rrule.get('BYDAY')
            weekdays = []
            if byday is not None:
                for day in byday:
                    weekdays.append(ical_weekdays.index(day))
            r = recurrent.WeeklyRecurrenceRule(weekdays=weekdays)
        elif freq == 'MONTHLY':
            byday = rrule.get('BYDAY')
            if byday is not None:
                if byday[0][0] == '-':
                    monthly = 'lastweekday'
                else:
                    monthly = 'weekday'
            else:
                monthly = 'monthday'
            r = recurrent.MonthlyRecurrenceRule(monthly=monthly)
        interval = rrule.get('INTERVAL')
        if interval is not None:
            r.interval = interval[0]
        count = rrule.get('COUNT')
        if count is not None:
            r.count = count[0]
        until = rrule.get('UNTIL')
        if until is not None:
            r.until = until[0]
        return r

    def _getCategories(self, e):
        try:
            categories = Set(e.get_inline('CATEGORIES'))
        except KeyError:
            categories = Set()
        except AttributeError:
            # XXX depending on implementation specific behavior
            # in icalendar..
            # we could not get categories using get_inline
            # as we probably have multiple CATEGORIES entries
            categories = e.decoded('CATEGORIES', None)
            if categories is None:
                categories = Set()
            else:
                categories = Set(categories)
        return categories

    def _repairText(self, text):
        # repair text to have \r\n if necessary
        i = text.find('\n')
        if i != -1 and i > 0:
            if text[i - 1] != '\r':
                lines = text.split('\n')
                text = '\r\n'.join(lines)
        return text

    # ACCESSORS

    def getEvent(self, event_id):
        # XXX should check whether event applies to any of the
        # attendees
        m = self._getStorageManager()
        return m.getEvent(event_id)

    def hasEvent(self, event_id):
        return self._getStorageManager().hasEvent(event_id)

    def getEvents(self, period, search_criteria=None):
        result = {}
        if search_criteria is not None:
            search_criteria = search_criteria.clone(
                attendees=self.getAttendees())
        else:
            search_criteria  = SearchCriteria(attendees=self.getAttendees())
        return self._getStorageManager().getEvents(period, search_criteria)

    def getOccurrences(self, period, search_criteria=None):
        result = {}
        if search_criteria is not None:
            search_criteria = search_criteria.clone(
                attendees=self.getAttendees())
        else:
            search_criteria  = SearchCriteria(attendees=self.getAttendees())
        return self._getStorageManager().getOccurrences(period, search_criteria)

    def getOccurrencesSegmented(self, period, search_criteria=None):
        # first get occurrences
        occurrences = self.getOccurrences(period, search_criteria)
        # now segment occurrences, spitting them up where they cross
        # borders (day and start and end of period)
        return segmentOccurrences(period, occurrences)

    def getEventsInDay(self, date, search_criteria=None):
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(1)
        period = (start, end)
        return self.getEvents(period, search_criteria)

    def getOccurrencesInDay(self, date, search_criteria=None):
        """Returns all occurrences in day.

        This segments the larger occurrences that might have started the
        previous day, only returning the part of it that starts at
        this day. Similarly, occurrences that span past the end of the day
        are cut off.
        """
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(1)
        period = (start, end)
        return self.getOccurrencesSegmented(period, search_criteria)

    def getRecentYears(self):
        year = self.getCurrentYear()
        # one year in the past to one year in the future
        return range(year - 1, year + 2)

    def getCurrentYear(self):
        return self.getToday().year

    def getToday(self):
        return datetime.today()

    def getAttendees(self):
        source = self._getAttendeeSource()
        result = []
        for attendee_id in self._attendees.keys():
            result.append(source.getAttendee(attendee_id))
        return result

    def export(self, period=(None, None), search_criteria=None):
        """Export calendar data in ICalendar format"""
        ical = icalendar.Calendar()
        ical.add('prodid', '-//CalCore //nuxeo.com//')
        ical.add('version', '2.0')

        for event in self.getEvents(period, search_criteria):
            e = event.export()
            ical.add_component(e)
        ical_text = ical.as_string()
        self._logger.log(5, 'export generated ical text: \n\n%s\n\n', ical_text)
        return ical_text


    def _getStorageManager(self):
        raise NotImplementedError

    def _getAttendeeSource(self):
        raise NotImplementedError

class Calendar(CalendarBase):
    def __init__(self, storage_manager, attendee_source):
        CalendarBase.__init__(self)
        self._storage_manager = storage_manager
        self._attendee_source = attendee_source

    def _getStorageManager(self):
        return self._storage_manager

    def _getAttendeeSource(self):
        return self._attendee_source

class SimpleAttendeeSource:
    """Simplistic attendee source that needs to be replaced in a real app.

    Basically only there for testing reasons.
    """
    implements(IAttendeeSource)

    def __init__(self, storage_manager):
        self._storage_manager = storage_manager
        self._attendees = {}

    # MANIPULATORS

    def createIndividual(self, attendee_id, name):
        attendee = Attendee(
            self._storage_manager, attendee_id,
            name, 'INDIVIDUAL')
        self._attendees[attendee_id] = attendee
        return attendee

    def createRoom(self, attendee_id, name):
        attendee = Attendee(
            self._storage_manager,
            attendee_id, name, 'ROOM')
        self._attendees[attendee_id] = attendee
        return attendee

    # ACCESSORS

    def getAttendee(self, attendee_id):
        return self._attendees[attendee_id]

    def getCurrentUserAttendeeId(self):
        # there is no concept of a current user at this level
        return None

    def getCurrentUserAttendee(self):
        # there is no concept of a current user at this level
        return None

    def findByName(self, query_str, attendee_type=None):
        result = []
        for attendee in self._attendees.values():
            if query_str not in attendee.getName():
                continue
            if (attendee_type is not None and
                attendee.getAttendeeType() is not attendee_type):
                continue
            result.append(attendee)
        return result

    def getAttendeesOfType(self, attendee_type):
        result = []
        for attendee in self.attendees.values():
            if attendee_type is attendee.getAttendeeType():
                result.append(attendee)
        return result

    def getAttendeeTypes():
        return ['INDIVIDUAL', 'ROOM']

    def getAttendeeFromSpec(self, vcaladdress):
        id = vcaladdress.decode()
        return self._attendees.get(id, None)


def Period(dtstart, duration):
    return (dtstart, timedelta(minutes=duration))

def inPeriod(o, (b, e)):
    """Check whether timed object is in period.

    o - an ITimed, something at least with dtstart and a duration
    attribute

    start - start of period (datetime). If None, no beginning
    end - end of period (datetime). If None, no end
    """
    if b is not None and o.dtstart + o.duration <= b:
        return False
    if e is not None and o.dtstart >= e:
        return False
    return True

def sameDay(dt, dt2):
    return dt.date() == dt2.date()

def roundtimedelta(td):
    """Round timedelta up to the nearest day.
    """
    if td.seconds > 0 or td.microseconds > 0:
        return timedelta(days=td.days + 1)
    else:
        return td

def float_datetime(dt):
    """Take a datetime and turn it into local time, floating, if necessary.
    """
    if dt.tzinfo is None:
        return dt
    dt = dt.astimezone(icalendar.LocalTimezone())
    return dt.replace(tzinfo=None)

def assertPeriodBounded(period):
    assert period[0] is not None, "Period is unbounded (into the past)"
    assert period[1] is not None, "Period is unbounded (into the future)"

def addrspec_unique_id(unique_maker, hostname):
    result = iso8601(datetime.now())
    result += '-%s' % unique_maker
    result += '@%s' % hostname
    return result

def iso8601(dt):
    return  '%.4d%.2d%.2dT%.2d%.2d%.2d' % (
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

def segmentOccurrences(period, occurrences):
    """Given a sequence of occurrences, split them up.

    Splitting up is by day, so that each new occurrence fits within
    a single day. Splitting up is also by period, so that period borders
    are like day borders.
    """
    start, end = period
    result = []
    for occ in occurrences:
        x = occ.dtstart
        if x < start:
            x = start
        y = occ.dtstart + occ.duration
        # calculate all day borders between x and y
        borders = []
        while 1:
            x = combine(x.date(), time(0, 0)) + timedelta(1)
            if x > end or x > y:
                break
            borders.append(x)
        # include start and end itself if necessary
        if start > occ.dtstart:
            borders = [start] + borders
        else:
            if not borders or occ.dtstart != borders[0]:
                borders = [occ.dtstart] + borders
        if end < y:
            borders.append(end)
        else:
            borders.append(y)
        # now created occurrences from borders
        e = borders.pop()
        while borders:
            s = borders.pop()
            occ = Occurrence(s, e - s, occ.original)
            if inPeriod(occ, period):
                result.append(occ)
            e = s
    return result

def CalendarVocabularyFactory(list):
    terms = []
    for item in list:
        terms.append(SimpleTerm(item, item, _(item)))
    return SimpleVocabulary(terms)

def CalendarEventStatusVocabulary(context):
    return CalendarVocabularyFactory(['TENTATIVE', 'CONFIRMED', 'CANCELED'])

def CalendarEventAccessVocabulary(context):
    return CalendarVocabularyFactory(['PUBLIC', 'PRIVATE', 'CONFIDENTIAL'])

def CalendarMontlyRecurrenceTypeVocabulary(context):
    return CalendarVocabularyFactory(['monthday', 'weekday', 'lastweekday'])

def CalendarWeekdaysVocabulary(context):
    terms = []
    for day in range(0,7):
        terms.append(SimpleTerm(day, day, _('weekday_%s' % str(day))))
    return SimpleVocabulary(terms)
