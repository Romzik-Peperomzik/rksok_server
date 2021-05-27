from enum import Enum


class RequestVerb(Enum):
    """Verbs specified in RKSOK specs for requests"""
    GET = "ОТДОВАЙ"
    DELETE = "УДОЛИ"
    WRITE = "ЗОПИШИ"

MODE_TO_VERB = {
    1: RequestVerb.GET,
    2: RequestVerb.WRITE,
    3: RequestVerb.DELETE
}

verb = MODE_TO_VERB.get(1)
_verb = verb

print(type(verb))
print(verb)
print(RequestVerb.GET.value)

raw_response = 'НОРМАЛДЫКС РКСОК/1.0\r\n89012345678' 

response_payload = "".join(raw_response.split("\r\n")[1:])
print(response_payload)
