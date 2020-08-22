import aiosqlite, sqlite3, json, logging
from modules.basemaster import *
from base import SQLCreate




if False:
    wand.executescript(' '.join(SQLCreate.create))
    wand.executescript(' '.join(SQLCreate.filling_1))
    YConnection.commit()
    YConnection.close()
    raise SystemExit


def check_s_and_l(status_and_log):
    status, log = status_and_log
    if not status:
        print(log)
        return False
    return True

async def backup_vault_upload(backup_vault):
    for chat_id, data in backup_vault['chats'].items():
        chat_id = int(chat_id)
        await add_chat(chat_id, data['name'])
        if data['gate']:
            await add_gate(chat_id, data['gate'])
            
        for num, user_id in enumerate(data['mute']):
            await add_mute(chat_id, user_id, data['mute_time'][num])
    
    for user_id, banlist in backup_vault['banlist'].items():
        user_id = int(user_id)
        for chat_id in banlist:
            if chat_id == 0:
                await add_perm_ban(user_id)
            else:
                await add_ban(user_id, chat_id)

    for admin_id, data in backup_vault['admins'].items():
        admin_id = int(admin_id)
        await add_admin(admin_id, data['level'], data['name'])
        for chat_id in data['chats']:
            if chat_id == 0:
                continue
            await add_admin_to_chat(chat_id, admin_id)
        for num, user_id in enumerate(data['targets']['users']):
            await add_target(admin_id, user_id, data['targets']['times'][num])

    for user_id, data in backup_vault['enters'].items():
        user_id = int(user_id)
        for num, chat_id in enumerate(data['chats']):
            await add_enter(chat_id, user_id, data['times'][num])

    for group_name, chat_list in backup_vault['groups'].items():
        await add_group(group_name)
        for chat_id in chat_list:
            await add_chat_to_group(chat_id, group_name)
    

async def start():
    basefile = 'VK4.0/base/database_1-4-temp.db'
    backup_vault_file = 'VK4.0/base/backup_vault.json'
    st.basefile = basefile
    st.logger = logging.getLogger('test')
    with open(basefile, 'w') as file:
        file.write('')
    YConnection = sqlite3.connect(basefile)
    wand = YConnection.cursor()
    wand.execute("PRAGMA foreign_keys=on;")
    wand.executescript(' '.join(SQLCreate.create))
    YConnection.close()
    with open(backup_vault_file, 'r') as file:
        vault = json.load(file)
    await backup_vault_upload(vault)
    print('Done')


