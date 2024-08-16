'''
Testing the elevator-related stuff
'''
import unittest

from .elevator import Elevator  # [relative-beyond-top-level]


class TestElevator(unittest.TestCase):
    '''
    Verify Elevator functionality
    '''

    def setUp(self):
        self.el = Elevator(5, 0)
        return

    def tearDown(self):
        self.el = None
        return

    def test_all(self):
        '''
        Test Elevator functionality
        '''
        print(self.el)
        return



if __name__ == '__main__':
    unittest.main()
