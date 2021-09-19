from enum import Enum

class RequestVerb(Enum):
    """Verbs specified in RKSOK specs for requests."""

    GET = "ОТДОВАЙ "
    DELETE = "УДОЛИ "
    WRITE = "ЗОПИШИ "


class ResponsePhrase(Enum):
    OK = "НОРМАЛДЫКС РКСОК/1.0"
    N_FND = "НИНАШОЛ РКСОК/1.0"
    DNU = "НИПОНЯЛ РКСОК/1.0"    
    N_APPR = "НИЛЬЗЯ"

PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8"
VALIDATION_SERVER_URL = "vragi-vezde.to.digital"
VALIDATION_SERVER_PORT = 51624
