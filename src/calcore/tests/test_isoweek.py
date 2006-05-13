import unittest

from calcore import isoweek
from datetime import datetime, timedelta

class IsoWeekTestCase(unittest.TestCase):
    def test_weeksInYear(self):
        self.assertEquals(53, isoweek.getWeeksInYear(2004))
        for year in range(2005, 2009):
            self.assertEquals(52, isoweek.getWeeksInYear(year))
        self.assertEquals(53, isoweek.getWeeksInYear(2009))
        
    def test_weeknr2datetime(self):
        self.assertEquals(datetime(2005, 2, 7),
                          isoweek.weeknr2datetime(2005, 6, 1))
        dt = datetime(2005, 2, 7)
        for weekday in range(1, 7):
            self.assertEquals(dt, isoweek.weeknr2datetime(2005, 6, weekday))
            dt = dt + timedelta(1)
    
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(IsoWeekTestCase)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')