'''
Testing the simulation/simulton stuff
'''
import unittest

from simulation import Simulation   # [relative-beyond-top-level]
from simulton import Simulton       # [relative-beyond-top-level]


class TestSimulation(unittest.TestCase):
    '''
    Verify Simulation launcher functionality
    '''

    def test_lifecycle(self) -> None:

        #
        # follow http://pymotw.com/2/multiprocessing/communication.html
        #

        world = Simulation()
        print(world)
        world.add(Simulton, 'foo')
        world.add(Simulton, 'bar')
        print(world)

        #world.initialize()
        #world.run(5)
        #world.pause()
        #world.run(10)
        #world.shutdown()
        return


if __name__ == '__main__':
    unittest.main()
