import unittest

from calcore import util

class UtilTestCase(unittest.TestCase):

    def test_removeOverlapsExtend(self):
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 7), (6, 12)]))

    def test_removeOverlapsExtendEdge(self):
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 7), (7, 12)]))

    def test_removeOverlapsSub(self):
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 12), (10, 11)]))

    def test_removeOverlapsSubEdge(self):
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 12), (5, 12)]))
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 12), (5, 7)]))
        self.assertEquals(
            [(5, 12)],
            util.removeOverlaps([(5, 12), (7, 12)]))
        
    def test_removeOverlapsEmpty(self):
        self.assertEquals(
            [],
            util.removeOverlaps([]))
            
    def test_removeOverlapsComplicated(self):
        sequence = [(5, 10), (7, 10), (7, 12), (14, 18), (20, 23)]
        self.assertEquals(
            [(5, 12), (14, 18), (20, 23)],
            util.removeOverlaps(sequence))
        
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(UtilTestCase)])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')