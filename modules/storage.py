import logging, json

def dump(obj):
    with open("temp.json", "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii = False, indent = 2)
    print("dumped")

def do(func):
    asyncio_loop.create_task(func)

async def execue(api, data_list):
    result = []
    ex_count = 25
    for i in range(0,len(data_list), ex_count):
        requests = ','.join(
            [f"API.{method}({str(data)})" for method, data in data_list[i:i+ex_count]]
            )
        code = f"return [{requests}];"
        result += (await api.execute(code=code)).response

    return result

talker = {
    'users': [],
    'consoles': [],
    'targets': []
}
vault = {}
config = {}
start_time = 0
asyncio_loop = None
time_day = 86400 # 60*60*24
user_api = None
enters = {}