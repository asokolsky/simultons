# Simulton

Simulton is:

* a process
* a zmq subscriber to Simulation publisher
* a FastAPI REST service(s)

responsible for creating simulated objects of one class, e.g. clock or elevator
class.  Such objects then can be interacted with using REST API.
The latter is class specific.

## Mandatory REST API

`/api/v1/simulton`

* shutdown

## Custom REST API(s)

e.g. `/api/v1/clock`
