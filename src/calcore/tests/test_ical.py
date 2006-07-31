import unittest
from calcore import cal, recurrent
from datetime import datetime, timedelta
from sets import Set

class AyeCalTestCase(unittest.TestCase):
    def setUp(self):
        self._m = cal.StorageManager()
        self._m.setStorage(cal.MemoryStorage('storage'))
        self._s = cal.SimpleAttendeeSource(self._m)
        self._calendar = cal.Calendar(self._m, self._s)

        martijn = self._s.createIndividual('martijn', 'Martijn')

        self._calendar.addAttendee(martijn)

        meeting = martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Martijn's Meeting",
            location='Room 1')
        meeting2 = martijn.createEvent(
            dtstart=datetime(2005, 4, 11, 17, 00),
            duration=timedelta(minutes=45),
            status='TENTATIVE',
            title='Another meeting',
            location='Room 2',
            document='/path/to/some/document',
            categories=Set(['Public Holiday',
                            'Wonderful Event']))

        self._meeting_uid = meeting.unique_id
        self._meeting2_uid = meeting2.unique_id

    def test_export_import1(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # now we import the text again.
        self._calendar.import_(text)

        # nothing should be changed!

        # we need to reconnect to the events
        meeting = self._calendar.getEvent(self._meeting_uid)
        meeting2 = self._calendar.getEvent(self._meeting2_uid)

        self.assertEquals(
            "Martijn's Meeting",
            meeting.title)
        self.assertEquals(
            "Another meeting",
            meeting2.title)
        self.assertEquals(
            datetime(2005, 4, 10, 16, 0),
            meeting.dtstart)
        self.assertEquals(
            datetime(2005, 4, 11, 17, 0),
            meeting2.dtstart)
        self.assertEquals(
            Set(['Public Holiday', 'Wonderful Event']),
            meeting2.categories)
        self.assertEquals(None, meeting.document)
        self.assertEquals('/path/to/some/document', meeting2.document)

    def test_export_import2(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # change a summary in the text
        text = text.replace("Martijn's Meeting", "Foo's Meeting")
        # now we import the text again.
        self._calendar.import_(text)
        meeting = self._calendar.getEvent(self._meeting_uid)
        meeting2 = self._calendar.getEvent(self._meeting2_uid)

        self.assertEquals(
            "Foo's Meeting",
            meeting.title)
        self.assertEquals(
            "Another meeting",
            meeting2.title)

    def test_export_import_change_datetime(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # change a dtstart in the text
        text = text.replace('DTSTART:20050411T170000',
                            'DTSTART:20050412T180000')
        # now we import the text again.
        self._calendar.import_(text)
        meeting = self._calendar.getEvent(self._meeting_uid)
        meeting2 = self._calendar.getEvent(self._meeting2_uid)
        self.assertEquals(
            datetime(2005, 4, 12, 18, 0),
            meeting2.dtstart)

    def test_export_import_new_event(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # now add a new event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050501T160000
DURATION:PT1H
LOCATION:Room 3
SUMMARY:Inserted meeting
UID:hoi
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        meeting = self._calendar.getEvent(self._meeting_uid)
        meeting2 = self._calendar.getEvent(self._meeting2_uid)
        meeting3 = self._calendar.getEvent('hoi')
        self.assertEquals(
            'Inserted meeting',
            meeting3.title)
        self.assertEquals(
            'Room 3',
            meeting3.location)
        self.assertEquals(
            datetime(2005, 5, 1, 16),
            meeting3.dtstart)
        self.assertEquals(
            timedelta(hours=1),
            meeting3.duration)

    def test_export_import_remove_event(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # we create a new event and remove an existing event,
        # simply by fiddling with the uid
        i = text.find('UID:')
        replaced_uid = text[i + 4:text.find('\r\n', i)]
        text = text.replace(replaced_uid, 'dag')
        self._calendar.import_(text, synchronize=1)
        # first determine which of the two events is left (one got
        # replaced)
        if self._m.hasEvent(self._meeting_uid):
            self.assertEquals(self._meeting2_uid, replaced_uid)
            self.assert_(not self._m.hasEvent(self._meeting2_uid))
            expected_uid = self._meeting_uid
        else:
            self.assertEquals(self._meeting_uid, replaced_uid)
            self.assert_(self._m.hasEvent(self._meeting2_uid))
            self.assert_(not self._m.hasEvent(self._meeting_uid))
            expected_uid = self._meeting2_uid
        expected_event = self._m.getEvent(expected_uid)
        # now verify new event's existence
        new_event = self._m.getEvent('dag')

    def test_export_import_duration(self):
        # export the calendar to iCalendar text
        text = self._calendar.export()
        # we modify a DTEND to DURATION instead
        text = text.replace('DTEND:20050411T174500',
                            'DURATION:PT75M')
        self._calendar.import_(text)
        meeting = self._m.getEvent(self._meeting_uid)
        meeting2 = self._m.getEvent(self._meeting2_uid)
        self.assertEquals(
            timedelta(minutes=75),
            meeting2.duration)

    def test_export_import_recurrence(self):
        # export it
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
RRULE:FREQ=DAILY;INTERVAL=1
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        # now import again
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences((datetime(2005, 4, 1),
                                                     datetime(2005, 4, 14)))
        # we expect 10 occurrences, 8 for the recurrent event, 2 for the
        # non-recurrent event
        self.assertEquals(10, len(occurrences))

    def test_export_import_recurrence2(self):
        text = self._calendar.export()
        # first we make an event recurrent
        text = insert_lines_textually(text, "SUMMARY:Martijn's Meeting\r\n",
                                      ['RRULE:FREQ=DAILY;INTERVAL=1'])
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences((datetime(2005, 4, 1),
                                                     datetime(2005, 4, 14)))
        # we expect 4 + 1 occurrences; 4 for the recurrent event and 1 for
        # the non-recurrent event
        self.assertEquals(5, len(occurrences))

    def test_export_import_recurrence_unrecur(self):
        text = self._calendar.export()
        # first we make an event recurrent
        text = insert_lines_textually(text, "SUMMARY:Martijn's Meeting\r\n",
                                      ['RRULE:FREQ=DAILY;INTERVAL=1'])
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences((datetime(2005, 4, 1),
                                                     datetime(2005, 4, 14)))
        # we expect 4 + 1 occurrences; 4 for the recurrent event and 1 for
        # the non-recurrent event
        self.assertEquals(5, len(occurrences))
        # now we unrecur the event again
        lines = [
            line for line in text.split('\r\n')
            if not line.startswith('RRULE:')]
        text = '\r\n'.join(lines)
        # and we import again
        self._calendar.import_(text)
        # we expect just 2 occurrences; one for each event
        occurrences = self._calendar.getOccurrences((datetime(2005, 4, 1),
                                                     datetime(2005, 4, 14)))
        self.assertEquals(2, len(occurrences))

    def test_status(self):
        text = self._calendar.export()
        # now turn all the status into confirmed
        text = text.replace('STATUS:TENTATIVE', 'STATUS:CONFIRMED')
        # reimport
        self._calendar.import_(text)
        meeting = self._calendar.getEvent(self._meeting_uid)
        meeting2 = self._calendar.getEvent(self._meeting2_uid)
        self.assertEquals(
            'CONFIRMED',
            meeting.status)
        self.assertEquals(
            'CONFIRMED',
            meeting2.status)

    def test_status_add(self):
        # export events
        text = self._calendar.export()
        # now textually add a new event that's confirmed
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
STATUS:CONFIRMED
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        # now import again
        self._calendar.import_(text)
        # now we should find that the existing events are still
        # tentative
        self.assertEquals(
            'TENTATIVE',
            self._calendar.getEvent(self._meeting_uid).status)
        self.assertEquals(
            'TENTATIVE',
            self._calendar.getEvent(self._meeting2_uid).status)
        # but the new one is confirmed
        self.assertEquals(
            'CONFIRMED',
            self._calendar.getEvent('hoi').status)

    def test_categories_new_event(self):
        # export events
        text = self._calendar.export()
        # now textually add a new event that has categories
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
STATUS:CONFIRMED
CATEGORIES:HOLIDAY,MISC
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        # now import again
        self._calendar.import_(text)
        self.assertEquals(
            Set(['HOLIDAY', 'MISC']),
            self._calendar.getEvent('hoi').categories)

    def test_categories_new_event_different(self):
        # export events
        text = self._calendar.export()
        # now textually add a new event that has categories,
        # in the Korganizer way (not sure whether this is standards
        # compliant, but spec does say CATEGORIES can occur multiple
        # times)
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
STATUS:CONFIRMED
CATEGORIES:HOLIDAY
CATEGORIES:MISC
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        # now import again
        self._calendar.import_(text)
        self.assertEquals(
            Set(['HOLIDAY', 'MISC']),
            self._calendar.getEvent('hoi').categories)

    def test_categories_existing_event(self):
        text = self._calendar.export()
        # first we make an event recurrent
        text = insert_lines_textually(text, "SUMMARY:Martijn's Meeting\r\n",
                                      ['CATEGORIES:HOLIDAY,MISC'])
        self._calendar.import_(text)
        self.assertEquals(
            Set(['HOLIDAY', 'MISC']),
            self._calendar.getEvent(self._meeting_uid).categories)

    def test_categories_existing_event_different(self):
        text = self._calendar.export()
        # first we make an event recurrent
        text = insert_lines_textually(text, "SUMMARY:Martijn's Meeting\r\n",
                                      ['CATEGORIES:HOLIDAY',
                                       'CATEGORIES:MISC'])
        self._calendar.import_(text)
        self.assertEquals(
            Set(['HOLIDAY', 'MISC']),
            self._calendar.getEvent(self._meeting_uid).categories)

    def test_transparent(self):
        text = self._calendar.export()
        text = text.replace('TRANSP:OPAQUE', 'TRANSP:TRANSPARENT')
        self._calendar.import_(text)
        self.assertEquals(
            True,
            self._calendar.getEvent(self._meeting_uid).transparent)

    def test_transparent2(self):
        text = self._calendar.export()
        self._calendar.import_(text)
        self.assertEquals(
            False,
            self._calendar.getEvent(self._meeting_uid).transparent)

    def test_transparent_new(self):
        # export events
        text = self._calendar.export()
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
STATUS:CONFIRMED
TRANSP:TRANSPARENT
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        # now import again
        self._calendar.import_(text)
        self.assertEquals(
            True,
            self._calendar.getEvent('hoi').transparent)

    def test_access_new(self):
        text = self._calendar.export()
        new_event = """\
BEGIN:VEVENT
DTSTART:20050406T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Inserted meeting
UID:hoi
STATUS:CONFIRMED
TRANSP:TRANSPARENT
CLASS:PRIVATE
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        self.assertEquals(
           'PRIVATE',
           self._calendar.getEvent('hoi').access)


    def test_access_change(self):
        text = self._calendar.export()
        text = text.replace('CLASS:PUBLIC', 'CLASS:PRIVATE')
        self._calendar.import_(text)
        self.assertEquals(
            'PRIVATE',
            self._calendar.getEvent(self._meeting_uid).access)

    def test_access_change_confidential(self):
        text = self._calendar.export()
        text = text.replace('CLASS:PUBLIC', 'CLASS:CONFIDENTIAL')
        self._calendar.import_(text)
        self.assertEquals(
            'CONFIDENTIAL',
            self._calendar.getEvent(self._meeting_uid).access)

class RecurrentImportExportTestCase(unittest.TestCase):
    def setUp(self):
        self._m = cal.StorageManager()
        self._m.setStorage(cal.MemoryStorage('storage'))
        self._s = cal.SimpleAttendeeSource(self._m)
        self._calendar = cal.Calendar(self._m, self._s)

        martijn = self._s.createIndividual('martijn', 'Martijn')

        self._calendar.addAttendee(martijn)

    def test_daily_recurrence_simple(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=DAILY;INTERVAL=1
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 4, 1),
             datetime(2005, 4, 10)))
        self.assertEquals(9, len(occurrences))

    def test_daily_recurrence_until(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20050406
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 4, 1),
             datetime(2005, 4, 10)))
        self.assertEquals(6, len(occurrences))

    def test_daily_recurrence_count(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 4, 1),
             datetime(2005, 4, 10)))
        self.assertEquals(4, len(occurrences))

    def test_yearly_recurrence_simple(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=YEARLY;INTERVAL=1
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2010, 4, 10)))
        self.assertEquals(6, len(occurrences))

    def test_weekly_recurrence_simple(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=WEEKLY;INTERVAL=1
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2005, 4, 30)))
        self.assertEquals(5, len(occurrences))
        occurrences.sort(lambda x, y: cmp(x.dtstart, y.dtstart))
        self.assertEquals(datetime(2005, 4, 1, 16), occurrences[0].dtstart)
        self.assertEquals(datetime(2005, 4, 8, 16), occurrences[1].dtstart)
        self.assertEquals(datetime(2005, 4, 15, 16), occurrences[2].dtstart)
        self.assertEquals(datetime(2005, 4, 22, 16), occurrences[3].dtstart)
        self.assertEquals(datetime(2005, 4, 29, 16), occurrences[4].dtstart)

    def test_weekly_recurrence_multidays(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,FR
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2005, 4, 30)))
        self.assertEquals(9, len(occurrences))
        occurrences.sort(lambda x, y: cmp(x.dtstart, y.dtstart))
        self.assertEquals(datetime(2005, 4, 1, 16), occurrences[0].dtstart)
        self.assertEquals(datetime(2005, 4, 4, 16), occurrences[1].dtstart)
        self.assertEquals(datetime(2005, 4, 8, 16), occurrences[2].dtstart)
        self.assertEquals(datetime(2005, 4, 11, 16), occurrences[3].dtstart)
        self.assertEquals(datetime(2005, 4, 15, 16), occurrences[4].dtstart)
        self.assertEquals(datetime(2005, 4, 18, 16), occurrences[5].dtstart)
        self.assertEquals(datetime(2005, 4, 22, 16), occurrences[6].dtstart)
        self.assertEquals(datetime(2005, 4, 25, 16), occurrences[7].dtstart)
        self.assertEquals(datetime(2005, 4, 29, 16), occurrences[8].dtstart)

    def test_monthly_recurrence_simple(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=MONTHLY;INTERVAL=1
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2005, 12, 10)))
        self.assertEquals(9, len(occurrences))

    def test_monthly_recurrence_weekday(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050401T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=MO
END:VEVENT"""
        # note that even though iCalendar says first monday of the
        # month in byday, the recurrence implementation simplifies
        # matters and will assume the same day in the month as the
        # original event is used instead, starting to count from
        # the start of the month, or the end of the month if the
        # BYDAY starts with -.
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2005, 8, 4)))
        self.assertEquals(4, len(occurrences))
        occurrences.sort(lambda x, y: cmp(x.dtstart, y.dtstart))
        # 2005/4/1 is a friday, so first friday of the month is assumed
        self.assertEquals(datetime(2005, 4, 1, 16), occurrences[0].dtstart)
        self.assertEquals(datetime(2005, 5, 6, 16), occurrences[1].dtstart)
        self.assertEquals(datetime(2005, 6, 3, 16), occurrences[2].dtstart)
        self.assertEquals(datetime(2005, 7, 1, 16), occurrences[3].dtstart)
        # august will not be included, as we stop searching before the
        # friday (the 5th)

    def test_monthly_recurrence_lastweekday(self):
        text = self._calendar.export()
        # now textually add a new recurrent event
        new_event = """\
BEGIN:VEVENT
DTSTART:20050420T160000
DURATION:PT1H
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=-MO
END:VEVENT"""
        # note that even though iCalendar says last monday of the
        # month in byday, the recurrence implementation simplifies
        # matters and will assume the same day in the month as the
        # original event is used instead, starting to count from
        # the end the month
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 3, 1),
             datetime(2005, 8, 23)))
        self.assertEquals(4, len(occurrences))
        occurrences.sort(lambda x, y: cmp(x.dtstart, y.dtstart))
        # 2005/4/1 is a friday, so first friday of the month is assumed
        self.assertEquals(datetime(2005, 4, 20, 16), occurrences[0].dtstart)
        self.assertEquals(datetime(2005, 5, 18, 16), occurrences[1].dtstart)
        self.assertEquals(datetime(2005, 6, 22, 16), occurrences[2].dtstart)
        self.assertEquals(datetime(2005, 7, 20, 16), occurrences[3].dtstart)
        # august will not be included, as we stop searching before the
        # wednesday (the 24th)

    def test_no_duration_no_dtend_date(self):
        # when dtstart is a DATE, and dtend is absent, dtend is end of
        # this day
        text = self._calendar.export()
        new_event = """\
BEGIN:VEVENT
DTSTART:20050503
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 5, 1),
             datetime(2005, 6, 1)))
        self.assertEquals(1, len(occurrences))
        self.assertEquals(
            datetime(2005, 5, 3),
            occurrences[0].dtstart)
        self.assertEquals(
            timedelta(1),
            occurrences[0].duration)

    def test_no_duration_no_dtend_datetime(self):
        # when dtstart is a DATETIME, and dtend is absent, dtend is same
        # as dtstart
        text = self._calendar.export()
        new_event = """\
BEGIN:VEVENT
DTSTART:20050503T160000
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 5, 1),
             datetime(2005, 6, 1)))
        self.assertEquals(1, len(occurrences))
        self.assertEquals(
            datetime(2005, 5, 3, 16, 0),
            occurrences[0].dtstart)
        self.assertEquals(
            timedelta(0),
            occurrences[0].duration)

    def test_duration_and_dtend(self):
        # This is invalid data evidently generated by some icalendar software
        text = self._calendar.export()
        new_event = """\
BEGIN:VEVENT
DTSTART:20050503T160000
DURATION:PT2H
DTEND:20050503T170000
LOCATION:Room Foo
SUMMARY:Test meeting
UID:hoi
END:VEVENT"""
        text = insert_event_textually(text, new_event)
        self._calendar.import_(text)
        occurrences = self._calendar.getOccurrences(
            (datetime(2005, 5, 1),
             datetime(2005, 6, 1)))
        self.assertEquals(1, len(occurrences))
        self.assertEquals(
            datetime(2005, 5, 3, 16, 0),
            occurrences[0].dtstart)
        self.assertEquals(
            timedelta(0,3600),
            occurrences[0].duration)
        
        
class AllDayImportExportTestCase(unittest.TestCase):
    def setUp(self):
        self._m = cal.StorageManager()
        self._m.setStorage(cal.MemoryStorage('storage'))
        self._s = cal.SimpleAttendeeSource(self._m)
        self._calendar = cal.Calendar(self._m, self._s)
        self._martijn = martijn = self._s.createIndividual('martijn', 'Martijn')
        self._calendar.addAttendee(martijn)

    def test_allday_export(self):
        meeting = self._martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(days=1),
            status='TENTATIVE',
            title="Martijn's Meeting",
            location='Room 1',
            allday=True)
        # export the calendar to iCalendar text
        text = self._calendar.export()
        uid = meeting.unique_id
        # remove event
        self._m.deleteEvent(meeting)
        # and import again, event should reappear and still be
        # all day
        self._calendar.import_(text)
        event = self._calendar.getEvent(uid)
        self.assert_(event.allday)
        self.assertEquals(timedelta(days=1),
                          event.duration)

    def test_allday_export_no_duration(self):
        meeting = self._martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=None,
            status='TENTATIVE',
            title="Martijn's Meeting",
            location='Room 1',
            allday=True)
        # export the calendar to iCalendar text
        text = self._calendar.export()
        uid = meeting.unique_id
        # remove event
        self._m.deleteEvent(meeting)
        # and import again, event should reappear and still be
        # all day
        self._calendar.import_(text)
        event = self._calendar.getEvent(uid)
        self.assert_(event.allday)
        self.assertEquals(timedelta(days=1),
                          event.duration)

    def test_allday_export_two_days(self):
        meeting = self._martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(days=2),
            status='TENTATIVE',
            title="Martijn's Meeting",
            location='Room 1',
            allday=True)
        # export the calendar to iCalendar text
        text = self._calendar.export()
        uid = meeting.unique_id
        # remove event
        self._m.deleteEvent(meeting)
        # and import again, event should reappear and still be
        # all day
        self._calendar.import_(text)
        event = self._calendar.getEvent(uid)
        self.assert_(event.allday)
        self.assertEquals(timedelta(days=2),
                          event.duration)

def insert_event_textually(text, event_text):
    # correct newline story
    event_text = '\r\n'.join(event_text.strip().split('\n'))
    event_text += '\r\n'
    # now look for end of text, and insert event there
    i = text.find('END:VCALENDAR')
    # insert just before it
    result = text[:i] + event_text + text[i:]
    return result

def insert_lines_textually(text, after, lines):
    lines = [line.strip() + '\r\n' for line in lines]
    i = text.find(after)
    i = i + len(after)
    # insert just after i
    result = text[:i] + ''.join(lines) + text[i:]
    return result


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(AyeCalTestCase)])
    suite.addTests([unittest.makeSuite(RecurrentImportExportTestCase)])
    suite.addTests([unittest.makeSuite(AllDayImportExportTestCase)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
