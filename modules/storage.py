import logging, json

def dump(obj):
    with open("temp.json", "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii = False, indent = 2)
    print("dumped")

async def execue(api, data_list):
    result = []
    ex_count = 2
    for i in range(0,len(data_list), ex_count):
        requests = ','.join(
            [f"API.{method}({str(data)})" for method, data in data_list[i:i+ex_count]]
            )
        code = f"return [{requests}];"
        result += (await api.execute(code=code)).response

    return result

talker = {
    "console" : 0,
    "user" : 0,
    "target" : 0
}
vault = {}
config = {}
start_time = 0
asyncio_loop = None



 