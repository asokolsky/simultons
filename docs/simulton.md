# Simulton

Simulton is:

* a process
* a FastAPI REST service(s)
* a zmq subscriber to Simulation publisher

Responsible for creating simulated objects of one class, e.g. clock or elevator
class.  Such objects then can be interacted with using REST API.
The latter is class specific.

## Mandatory REST API /api/v1/simulton

* GET -> [SimultonResponse](../simultons/schemas.py)
* PUT, [SimultonRequest](../simultons/schemas.py) -> [SimultonResponse](../simultons/schemas.py)


## Custom REST API(s) e.g. /api/v1/clocks

* GET -> [ClockResponse](../simultons/schemas.py)
* POST [NewClockParams](../simultons/schemas.py) -> [ClockResponse](../simultons/schemas.py)
* GET /api/v1/clocks/{id} -> [ClockResponse](../simultons/schemas.py)
* DELETE /api/v1/clocks/{id} -> OK
