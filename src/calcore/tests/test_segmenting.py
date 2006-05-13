import unittest
from calcore import cal
from calcore.cal import Occurrence
from datetime import datetime, timedelta

january = (datetime(2005, 1, 1, 0, 0),
           datetime(2005, 2, 1, 0, 0))

class SegmentingTestCase(unittest.TestCase):
    def setUp(self):
        self._m = cal.StorageManager()
        self._m.setStorage(cal.MemoryStorage('storage'))
        self._s = cal.SimpleAttendeeSource(self._m)
        self._calendar = cal.Calendar(self._m, self._s)
        martijn = self._s.createIndividual('martijn', 'Martijn')
        self._calendar.addAttendee(martijn)
        self._individual = martijn

    def test_segmented(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=14), 'payload')]
        occs = cal.segmentOccurrences(january, occs)
        self.assertEquals(2, len(occs))
        occs.sort(lambda x, y: cmp((x.dtstart, x.duration),
                                   (y.dtstart, y.duration)))
        self.assertEquals(
            datetime(2005, 1, 2, 17, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=7),
            occs[0].duration)
        self.assertEquals(
            'payload',
            occs[0].original)
        self.assertEquals(
            datetime(2005, 1, 3, 0, 0),
            occs[1].dtstart)
        self.assertEquals(
            timedelta(hours=7),
            occs[1].duration)
        self.assertEquals(
            'payload',
            occs[1].original)
        
    def test_segmented_three_days(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=34), 'payload')]
        occs = cal.segmentOccurrences(january, occs)
        self.assertEquals(3, len(occs))
        occs.sort(lambda x, y: cmp((x.dtstart, x.duration),
                                   (y.dtstart, y.duration)))
        self.assertEquals(
            datetime(2005, 1, 2, 17, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=7),
            occs[0].duration)
        self.assertEquals(
            datetime(2005, 1, 3, 0, 0),
            occs[1].dtstart)
        self.assertEquals(
            timedelta(days=1),
            occs[1].duration)
        self.assertEquals(
            datetime(2005, 1, 4, 0, 0),
            occs[2].dtstart)
        self.assertEquals(
            timedelta(hours=3),
            occs[2].duration)

    def test_segmented_null_case(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=1), 'payload')]
        occs = cal.segmentOccurrences(january, occs)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 1, 2, 17, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=1),
            occs[0].duration)

    def test_segmented_multiple_occs(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=34), 'payload'),
                Occurrence(datetime(2005, 1, 3, 14, 0),
                           timedelta(hours=24), 'payload')]
        occs = cal.segmentOccurrences(january, occs)
        self.assertEquals(5, len(occs))
        occs.sort(lambda x, y: cmp((x.dtstart, x.duration),
                                   (y.dtstart, y.duration)))
        self.assertEquals(
            datetime(2005, 1, 2, 17, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=7),
            occs[0].duration)
        self.assertEquals(
            datetime(2005, 1, 3, 0, 0),
            occs[1].dtstart)
        self.assertEquals(
            timedelta(hours=24),
            occs[1].duration)
        self.assertEquals(
            datetime(2005, 1, 3, 14, 0),
            occs[2].dtstart)
        self.assertEquals(
            timedelta(hours=10),
            occs[2].duration)
        self.assertEquals(
            datetime(2005, 1, 4, 0, 0),
            occs[3].dtstart)
        self.assertEquals(
            timedelta(hours=3),
            occs[3].duration)
        self.assertEquals(
            datetime(2005, 1, 4, 0, 0),
            occs[4].dtstart)
        self.assertEquals(
            timedelta(hours=14),
            occs[4].duration)

    def test_segment_start_period(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=34), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 1, 2, 19, 0),
             datetime(2005, 2, 1, 0, 0)),
            occs)
        self.assertEquals(3, len(occs))
        occs.sort(lambda x, y: cmp((x.dtstart, x.duration),
                                   (y.dtstart, y.duration)))
        self.assertEquals(
            datetime(2005, 1, 2, 19, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=5),
            occs[0].duration)
        self.assertEquals(
            datetime(2005, 1, 3, 0, 0),
            occs[1].dtstart)
        self.assertEquals(
            timedelta(hours=24),
            occs[1].duration)
        self.assertEquals(
            datetime(2005, 1, 4, 0, 0),
            occs[2].dtstart)
        self.assertEquals(
            timedelta(hours=3),
            occs[2].duration)
        
    def test_segment_end_period(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=34), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 1, 1, 0, 0),
             datetime(2005, 1, 3, 17, 0)),
            occs)
        self.assertEquals(2, len(occs))
        occs.sort(lambda x, y: cmp((x.dtstart, x.duration),
                                   (y.dtstart, y.duration)))
        self.assertEquals(
            datetime(2005, 1, 2, 17, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=7),
            occs[0].duration)
        self.assertEquals(
            datetime(2005, 1, 3, 0, 0),
            occs[1].dtstart)
        self.assertEquals(
            timedelta(hours=17),
            occs[1].duration)

    def test_segment_overflowing(self):
        occs = [Occurrence(datetime(2005, 1, 2, 17, 0),
                           timedelta(hours=3), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 1, 2, 18, 0),
             datetime(2005, 1, 2, 19, 0)),
            occs)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 1, 2, 18, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=1),
            occs[0].duration)

    def test_before_sameday(self):
        occs = [Occurrence(datetime(2005, 1, 2, 10, 0),
                           timedelta(hours=3), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 1, 2, 17, 0),
             datetime(2005, 1, 2, 20, 0)),
            occs)
        self.assertEquals(0, len(occs))

    def test_after_sameday(self):
        occs = [Occurrence(datetime(2005, 1, 2, 18, 0),
                           timedelta(hours=14), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 1, 1, 17, 0),
             datetime(2005, 1, 2, 17, 0)),
            occs)
        self.assertEquals(0, len(occs))

    def test_starts_in_day(self):
        occs = [Occurrence(datetime(2005, 4, 13, 14, 0),
                           timedelta(hours=23), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 4, 13),
             datetime(2005, 4, 14)),
            occs)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 4, 13, 14, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=10),
            occs[0].duration)

    def test_ends_in_day(self):
        occs = [Occurrence(datetime(2005, 4, 13, 14, 0),
                           timedelta(hours=23), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 4, 14),
             datetime(2005, 4, 15)),
            occs)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 4, 14, 0, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=13),
            occs[0].duration)

    def test_smaller_period_same_day(self):
        occs = [Occurrence(datetime(2005, 4, 13, 14, 0),
                           timedelta(hours=5), 'payload')]
        occs = cal.segmentOccurrences(
            (datetime(2005, 4, 13, 15),
             datetime(2005, 4, 13, 16)),
            occs)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 4, 13, 15),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=1),
            occs[0].duration)
        
    def test_occurrences_in_day(self):
        self._individual.createEvent(
            dtstart=datetime(2005, 4, 13, 14, 00),
            duration=timedelta(hours=23),
            status='TENTATIVE',
            title="Long meeting")
        day = datetime(2005, 4, 13)
        occs = self._calendar.getOccurrencesInDay(day)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 4, 13, 14, 00),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=10),
            occs[0].duration)
        day = datetime(2005, 4, 14)
        occs = self._calendar.getOccurrencesInDay(day)
        self.assertEquals(1, len(occs))
        self.assertEquals(
            datetime(2005, 4, 14, 0, 0),
            occs[0].dtstart)
        self.assertEquals(
            timedelta(hours=13),
            occs[0].duration)
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(SegmentingTestCase)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
