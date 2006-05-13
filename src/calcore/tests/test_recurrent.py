import unittest
import doctest

from zope.interface import verify

from calcore import recurrent
from calcore import interfaces

def doctest_interfaces():
    """Test the interfaces of the recurrence objects.

    Basic Recurrence:
        >>> r = recurrent.BasicRecurrenceRule()
        >>> verify.verifyObject(interfaces.IBasicRecurrenceRule, r)
        True

    Daily Recurrence:
        >>> r = recurrent.DailyRecurrenceRule()
        >>> verify.verifyObject(interfaces.IDailyRecurrenceRule, r)
        True

    Weekly Recurrence:
        >>> r = recurrent.WeeklyRecurrenceRule()
        >>> verify.verifyObject(interfaces.IWeeklyRecurrenceRule, r)
        True

    Yearly Recurrence:
        >>> r = recurrent.YearlyRecurrenceRule()
        >>> verify.verifyObject(interfaces.IYearlyRecurrenceRule, r)
        True

    Monthly Recurrence:
        >>> r = recurrent.MonthlyRecurrenceRule()
        >>> verify.verifyObject(interfaces.IMonthlyRecurrenceRule, r)
        True

    No recurrence:
        >>> r = recurrent.NoRecurrenceRule()
        >>> verify.verifyObject(interfaces.INoRecurrenceRule, r)
        True
    """

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([doctest.DocTestSuite()])
    return suite
