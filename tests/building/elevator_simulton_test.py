import unittest

from fastapi.testclient import TestClient

from simultons import setup_logging
from simultons.building import ElevatorResponse, NewElevatorParams
from simultons.building.elevator import app

elevators_uri = '/api/v1/elevators/'

log = setup_logging(__name__)


class TestElevatorSimultonWithTestClient(unittest.TestCase):
    """
    Verify ElevatorSimulton functionality using TestClient
    """

    def setUp(self) -> None:
        return

    def tearDown(self) -> None:
        return

    def test_all(self) -> None:
        """
        Test Elevator REST APIs functionality
        """
        # this will ensure that startup/shutdown events ARE generated
        with TestClient(app) as client:
            #
            # blank slate, no elevators created yet
            #
            response = client.get(elevators_uri)
            self.assertTrue(response.status_code, 200)
            self.assertEqual(response.json(), {})

            #
            # Create some elevators
            #
            floors = 10
            names = ['foo', 'bar', 'baz']
            for name in names:
                params = NewElevatorParams(name=name, floors=floors)
                log.info(f'posting: {params.model_dump()}')
                response = client.post(elevators_uri, json=params.model_dump())
                self.assertTrue(response.status_code, 201)
                jresp = response.json()
                self.assertEqual(jresp['name'], name)
            #
            # retrieve them all
            #
            response = client.get(elevators_uri)
            self.assertTrue(response.status_code, 200)
            jresp = response.json()
            #
            # retrieve them, one at a time
            #
            for id, el in jresp.items():
                response = client.get(f'{elevators_uri}{id}')
                expected = ElevatorResponse(id=id, name=el['name'], floors=floors)
                log.info(f'received: {response.json()}')
                log.info(f'expected: {expected.model_dump()}')
                self.assertEqual(response.json(), expected.model_dump())

        return
