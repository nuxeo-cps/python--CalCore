# this is a package

if __name__ == '__main__':
    import unittest
    import test_cal, test_isoweek, test_util
    def test_suite():
        suite = test_cal.test_suite()
        suite.addTests([test_isoweek.test_suite()])
        suite.addTests([test_util.test_suite()])
        return suite
        
    unittest.main(defaultTest='test_suite')
