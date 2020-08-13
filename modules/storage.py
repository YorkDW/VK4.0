import logging, json

def dump(obj):
    with open("temp.json", "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii = False, indent = 2)
    print("dumped")

log = logging.getLogger("test")
talker = {
    "enabled" : False,
    "console" : 0,
    "user" : 0,
    "target" : 0
}
vault = {}
config = {}

def set_config(con):
    config = con.copy()

def get_config():
    return config

 