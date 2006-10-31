import unittest
import doctest
from calcore import cal
from datetime import datetime, timedelta
from calcore.interfaces import IEventParticipationChangeEvent

def _invite_subscriber(eventevent):
    if IEventParticipationChangeEvent.providedBy(eventevent):
        # always accept for now
        eventevent.event.setParticipationStatus(
            eventevent.attendee, 'ACCEPTED')

class CalTestCase(unittest.TestCase):
    def setUp(self):
        self._m = cal.StorageManager()
        self._m.setStorage(cal.MemoryStorage('storage'))
        self._s = cal.SimpleAttendeeSource(self._m)


    def test_inviteEvent(self):
        from zope.event import subscribers
        subscribers.append(_invite_subscriber)

        room = self._s.createRoom('room', 'Room')
        martijn = self._s.createIndividual('martijn', 'Martijn')
        meeting = martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Martijn's Meeting")
        meeting.invite([room])
        self.assertEquals(
            'ACCEPTED',
            meeting.getParticipationStatus(room))
        subscribers.remove(_invite_subscriber)

    def test_getOccurrencesEndsInPeriod(self):
        martijn = self._s.createIndividual('martijn', 'Martijn')
        # an event that goes from 16 until 02 the next day
        meeting = martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(hours=10),
            status='TENTATIVE',
            title="Martijn's Meeting")
        # we get all occurrences, starting the next day, so we
        # expect an event that ends next day to show up
        occ = martijn.getOccurrences(
            (datetime(2005, 4, 11, 0, 0),
             datetime(2005, 4, 14, 0, 0)))
        self.assertEquals(
            1, len(occ))

    def test_getOccurrencesStartsInPeriod(self):
        martijn = self._s.createIndividual('martijn', 'Martijn')
        # an event that goes from 16 until 02 the next day
        meeting = martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(hours=10),
            status='TENTATIVE',
            title="Martijn's Meeting")
        # we get all occurrences until the start of the 11th,
        # so event ends after this period ends
        occ = martijn.getOccurrences(
            (datetime(2005, 4, 7, 0, 0),
             datetime(2005, 4, 11, 0, 0)))
        self.assertEquals(
            1, len(occ))

    def test_attendeeManagement(self):
        calendar = cal.Calendar(self._m, self._s)
        martijn = self._s.createIndividual('martijn', 'Martijn')
        guido = self._s.createIndividual('guido', 'Guido')
        calendar.addAttendee(martijn)
        calendar.addAttendee(guido)
        self.failUnlessEqual(calendar.getMainAttendeeId(), 'martijn')
        self.failUnlessEqual(calendar.getMainAttendee().getAttendeeId(),
                             'martijn')
        calendar.removeAttendee(martijn)
        self.failUnlessEqual(calendar.getMainAttendeeId(), 'guido')
        self.failUnlessEqual(calendar.getMainAttendee().getAttendeeId(),
                             'guido')

    def test_searchCriteria(self):
        martijn = self._s.createIndividual('martijn', 'Martijn')
        meeting = martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Martijn's Meeting")
        guido = self._s.createIndividual('guido', 'Guido')
        meeting = guido.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Martijn's Meeting")
        sc = cal.SearchCriteria(attendees=martijn)
        events = self._m.getEvents((None, None), sc)
        self.failUnlessEqual(len(events), 1)
        sc = cal.SearchCriteria(attendees=(martijn, guido))
        events = self._m.getEvents((None, None), sc)
        self.failUnlessEqual(len(events), 2)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(CalTestCase)])
    suite.addTests([doctest.DocFileSuite('../../../doc/usecase.txt')])
#    suite.addTests([doctest.DocFileSuite('../../../doc/storage.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/calendar.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/attendee.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/category.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/recurrence.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/meeting.txt')])
    suite.addTests([doctest.DocFileSuite('../../../doc/allday.txt')])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
