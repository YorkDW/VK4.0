import time, logging, aiosqlite

class st:
    Zconnection = None
    wand = None

# посоветоваться и, возможно, сделать всё синхронным

logging.getLogger('aiosqlite').setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__.split('.')[-1])

def logging_decorator(func):
    async def log_after(*args, **kwargs):
        status, respond = await func(*args, **kwargs)
        intro = 'Done:' if status else 'FAIL:'
        level = 11 if status else 13
        logger.log(level, f" {intro} {func.__name__}{args}{kwargs} - {respond}")
        return (status, respond)
    return log_after

async def initiate(basefile):
    st.Zconnection = await aiosqlite.connect(basefile)
    st.wand = await st.Zconnection.cursor()
    await st.wand.execute("PRAGMA foreign_keys=on;")


async def add_or_update_object(name, sql, params:list, add_or_update):
    try:
        await st.wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        unique_field_fail = error.args[0].split('.')[-1]
        return (False, f"{unique_field_fail} already added")
    else:
        await st.Zconnection.commit()
    return (True, f"{name} {add_or_update}ed")

@logging_decorator
async def add_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_update":"add",
        "sql":"INSERT INTO Chats ('VK_ID', 'Name') VALUES(?, ?)",
        "params":[chat_id, name]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def add_group(group_name):
    kwargs = {
        "name":'Group',
        "add_or_update":"add",
        "sql":"INSERT INTO Groups ('Name') VALUES(?)",
        "params":[group_name]
    }
    return await add_or_update_object(**kwargs)
    
@logging_decorator
async def add_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_update":"add",
        "sql":"INSERT INTO Admins ('VK_ID', 'Level', 'Name') VALUES(?, ?, ?)",
        "params":[admin_id, level, name]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def update_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_update":"update",
        "sql":"UPDATE Chats SET Name=? WHERE VK_ID=?",
        "params":[name, chat_id]
    }
    return await add_or_update_object(**kwargs)

@logging_decorator
async def update_group(old_group_name, new_group_name):
    kwargs = {
        "name":'Group',
        "add_or_update":"update",
        "sql":"UPDATE Groups SET Name=? WHERE Name=?",
        "params":[new_group_name, old_group_name]
    }
    return await add_or_update_object(**kwargs)
    
@logging_decorator
async def update_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_update":"update",
        "sql":"UPDATE Admins SET Level=?, Name=? WHERE VK_ID=?",
        "params":[level, name, admin_id]
    }
    return await add_or_update_object(**kwargs)

async def del_object(name, param, get_base_func, connected_tables):
    base_id = await get_base_func(param)
    if not base_id:
        return (False, f"{name} does not exists")
    sql = [f"DELETE FROM {table} WHERE {name}_ID={base_id};" for table in connected_tables]
    await st.wand.executescript(' '.join(sql))
    await st.Zconnection.commit()
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
        'connected_tables':['Group_fill','Admin_fill','Banlist','Last_enters','Chat_mutes','Chat_gates','Chats']
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

async def add_or_del_pair_connection(chat_id, second_id_or_name, get_base_func, second_param_name, sql, add_or_delet):
    base_chat_id = await get_base_chat_id(chat_id)
    base_second_id = await get_base_func(second_id_or_name)
    if not base_chat_id:
        return (False, f"Wrong chat")
    if not base_second_id:
        return (False, f"Wrong {second_param_name}")
    try:
        await st.wand.execute(sql, [base_chat_id, base_second_id])
    except:
        if add_or_delet=="add":
            return (False, f"{second_param_name} already added")
        else:
            return (False, f"No such connection")
    await st.Zconnection.commit()
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
    
async def add_or_det_status(name, base_chat_or_admin_id, params:list, sql, sql_update, add_or_delet):
    if not base_chat_or_admin_id:
        return (False, "Wrong chat or something else")
    params.insert(0, base_chat_or_admin_id)
    try:
        await st.wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        params.pop(0)
        params.append(base_chat_or_admin_id)
        await st.wand.execute(sql_update, params)
    await st.Zconnection.commit()
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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

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
    return await add_or_det_status(**kwargs)

async def update_vault_banlist(vault:dict):
    vault['banlist'] = {}
    await st.wand.execute('''SELECT User_ID FROM Perm_banlist''')
    p_bans = await st.wand.fetchall()
    for user_id in p_bans:
        vault['banlist'][user_id] = [0]
    
    await st.wand.execute('''SELECT c.VK_ID, b.User_ID
    FROM Chats c, Banlist b
    WHERE b.Chat_ID=c.Chat_ID''')
    bans = await st.wand.fetchall()
    for chat_id, user_id in bans:
        if user_id not in vault['banlist'].keys():
            vault['banlist'][user_id] = [chat_id]
        else:
            vault['banlist'][user_id].append(chat_id)
        

async def update_vault_chats(vault:dict):
    vault['chats'] = {}
    await st.wand.execute('''SELECT VK_ID, name FROM Chats''')
    chats = await st.wand.fetchall()
    for chat_id, name in chats:
         vault['chats'][chat_id] = {
             'name':name,
             'gate':0,
             'mute':[]
         }

    await st.wand.execute('''DELETE FROM Chat_mutes WHERE time<?''',[int(time.time())])
    await st.wand.execute('''SELECT c.VK_ID, m.User_ID, m.time
    FROM Chats c, Chat_mutes m
    WHERE m.Chat_ID=c.Chat_ID''')
    mutes = await st.wand.fetchall()
    for chat_id, user_id, time_ in mutes:
        vault['chats'][chat_id]['mute'].append((user_id, time_))

    await st.wand.execute('''DELETE FROM Chat_gates WHERE time<?''',[int(time.time())])
    await st.wand.execute('''SELECT c.VK_ID, g.time
    FROM Chats c, Chat_gates g
    WHERE g.Chat_ID=c.Chat_ID''')
    mutes = await st.wand.fetchall()
    for chat_id, time_ in mutes:
        vault['chats'][chat_id]['gate'] = time_
    

async def update_vault_enters(vault:dict):
    vault['enters'] = {}
    await st.wand.execute('''DELETE FROM Last_enters WHERE time<?''',[int(time.time())])
    await st.wand.execute('''SELECT c.VK_ID, l.User_ID, l.time
    FROM Chats c, Last_enters l
    WHERE l.Chat_ID=c.Chat_ID''')
    enters = await st.wand.fetchall()
    for chat_id, user_id, time_ in enters:
        if user_id not in vault['enters'].keys():
            vault['enters'][user_id] = [(chat_id, time_)]
        else:
            vault['enters'][user_id].append((chat_id, time_))

async def update_vault_admins(vault:dict):
    vault['admins'] = {}
    await st.wand.execute('''SELECT VK_ID, name, level FROM Admins''')
    admins = await st.wand.fetchall()
    for admin_id, name, level in admins:
        vault['admins'][admin_id] = {
            'name':name,
            'level':level,
            'chats': [0] if level>=3 else [],
            'targets':[]
        }
    
    await st.wand.execute('''SELECT a.VK_ID, c.VK_ID
    FROM Admins a, Chats c, Admin_fill af
    WHERE af.Chat_ID=c.Chat_ID AND af.Admin_ID=a.Admin_ID''')
    admin_fill = await st.wand.fetchall()
    for admin_id, chat_id in admin_fill:
        vault['admins'][admin_id]['chats'].append(chat_id)

    await st.wand.execute('''DELETE FROM Last_targets WHERE time<?''',[int(time.time())])
    await st.wand.execute('''SELECT a.VK_ID, l.User_ID, l.time
    FROM Admins a, Last_targets l
    WHERE l.Admin_ID=a.Admin_ID''')
    targets = await st.wand.fetchall()
    for admin_id, user_id, time_ in targets:
        vault['admins'][admin_id]['targets'].append((user_id, time_))



async def update_vault_groups(vault:dict):
    if 'groups' not in vault.keys():
        vault['groups'] = {}
    await st.wand.execute('''SELECT g.name, c.VK_ID
    FROM Groups g, Chats c, Group_fill gf
    WHERE gf.Chat_ID=c.Chat_ID AND gf.Group_ID=g.Group_ID''')
    groups = await st.wand.fetchall()
    for group_name, chat_id in groups:
        if group_name not in vault['groups'].keys():
            vault['groups'][group_name] = [chat_id]
        else:
            vault['groups'][group_name].append(chat_id)


async def update_vault_all(vault:dict):
    await update_vault_chats(vault)
    await update_vault_banlist(vault)
    await update_vault_admins(vault)
    await update_vault_enters(vault)
    await update_vault_groups(vault)




















async def getChatStatuses(chatId):
    sql = "SELECT Status, Time FROM Chat_status WHERE Chat_ID=(SELECT Chat_ID FROM Chats WHERE VK_ID=?)"
    await st.wand.execute(sql, [chatId])
    statuses = await st.wand.fetchall()
    res = []
    for status, tim in statuses:
        if tim-time.time()<0:
            delChatStatus(chatId, status)
        else:
            res.append(status)
            res.append(int((tim-time.time())/60+1))
    return res

async def getBanList():
    sql = '''SELECT c.VK_ID, b.User_ID
    FROM Chats c, Banlist b
    WHERE c.Chat_ID=b.Chat_ID'''
    await st.wand.execute(sql)
    return await st.wand.fetchall()

async def getChatsByGroup(userId, supposedGroup):
    sql='''SELECT C.VK_ID FROM Chats AS C, Admins AS A, Admin_fill AS AF,
    Groups AS G, Group_fill AS GF 
    WHERE 
    G.Name=? AND G.Group_ID=GF.Group_ID AND C.Chat_ID=GF.Chat_ID AND A.VK_ID=? AND
    AF.Admin_ID=A.Admin_ID AND AF.Chat_ID=C.Chat_ID'''
    await st.wand.execute(sql, [supposedGroup, userId])
    return getList(await st.wand.fetchall())

async def getAllChatsByGroup(supposedGroup):
    sql='''SELECT C.VK_ID FROM Chats AS C, Groups AS G, Group_fill AS GF 
    WHERE 
    G.Name=? AND G.Group_ID=GF.Group_ID AND C.Chat_ID=GF.Chat_ID'''
    await st.wand.execute(sql, [supposedGroup])
    return getList(await st.wand.fetchall())

async def getChatsByUserId(userId):
    sql='''SELECT C.VK_ID FROM Chats AS C, Admins AS A, Admin_fill AS AF
    WHERE 
    A.VK_ID=? AND AF.Admin_ID=A.Admin_ID AND AF.Chat_ID=C.Chat_ID'''
    await st.wand.execute(sql, [userId])
    return getList(await st.wand.fetchall())

async def getAllChats():
    sql = "SELECT VK_ID FROM Chats"
    await st.wand.execute(sql)
    return getList(await st.wand.fetchall())

async def getAdminLevel(userId): 
    sql = 'SELECT level FROM Admins WHERE VK_ID = ?'
    await st.wand.execute(sql, [userId])
    temp = await st.wand.fetchall()
    return temp[0][0] if temp != [] else 0
        
async def isChatAdmin(chatId, userId):             
    sql = '''SELECT COUNT(*) FROM Admin_fill
    WHERE Chat_id=(SELECT Chat_ID FROM Chats WHERE VK_ID=?) and
    Admin_ID=(SELECT Admin_ID FROM Admins WHERE VK_ID=?) or
    (SELECT level FROM Admins WHERE VK_ID = ?)=4'''
    await st.wand.execute(sql, [chatId, userId, userId])
    return (await st.wand.fetchone())[0] > 0


async def ban(chatId, userId):  
    sql = "INSERT INTO 'Banlist' ('Chat_ID', 'User_ID') VALUES((SELECT Chat_ID FROM Chats WHERE VK_ID=?), ?)"
    try:
        await st.wand.execute(sql,[chatId, userId])
    except:
        return False
    await st.Zconnection.commit()
    return True

async def multi_ban(ban_pairs): # not now
    sql = "INSERT INTO 'Banlist' ('Chat_ID', 'User_ID') VALUES((SELECT Chat_ID FROM Chats WHERE VK_ID=?), ?)"
    good = True
    try:
        await st.wand.executemany(sql, ban_pairs)
    except:
        good = False
    await st.Zconnection.commit()
    return good 

async def forgive(chatId, userId):
    sql = "DELETE FROM 'Banlist' WHERE Chat_ID=(SELECT Chat_ID FROM Chats WHERE VK_ID=?) AND User_ID=?"
    await st.wand.execute(sql,[chatId, userId])
    await st.Zconnection.commit()
    return True
    
async def isBanned(chatId, userId):
    sql = '''SELECT * 
    FROM Chats c, Banlist b 
    WHERE c.VK_ID=? AND b.Chat_ID=c.Chat_ID AND User_ID=?'''
    await st.wand.execute(sql,[chatId, userId])
    return True if await st.wand.fetchall() != [] else False

async def handleEnter(chatId, userId, time):
    # This part was in trigger in db, but now it is here
    delTime = 60*60*24 # 24 hours in seconds
    sql = '''DELETE FROM Last_enters WHERE ?-Time>?'''
    await st.wand.execute(sql, [time, delTime])
    try:
        sql = '''INSERT INTO 'Last_enters' ('Chat_ID', 'User_ID', 'Time') 
        VALUES((SELECT Chat_ID FROM Chats WHERE VK_ID=?), ?, ?)'''
        await st.wand.execute(sql,[chatId, userId, time])
    except:
        pass
    await st.Zconnection.commit()
    sql = '''SELECT c.VK_ID FROM Chats c, Last_enters l
    WHERE c.Chat_ID=l.Chat_ID AND l.User_ID=?'''
    await st.wand.execute(sql,[userId])
    return getList(await st.wand.fetchall())

async def handleTargets(admId, targets, time, maxCount):
    if targets == []:
        return []
    usedTargets = getUsedTargets(admId, time)
    targetSlots = maxCount-len(usedTargets)
    aviableTargets = []
    for targ in usedTargets:
        if targ in targets:
            aviableTargets.append(targ)
            targets.remove(targ)
    for targ in targets:
        if not targetSlots > 0:
            break
        try:
            sql = '''INSERT INTO 'Last_targets' ('Admin_ID', 'User_ID', 'Time') 
            VALUES((SELECT Admin_ID FROM Admins WHERE VK_ID=?), ?, ?)'''
            await st.wand.execute(sql,[admId, targ, time])
            aviableTargets.append(targ)
            targetSlots -= 1
        except:
            print('This error in handleTargets must not raise')
    await st.Zconnection.commit()
    return aviableTargets

async def getUsedTargets(admId, time):
    delTime = 60*60*24 # 24 hours in seconds
    sql = '''DELETE FROM Last_targets WHERE ?-Time>?'''
    await st.wand.execute(sql, [time, delTime])
    await st.Zconnection.commit()
    sql = '''SELECT l.User_ID FROM Admins a, Last_targets l
    WHERE l.Admin_ID=(SELECT Admin_ID FROM Admins WHERE VK_ID=?)'''
    await st.wand.execute(sql,[admId])
    return getList(await st.wand.fetchall())

async def get_base_chat_id(chatId):
    await st.wand.execute("SELECT Chat_ID FROM Chats WHERE VK_ID=?", [chatId])
    temp = await st.wand.fetchall()
    return temp[0][0] if temp != [] else False

async def get_base_group_id(groupName):
    await st.wand.execute("SELECT Group_ID FROM Groups WHERE Name=?", [groupName])
    temp = await st.wand.fetchall()
    return temp[0][0] if temp != [] else False

async def get_base_admin_id(adminId):
    await st.wand.execute("SELECT Admin_ID FROM Admins WHERE VK_ID=?", [adminId])
    temp = await st.wand.fetchall()
    return temp[0][0] if temp != [] else False


def getList(fetch):
    return [s[0] for s in fetch] # [(x,), (y,)]