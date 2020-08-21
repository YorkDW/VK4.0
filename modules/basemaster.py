import time, logging, aiosqlite, asyncio
import modules.storage as stor

class st:
    basefile = None
    logger = None



# logging.getLogger('aiosqlite').setLevel(logging.CRITICAL)
# logger = logging.getLogger(__name__.split('.')[-1])
# logger.setLevel(1)

def logging_decorator(func):
    async def log_after(*args, **kwargs):
        status, respond = await func(*args, **kwargs)
        intro = 'Done:' if status else 'FAIL:'
        level = 11 if status else 13
        st.logger.log(level, f" {intro} {func.__name__}{args}{kwargs} - {respond}")
        return (status, respond)
    return log_after



async def get_conn_and_wand(basefile):
    Zconnection = await aiosqlite.connect(basefile)
    wand = await Zconnection.cursor()
    await wand.execute("PRAGMA foreign_keys=on;")
    return (Zconnection, wand)

def conn_and_wand_decorator(func):
    async def cover(*args, **kwargs):
        Zconnection, wand = await get_conn_and_wand(st.basefile)

        args = (Zconnection, wand) + args
        res = await func(*args, **kwargs)
        await Zconnection.close()
        return res
    return cover

async def initiate(basefile, base_logger):
    st.basefile = basefile
    st.logger = base_logger
    await update_vault_all()

@conn_and_wand_decorator
async def add_or_update_object(Zconnection, wand, name, sql, params:list, add_or_updat):
    try:
        await wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        unique_field_fail = error.args[0].split('.')[-1]
        return (False, f"{unique_field_fail} already added")
    else:
        await Zconnection.commit()
    return (True, f"{name} {add_or_updat}ed")

@logging_decorator
async def add_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_updat":"add",
        "sql":"INSERT INTO Chats ('VK_ID', 'Name') VALUES(?, ?)",
        "params":[chat_id, name]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def add_group(group_name):
    kwargs = {
        "name":'Group',
        "add_or_updat":"add",
        "sql":"INSERT INTO Groups ('Name') VALUES(?)",
        "params":[group_name]
    }
    return await add_or_update_object(**kwargs)
    
@logging_decorator
async def add_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_updat":"add",
        "sql":"INSERT INTO Admins ('VK_ID', 'Level', 'Name') VALUES(?, ?, ?)",
        "params":[admin_id, level, name]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def update_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_updat":"updat",
        "sql":"UPDATE Chats SET Name=? WHERE VK_ID=?",
        "params":[name, chat_id]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def update_group(old_group_name, new_group_name):
    kwargs = {
        "name":'Group',
        "add_or_updat":"updat",
        "sql":"UPDATE Groups SET Name=? WHERE Name=?",
        "params":[new_group_name, old_group_name]
    }
    return await add_or_update_object(**kwargs)
    
@logging_decorator
async def update_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_updat":"updat",
        "sql":"UPDATE Admins SET Level=?, Name=? WHERE VK_ID=?",
        "params":[level, name, admin_id]
    }
    return await add_or_update_object(**kwargs)

@conn_and_wand_decorator
async def del_object(Zconnection, wand, name, param, get_base_func, connected_tables):
    base_id = await get_base_func(param)
    if not base_id:
        return (False, f"{name} does not exists")
    sql = [f"DELETE FROM {table} WHERE {name}_ID={base_id};" for table in connected_tables]
    await wand.executescript(' '.join(sql))
    await Zconnection.commit()
    return (True, f"{name} probably deleted")

@logging_decorator
async def del_group(group_name):
    kwargs = {
        "name":'Group',
        "param":group_name,
        'get_base_func':get_base_group_id,
        'connected_tables':['Group_fill','Groups']
    }
    return await del_object(**kwargs)

@logging_decorator
async def del_chat(chat_id):
    kwargs = {
        "name":'Chat',
        "param":chat_id,
        'get_base_func':get_base_chat_id,
        'connected_tables':['Group_fill','Admin_fill','Bans_fill','Last_enters','Chat_mutes','Chat_gates','Chats']
    }
    return await del_object(**kwargs)

@logging_decorator
async def del_admin(admin_id):
    kwargs = {
        "name":'Admin',
        "param":admin_id,
        'get_base_func':get_base_admin_id,
        'connected_tables':['Admin_fill','Last_targets','Admins']
    }
    return await del_object(**kwargs)

@conn_and_wand_decorator
async def add_or_del_pair_connection(Zconnection, wand, chat_id,
                                second_id_or_name, get_base_func,
                                second_param_name, sql, add_or_delet):
    base_chat_id = await get_base_chat_id(chat_id)
    base_second_id = await get_base_func(second_id_or_name)
    if not base_chat_id:
        return (False, f"Wrong chat")
    if not base_second_id:
        return (False, f"Wrong {second_param_name}")
    try:
        await wand.execute(sql, [base_chat_id, base_second_id])
    except:
        if add_or_delet=="add":
            return (False, f"{second_param_name} already added")
        else:
            return (False, f"No such connection")
    await Zconnection.commit()
    return (True, f"{second_param_name} {add_or_delet}ed")

@logging_decorator
async def add_admin_to_chat(chat_id, admin_id):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":admin_id,
        "get_base_func":get_base_admin_id,
        "second_param_name":"Admin",
        "add_or_delet":"add",
        "sql":"INSERT INTO Admin_fill ('Chat_ID', 'Admin_ID') VALUES(?, ?)"
    }
    return await add_or_del_pair_connection(**kwargs)

@logging_decorator
async def add_chat_to_group(chat_id, group_name):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":group_name,
        "get_base_func":get_base_group_id,
        "second_param_name":"Group",
        "add_or_delet":"add",
        "sql":"INSERT INTO Group_fill ('Chat_ID', 'Group_ID') VALUES(?, ?)"
    }
    return await add_or_del_pair_connection(**kwargs)

@logging_decorator
async def del_chat_from_group(chat_id, group_name):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":group_name,
        "get_base_func":get_base_group_id,
        "second_param_name":"Group",
        "add_or_delet":"delet",
        "sql":"DELETE FROM Group_fill WHERE Chat_ID=? AND Group_ID=?"
    }
    return await add_or_del_pair_connection(**kwargs)

@logging_decorator
async def del_admin_from_chat(chat_id, admin_id):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":admin_id,
        "get_base_func":get_base_admin_id,
        "second_param_name":"Admin",
        "add_or_delet":"delet",
        "sql":"DELETE FROM Admin_fill WHERE Chat_ID=? AND Admin_ID=?"
    }
    return await add_or_del_pair_connection(**kwargs)
    
@conn_and_wand_decorator
async def add_or_del_status(Zconnection, wand, name,
                        base_chat_or_admin_id, params:list,
                        sql, sql_update, add_or_delet):

    if not base_chat_or_admin_id:
        return (False, "Wrong chat or something else")
    params.insert(0, base_chat_or_admin_id)
    try:
        await wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        params.pop(0)
        params.append(base_chat_or_admin_id) # просто гениально
        await wand.execute(sql_update, params)
    await Zconnection.commit()
    negative = '' if add_or_delet=='add' else 'un'
    return (True, f"Chat {negative}{name}ed")

@logging_decorator
async def add_mute(chat_id, user_id, time_):
    kwargs = {
        "name":"mut",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Chat_mutes ('Chat_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Chat_mutes SET Time=? WHERE User_ID = ? AND Chat_ID=?"
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def add_gate(chat_id, time_):
    kwargs = {
        "name":"lock",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[time_],
        "add_or_delet":"add",
        "sql":"INSERT INTO Chat_gates ('Chat_ID', 'time') VALUES(?, ?)",
        "sql_update":"UPDATE Chat_gates SET Time=? WHERE Chat_ID=?"
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def add_enter(chat_id, user_id, time_):
    kwargs = {
        "name":"enter",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Last_enters ('Chat_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Last_enters SET Time=? WHERE User_ID = ? AND Chat_ID=?"
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def add_target(admin_id, user_id, time_):
    kwargs = {
        "name":"target",
        "base_chat_or_admin_id":await get_base_admin_id(admin_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Last_targets ('Admin_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Last_targets SET Time=? WHERE User_ID=? AND Admin_ID=?"
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def del_mute(chat_id, user_id):
    kwargs = {
        "name":"mut",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Chat_mutes WHERE Chat_ID=? AND User_ID=?",
        "sql_update":None
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def del_gate(chat_id):
    kwargs = {
        "name":"lock",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Chat_gates WHERE Chat_ID=?",
        "sql_update":None
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def del_enter(chat_id, user_id):
    kwargs = {
        "name":"enter",
        "base_chat_or_admin_id":await get_base_chat_id(chat_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Last_enters WHERE Chat_ID=? AND User_ID=?",
        "sql_update":None
    }
    return await add_or_del_status(**kwargs)

@logging_decorator
async def del_target(admin_id, user_id):
    kwargs = {
        "name":"target",
        "base_chat_or_admin_id":await get_base_admin_id(admin_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Last_targets WHERE Admin_ID=? AND User_ID=?",
        "sql_update":None
    }
    return await add_or_del_status(**kwargs)

@conn_and_wand_decorator
async def add_ban(Zconnection, wand, user_id, chat_id):
    sql = "INSERT INTO 'Bans' ('VK_ID', 'Everywhere') VALUES(?, ?)"
    try:
        await wand.execute(sql, [user_id, 0])
    except:
        pass

    sql = "INSERT INTO 'Bans_fill' ('Chat_ID', 'Ban_ID') VALUES((SELECT Chat_ID FROM Chats WHERE VK_ID=?), (SELECT Ban_ID FROM Bans WHERE VK_ID=?))"
    try:
        await wand.execute(sql, [chat_id, user_id])
    except:
        return (False, f"User {user_id} already banned in {chat_id}")
    await Zconnection.commit()
    return (True, f"User {user_id} banned in {chat_id}")

@conn_and_wand_decorator
async def del_ban(Zconnection, wand, user_id, chat_id):
    if user_id not in stor.vault['banlist'].keys() or chat_id not in stor.vault['banlist'][user_id]:
        return (False, f"User {user_id} is not banned in {chat_id}")
    
    sql = '''DELETE FROM Bans_fill WHERE 
    Chat_ID=(SELECT Chat_ID FROM Chats WHERE VK_ID=?) AND 
    Ban_ID=(SELECT Ban_ID FROM Bans WHERE VK_ID=?)'''
    await wand.execute(sql,[chat_id, user_id])

    if 0 not in stor.vault['banlist'][user_id] and len(stor.vault['banlist'][user_id])==1:
        await wand.execute('''DELETE FROM Bans WHERE VK_ID=?''',[user_id])
    await Zconnection.commit()
    return (True, f"User {user_id} is forgiven in {chat_id}")

@conn_and_wand_decorator
async def add_perm_ban(Zconnection, wand, user_id):
    sql = '''INSERT INTO Bans(VK_ID, Everywhere) VALUES (?,1)'''
    sql_update = '''UPDATE Bans SET Everywhere=1 WHERE VK_ID=?'''''
    try:
        await wand.execute(sql,[user_id])
    except:
        await wand.execute(sql_update,[user_id])
    await Zconnection.commit()
    return (True, f"User {user_id} is banned everywhere")

@conn_and_wand_decorator
async def del_perm_ban(Zconnection, wand, user_id):
    user_s_banlist = stor.vault['banlist'].get(user_id, [])
    if 0 not in user_s_banlist:
        return (False, f"User {user_id} was not fully banned")
    if len(user_s_banlist)>1:
        await wand.execute("UPDATE Bans SET Everywhere=0 WHERE VK_ID=?",[user_id])
    else:
        await wand.execute("DELETE FROM Bans WHERE VK_ID=?",[user_id])
    await Zconnection.commit()
    return (True, f"User {user_id} is not fully banned now")

# переделать это всё, вообще всё, под нормальные методы работы с базой, а не этот колхоз

@conn_and_wand_decorator
async def update_vault_banlist(Zconnection, wand):
    await wand.execute('''SELECT VK_ID, Everywhere FROM Bans''')
    bans = await wand.fetchall()
    
    await wand.execute('''SELECT c.VK_ID, b.VK_ID
    FROM Chats c, Bans b, Bans_fill bf
    WHERE b.Ban_ID=bf.Ban_ID AND bf.Chat_ID=c.Chat_ID''')
    banlist = await wand.fetchall()

    stor.vault['banlist'] = {}

    for user_id, everywhere in bans:
        stor.vault['banlist'][user_id] = [0] if everywhere else []

    for chat_id, user_id in banlist:
        stor.vault['banlist'][user_id].append(chat_id)
            
        
@conn_and_wand_decorator
async def update_vault_chats(Zconnection, wand):
    await wand.execute('''SELECT VK_ID, name FROM Chats''')
    chats = await wand.fetchall()

    await wand.execute('''DELETE FROM Chat_mutes WHERE time<?''',[int(time.time())])
    await wand.execute('''SELECT c.VK_ID, m.User_ID, m.time
    FROM Chats c, Chat_mutes m
    WHERE m.Chat_ID=c.Chat_ID''')
    mutes = await wand.fetchall()

    await wand.execute('''DELETE FROM Chat_gates WHERE time<?''',[int(time.time())])
    await wand.execute('''SELECT c.VK_ID, g.time
    FROM Chats c, Chat_gates g
    WHERE g.Chat_ID=c.Chat_ID''')
    gates = await wand.fetchall()

    stor.vault['chats'] = {}

    for chat_id, name in chats:
         stor.vault['chats'][chat_id] = {
             'name':name,
             'gate':0,
             'mute':[],
             'mute_time':[]
         }

    for chat_id, user_id, time_ in mutes:
        stor.vault['chats'][chat_id]['mute'].append(user_id)
        stor.vault['chats'][chat_id]['mute_time'].append(time_)
    stor.vault['chats'][chat_id]['mute'] = tuple(stor.vault['chats'][chat_id]['mute'])
    stor.vault['chats'][chat_id]['mute_time'] = tuple(stor.vault['chats'][chat_id]['mute_time'])

    for chat_id, time_ in gates:
        stor.vault['chats'][chat_id]['gate'] = time_

    await Zconnection.commit()
    
@conn_and_wand_decorator
async def update_vault_enters(Zconnection, wand):
    await wand.execute('''DELETE FROM Last_enters WHERE time<?''',[int(time.time())])
    await wand.execute('''SELECT c.VK_ID, l.User_ID, l.time
    FROM Chats c, Last_enters l
    WHERE l.Chat_ID=c.Chat_ID''')
    enters = await wand.fetchall()

    stor.vault['enters'] = {}

    for chat_id, user_id, time_ in enters:
        if user_id not in stor.vault['enters'].keys():
            stor.vault['enters'][user_id] = [(chat_id, time_)]
        else:
            stor.vault['enters'][user_id].append((chat_id, time_))

    await Zconnection.commit()

@conn_and_wand_decorator
async def update_vault_admins(Zconnection, wand):
   
    await wand.execute('''SELECT VK_ID, name, level FROM Admins''')
    admins = await wand.fetchall()
    
    await wand.execute('''SELECT a.VK_ID, c.VK_ID
    FROM Admins a, Chats c, Admin_fill af
    WHERE af.Chat_ID=c.Chat_ID AND af.Admin_ID=a.Admin_ID''')
    admin_fill = await wand.fetchall()
    

    await wand.execute('''DELETE FROM Last_targets WHERE time<?''',[int(time.time())])
    await wand.execute('''SELECT a.VK_ID, l.User_ID, l.time
    FROM Admins a, Last_targets l
    WHERE l.Admin_ID=a.Admin_ID''')
    targets = await wand.fetchall()

    stor.vault['admins'] = {}

    for admin_id, name, level in admins:
        stor.vault['admins'][admin_id] = {
            'name':name,
            'level':level,
            'chats': [0] if level>=3 else [],
            'targets':{'users':[], 'times':[]}
        }

    for admin_id, chat_id in admin_fill:
        stor.vault['admins'][admin_id]['chats'].append(chat_id)

    for admin_id, user_id, time_ in targets:
        stor.vault['admins'][admin_id]['targets']['users'].append(user_id)
        stor.vault['admins'][admin_id]['targets']['times'].append(time_)

    await Zconnection.commit()
    


@conn_and_wand_decorator
async def update_vault_groups(z, wand):
    await wand.execute('''SELECT g.name, c.VK_ID
    FROM Groups g, Chats c, Group_fill gf
    WHERE gf.Chat_ID=c.Chat_ID AND gf.Group_ID=g.Group_ID''')
    groups = await wand.fetchall()
    stor.vault['groups'] = {}
    for group_name, chat_id in groups:
        if group_name not in stor.vault['groups'].keys():
            stor.vault['groups'][group_name] = [chat_id]
        else:
            stor.vault['groups'][group_name].append(chat_id)


async def update_vault_all():
    await update_vault_chats()
    await update_vault_banlist()
    await update_vault_admins()
    await update_vault_enters()
    await update_vault_groups()


@conn_and_wand_decorator
async def get_base_chat_id(z,wand,chatId):
    await wand.execute("SELECT Chat_ID FROM Chats WHERE VK_ID=?", [chatId])
    temp = await wand.fetchall()
    return temp[0][0] if temp != [] else False

@conn_and_wand_decorator
async def get_base_group_id(z, wand, groupName):
    await wand.execute("SELECT Group_ID FROM Groups WHERE Name=?", [groupName])
    temp = await wand.fetchall()
    return temp[0][0] if temp != [] else False

@conn_and_wand_decorator
async def get_base_admin_id(z, wand, adminId):
    await wand.execute("SELECT Admin_ID FROM Admins WHERE VK_ID=?", [adminId])
    temp = await wand.fetchall()
    return temp[0][0] if temp != [] else False


def getList(fetch):
    return [s[0] for s in fetch] # [(x,), (y,)]

def get_admin_level(user_id):
    admin = stor.vault['admins'].get(user_id, False)
    return admin['level'] if admin else 0

def is_chat_admin(user_id, peer_id):
    if user_id not in stor.vault['admins'].keys():
        return False
    if 0 in  stor.vault['admins'][user_id]['chats'] or chat_id in stor.vault['admins'][user_id]['chats']:
        return True
    return False

def is_muted(user_id, peer_id):
    chat = stor.vault['chats'].get(peer_id, False)
    if not chat:
        return False

    if user_id in chat['mute']:
        if chat['mute_time'][chat['mute'].index(user_id)] > time.time():
            return True

    if 0 in chat['mute']:
        if chat['mute_time'][chat['mute'].index(0)] > time.time():
            return True

    return False

def get_chats_by_admin(user_id):
    admin = stor.vault['admins'].get(user_id, False)
    return admin['chats'] if admin else []

def check_gate(chat_id):
    if chat_id in stor.vault['chats']:
        return True if stor.vault['chats']>time.time() else False

def verify_chat(chat_id):
    return chat_id in stor.vault['chats'].keys()
        

async def handle_targets(admin_id, targets, time_):
    for_delete = []
    cur_adm_targets = stor.vault['admins'][admin_id]['targets']
    for num, expire_time in enumerate(cur_adm_targets['times']):
        if expire_time < time.time():
            for_delete.append(num)
    
    for num in for_delete:
        cur_adm_targets['times'].pop(num)
        cur_adm_targets['users'].pop(num)
    stor.vault['admins'][admin_id]['targets'] = cur_adm_targets

    aviable_slots = stor.config['MAXTARGETS'] - len(cur_adm_targets['users'])
    result_targets = []

    for target in targets:
        if target in cur_adm_targets['users']:
            await add_target(admin_id, target, time_)
        if aviable_slots:
            aviable_slots -= 1
            await add_target(admin_id, target, time_)

    await update_vault_admins()
    return list(set(targets).intersection(set(stor.vault['admins'][admin_id]['targets']['users'])))


async def handle_enter(user_id, chat_id, time_):
    await add_enter(chat_id, user_id, time_)
    await update_vault_enters()
    enters = stor.vault['enters'][user_id]
    return list(map(lambda pair:pair[0], enters))

def is_banned(user_id, chat_id):
    if user_id not in stor.vault['banlist'].keys():
        return False
    if 0 in stor.vault['banlist'][user_id] or chat_id in stor.vault['banlist'][user_id]:
        return True



async def test1(num=0):
    Zconnection = await aiosqlite.connect(st.b)
    wand = await Zconnection.cursor()
    await wand.execute("PRAGMA foreign_keys=on;")
    sql = '''INSERT INTO Bans(VK_ID, Everywhere) VALUES (?,?)'''
    await wand.execute(sql, [1324, 0])
    await asyncio.sleep(2)
    sql = '''SELECT * FROM Bans'''
    await wand.execute(sql)
    print(1,await wand.fetchall())
    await Zconnection.rollback()
    await wand.execute(sql)
    print(1,await wand.fetchall())
    return
    

async def test2(num=0):
    Zconnection = await aiosqlite.connect(st.b)
    wand = await Zconnection.cursor()
    await wand.execute("PRAGMA foreign_keys=on;")
    # sql = '''INSERT INTO Bans(VK_ID, Everywhere) VALUES (?,?)'''
    # await wand.execute(sql, [4321, 1])
    sql = '''SELECT * FROM Bans'''
    await wand.execute(sql)
    print(2,await wand.fetchall())
    await Zconnection.rollback()
    await wand.execute(sql)
    print(2,await wand.fetchall())
    return
    