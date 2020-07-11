import logging, json

def dump(obj):
    with open("temp.json", "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii = False, indent = 2)
    print("dumped")

my_id = 0 # под вопросом, возможно, уже есть в боте
log = logging.getLogger("test")
talker = {
    "enabled" : False,
    "console" : 0,
    "user" : 0,
    "target" : 0
}
vault = {}
