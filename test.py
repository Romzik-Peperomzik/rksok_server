import base64
from random import randint
from enum import Enum



# Иваннн Хмурый Дацузбе Акпку
raw_response = 'НОРМАЛДЫКС РКСОК/1.0\r\n89012345678' 
foo = 'ЗОПИШИ SDferwwe erGrgrg РКСОК/1.0\r\n89012345678 — мобильный\r\n02 — рабочий\r\n'
name = foo.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
# print(name)
encode_name = base64.b64encode(name.encode("UTF-8")).decode()
print(encode_name)
with open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
    f.write(foo.split('\r\n', 1)[1])

"""
class ResponseState(Enum):
    ALLOW = 'МОЖНА РКСОК/1.0'
    NOTALLOW = 'НИЛЬЗЯ РКСОК/1.0' 


MODE_TO_VERB = {
    1: ResponseState.ALLOW,
    2: ResponseState.NOTALLOW
}
"""

allow_or_not_list = ['МОЖНА РКСОК/1.0', 'НИЛЬЗЯ РКСОК/1.0']

print(allow_or_not_list[randint(0, 1)].encode("UTF-8"))

print(base64.b64decode('U0RmZXJ3d2UgZXJHcmdyZw=='))