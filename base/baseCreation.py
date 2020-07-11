import sqlite3, SQLCreate, json


def fill(adminIds, banList, wand, chats, groupNum):
    for chat in chats:
        wand.execute(SQLCreate.filling_2['chats'], [chat])
        curChatId = wand.lastrowid
        wand.execute(SQLCreate.filling_2['group_fill'], [curChatId, groupNum])
        for ban in banList:
            wand.execute(SQLCreate.filling_2['banlist'], [curChatId, ban])
        for adminNum in range(1, len(adminIds)+1):
            wand.execute(SQLCreate.filling_2['adm_fill'], [curChatId, adminNum])


YConnection = sqlite3.connect('database_1-4.db')
wand = YConnection.cursor()
wand.execute("PRAGMA foreign_keys=on;")

if True:
    wand.executescript(' '.join(SQLCreate.create))
    wand.executescript(' '.join(SQLCreate.filling_1))
    YConnection.commit()
    YConnection.close()
    raise SystemExit

with open("baseDataReserve.json", 'r') as file:
    temp = json.load(file)
create = ' '.join(SQLCreate.create)
wand.executescript(create)
for admin in temp['adminIds']:
    wand.execute(SQLCreate.filling_2['adm'], [admin, 4])
for group in temp['groups'].keys():
    wand.execute(SQLCreate.filling_2['groups'], [group])
    fill(
        temp['adminIds'], 
        temp['banList'], 
        wand, 
        temp['groups'][group], 
        wand.lastrowid
        )
print('created')
YConnection.commit()
YConnection.close()

