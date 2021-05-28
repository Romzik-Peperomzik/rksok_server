import base64

# Иваннн Хмурый Дацузбе Акпку
raw_response = 'НОРМАЛДЫКС РКСОК/1.0\r\n89012345678' 
foo = 'ЗОПИШИ SDferwwe erGrgrg РКСОК/1.0\r\n89012345678 — мобильный\r\n02 — рабочий\r\n'
name = foo.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
# print(name)
encode_name = base64.b64encode(name.encode("UTF-8")).decode()
print(encode_name)
with open(f"{encode_name}", 'x', encoding='utf-8') as f:
    f.write(foo.split('\r\n', 1)[1])