import time, logging, sqlite3, asyncio
from modules.storage import vault

class st:
    Zconnection = None
    wand = None
    basefile = None
    logger = None

# посоветоваться и, возможно, сделать всё синхронным

# logging.getLogger('aiosqlite').setLevel(logging.CRITICAL)
# logger = logging.getLogger(__name__.split('.')[-1])
# logger.setLevel(1)

def logging_decorator(func):
    def log_after(*args, **kwargs):
        status, respond = func(*args, **kwargs)
        intro = 'Done:' if status else 'FAIL:'
        level = 11 if status else 13
        st.logger.log(level, f" {intro} {func.__name__}{args}{kwargs} - {respond}")
        return (status, respond)
    return log_after

def get_conn_and_wand(basefile):
    Zconnection = sqlite3.connect(basefile)
    wand = Zconnection.cursor()
    wand.execute("PRAGMA foreign_keys=on;")
    return (Zconnection, wand)

def initiate(basefile, base_logger):
    st.basefile = basefile
    st.logger = base_logger
    st.Zconnection, st.wand = get_conn_and_wand(basefile)
    update_vault_all()


def add_or_update_object(name, sql, params:list, add_or_update):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    try:
        wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        unique_field_fail = error.args[0].split('.')[-1]
        return (False, f"{unique_field_fail} already added")
    else:
        Zconnection.commit()
    return (True, f"{name} {add_or_update}ed")

@logging_decorator
def add_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_update":"add",
        "sql":"INSERT INTO Chats ('VK_ID', 'Name') VALUES(?, ?)",
        "params":[chat_id, name]
    }
    return add_or_update_object(**kwargs)

@logging_decorator
def add_group(group_name):
    kwargs = {
        "name":'Group',
        "add_or_update":"add",
        "sql":"INSERT INTO Groups ('Name') VALUES(?)",
        "params":[group_name]
    }
    return add_or_update_object(**kwargs)
    
@logging_decorator
def add_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_update":"add",
        "sql":"INSERT INTO Admins ('VK_ID', 'Level', 'Name') VALUES(?, ?, ?)",
        "params":[admin_id, level, name]
    }
    return add_or_update_object(**kwargs)

@logging_decorator
def update_chat(chat_id, name):
    kwargs = {
        "name":'Chat',
        "add_or_update":"update",
        "sql":"UPDATE Chats SET Name=? WHERE VK_ID=?",
        "params":[name, chat_id]
    }
    return add_or_update_object(**kwargs)

@logging_decorator
def update_group(old_group_name, new_group_name):
    kwargs = {
        "name":'Group',
        "add_or_update":"update",
        "sql":"UPDATE Groups SET Name=? WHERE Name=?",
        "params":[new_group_name, old_group_name]
    }
    return add_or_update_object(**kwargs)
    
@logging_decorator
def update_admin(admin_id, level, name):
    kwargs = {
        "name":'Admin',
        "add_or_update":"update",
        "sql":"UPDATE Admins SET Level=?, Name=? WHERE VK_ID=?",
        "params":[level, name, admin_id]
    }
    return add_or_update_object(**kwargs)

def del_object(name, param, get_base_func, connected_tables):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    base_id = get_base_func(param)
    if not base_id:
        return (False, f"{name} does not exists")
    sql = [f"DELETE FROM {table} WHERE {name}_ID={base_id};" for table in connected_tables]
    wand.executescript(' '.join(sql))
    Zconnection.commit()
    return (True, f"{name} probably deleted")

@logging_decorator
def del_group(group_name):
    kwargs = {
        "name":'Group',
        "param":group_name,
        'get_base_func':get_base_group_id,
        'connected_tables':['Group_fill','Groups']
    }
    return del_object(**kwargs)

@logging_decorator
def del_chat(chat_id):
    kwargs = {
        "name":'Chat',
        "param":chat_id,
        'get_base_func':get_base_chat_id,
        'connected_tables':['Group_fill','Admin_fill','Bans_fill','Last_enters','Chat_mutes','Chat_gates','Chats']
    }
    return del_object(**kwargs)

@logging_decorator
def del_admin(admin_id):
    kwargs = {
        "name":'Admin',
        "param":admin_id,
        'get_base_func':get_base_admin_id,
        'connected_tables':['Admin_fill','Last_targets','Admins']
    }
    return del_object(**kwargs)

def add_or_del_pair_connection(chat_id, second_id_or_name, get_base_func, second_param_name, sql, add_or_delet):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    base_chat_id = get_base_chat_id(chat_id)
    base_second_id = get_base_func(second_id_or_name)
    if not base_chat_id:
        return (False, f"Wrong chat")
    if not base_second_id:
        return (False, f"Wrong {second_param_name}")
    try:
        wand.execute(sql, [base_chat_id, base_second_id])
    except:
        if add_or_delet=="add":
            return (False, f"{second_param_name} already added")
        else:
            return (False, f"No such connection")
    Zconnection.commit()
    return (True, f"{second_param_name} {add_or_delet}ed")

@logging_decorator
def add_admin_to_chat(chat_id, admin_id):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":admin_id,
        "get_base_func":get_base_admin_id,
        "second_param_name":"Admin",
        "add_or_delet":"add",
        "sql":"INSERT INTO Admin_fill ('Chat_ID', 'Admin_ID') VALUES(?, ?)"
    }
    return add_or_del_pair_connection(**kwargs)

@logging_decorator
def add_chat_to_group(chat_id, group_name):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":group_name,
        "get_base_func":get_base_group_id,
        "second_param_name":"Group",
        "add_or_delet":"add",
        "sql":"INSERT INTO Group_fill ('Chat_ID', 'Group_ID') VALUES(?, ?)"
    }
    return add_or_del_pair_connection(**kwargs)

@logging_decorator
def del_chat_from_group(chat_id, group_name):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":group_name,
        "get_base_func":get_base_group_id,
        "second_param_name":"Group",
        "add_or_delet":"delet",
        "sql":"DELETE FROM Group_fill WHERE Chat_ID=? AND Group_ID=?"
    }
    return add_or_del_pair_connection(**kwargs)

@logging_decorator
def del_admin_from_chat(chat_id, admin_id):
    kwargs = {
        "chat_id":chat_id,
        "second_id_or_name":admin_id,
        "get_base_func":get_base_admin_id,
        "second_param_name":"Admin",
        "add_or_delet":"delet",
        "sql":"DELETE FROM Admin_fill WHERE Chat_ID=? AND Admin_ID=?"
    }
    return add_or_del_pair_connection(**kwargs)
    
def add_or_del_status(name, base_chat_or_admin_id, params:list, sql, sql_update, add_or_delet):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    if not base_chat_or_admin_id:
        return (False, "Wrong chat or something else")
    params.insert(0, base_chat_or_admin_id)
    try:
        st.wand.execute(sql, params)
    except Exception as error:
        if not isinstance(error, aiosqlite.IntegrityError):
            return (False, str(error))
        params.pop(0)
        params.append(base_chat_or_admin_id)
        wand.execute(sql_update, params)
    Zconnection.commit()
    # Zconnection.close()
    # Zconnection, wand = get_conn_and_wand(st.basefile)
    wand.execute('''DELETE FROM Last_enters WHERE time<?''',[int(time.time())])
    negative = '' if add_or_delet=='add' else 'un'
    return (True, f"Chat {negative}{name}ed")

@logging_decorator
def add_mute(chat_id, user_id, time_):
    kwargs = {
        "name":"mut",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Chat_mutes ('Chat_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Chat_mutes SET Time=? WHERE User_ID = ? AND Chat_ID=?"
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def add_gate(chat_id, time_):
    kwargs = {
        "name":"lock",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[time_],
        "add_or_delet":"add",
        "sql":"INSERT INTO Chat_gates ('Chat_ID', 'time') VALUES(?, ?)",
        "sql_update":"UPDATE Chat_gates SET Time=? WHERE Chat_ID=?"
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def add_enter(chat_id, user_id, time_):
    kwargs = {
        "name":"enter",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Last_enters ('Chat_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Last_enters SET Time=? WHERE User_ID = ? AND Chat_ID=?"
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def add_target(admin_id, user_id, time_):
    kwargs = {
        "name":"target",
        "base_chat_or_admin_id":get_base_admin_id(admin_id),
        "params":[time_, user_id],
        "add_or_delet":"add",
        "sql":"INSERT INTO Last_targets ('Admin_ID', 'time', 'User_ID') VALUES(?, ?, ?)",
        "sql_update":"UPDATE Last_targets SET Time=? WHERE User_ID=? AND Admin_ID=?"
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def del_mute(chat_id, user_id):
    kwargs = {
        "name":"mut",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Chat_mutes WHERE Chat_ID=? AND User_ID=?",
        "sql_update":None
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def del_gate(chat_id):
    kwargs = {
        "name":"lock",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Chat_gates WHERE Chat_ID=?",
        "sql_update":None
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def del_enter(chat_id, user_id):
    kwargs = {
        "name":"enter",
        "base_chat_or_admin_id":get_base_chat_id(chat_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Last_enters WHERE Chat_ID=? AND User_ID=?",
        "sql_update":None
    }
    return add_or_del_status(**kwargs)

@logging_decorator
def del_target(admin_id, user_id):
    kwargs = {
        "name":"target",
        "base_chat_or_admin_id":get_base_admin_id(admin_id),
        "params":[user_id],
        "add_or_delet":"delet",
        "sql":"DELETE FROM Last_targets WHERE Admin_ID=? AND User_ID=?",
        "sql_update":None
    }
    return add_or_del_status(**kwargs)

def add_ban(user_id, chat_id):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    sql = "INSERT INTO 'Bans' ('VK_ID', 'Everywhere') VALUES(?, ?)"
    try:
        wand.exrcute(sql, [user_id, 0])
    except:
        pass

    sql = "INSERT INTO 'Bans_fill' ('Chat_ID', 'Ban_ID') VALUES((SELECT Chat_ID FROM Chats WHERE VK_ID=?), (SELECT Ban_ID FROM Bans WHERE VK_ID=?))"
    try:
        wand.exrcute(sql, [chat_id, user_id])
    except:
        return (False, f"User {user_id} already banned in {chat_id}")
    Zconnection.commit()
    return (True, f"User {user_id} banned in {chat_id}")

def del_ban(user_id, chat_id):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    wand.execute('''SELECT c.VK_ID, b.VK_ID, b.Everywhere
    FROM Chats c, Bans b, Bans_fill bf
    WHERE b.Ban_ID=bf.Ban_ID AND bf.Chat_ID=c.Chat_ID AND b.VK_ID=?''',[user_id])
    chats_under_ban = wand.fetchall()
    for chat, user, every in chats_under_ban:
        if chat==chat_id:
            every_flag = every
            break
    else:
        return (False, f"User {user_id} is not banned in {chat_id}")
    sql = '''DELETE FROM Bans_fill WHERE 
    Chat_ID=(SELECT Chat_ID FROM Chats WHERE VK_ID=?) AND 
    Ban_ID=(SELECT Ban_ID FROM Bans WHERE VK_ID=?)'''
    wand.execute(sql,[chat_id, user_id])

    if not every_flag and len(chats_under_ban)==1:
        wand.execute('''DELETE FROM Bans WHERE VK_ID=?''',[user_id])
    Zconnection.commit()
    return (True, f"User {user_id} is forgiven in {chat_id}")

def add_perm_ban(user_id):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    sql = '''INSERT INTO Bans(VK_ID, Everywhere)
    VALUES (?,1)
    ON CONFLICT(VK_ID) DO UPDATE SET Everywhere=excluded.Everywhere'''
    wand.execute(sql,[user_id])
    Zconnection.commit()
    return (True, f"User {user_id} is banned everywhere")

def del_perm_ban(user_id):
    Zconnection, wand = get_conn_and_wand(st.basefile)
    user_s_banlist = vault['banlist'].get(user_id, [])
    if 0 not in user_s_banlist:
        return (False, f"User {user_id} is not fully banned")
    if len(user_s_banlist)>1:
        wand.execute("UPDATE Bans SET Everywhere=0 WHERE VK_ID=?",[user_id])
    else:
        wand.execute("DELETE FROM Bans WHERE VK_ID=?",[user_id])
    Zconnection.commit()
    return (False, f"User {user_id} is not fully banned now")

# переделать это всё, вообще всё, под нормальные методы работы с базой, а не этот колхоз


def update_vault_banlist():
    vault['banlist'] = {}
    st.wand.execute('''SELECT VK_ID, Everywhere FROM Bans''')
    bans = st.wand.fetchall()
    for user_id, everywhere in bans:
        vault['banlist'][user_id] = [0] if everywhere else []
    
    st.wand.execute('''SELECT c.VK_ID, b.VK_ID
    FROM Chats c, Bans b, Bans_fill bf
    WHERE b.Ban_ID=bf.Ban_ID AND bf.Chat_ID=c.Chat_ID''')
    banlist = st.wand.fetchall()
    for chat_id, user_id in banlist:
        vault['banlist'][user_id].append(chat_id)
            
        

def update_vault_chats():
    Zconnection, wand = get_conn_and_wand(st.basefile)
    vault['chats'] = {}
    wand.execute('''SELECT VK_ID, name FROM Chats''')
    chats = wand.fetchall()
    for chat_id, name in chats:
         vault['chats'][chat_id] = {
             'name':name,
             'gate':0,
             'mute':[]
         }

    wand.execute('''DELETE FROM Chat_mutes WHERE time<?''',[int(time.time())])
    wand.execute('''SELECT c.VK_ID, m.User_ID, m.time
    FROM Chats c, Chat_mutes m
    WHERE m.Chat_ID=c.Chat_ID''')
    mutes = wand.fetchall()
    for chat_id, user_id, time_ in mutes:
        vault['chats'][chat_id]['mute'].append((user_id, time_))

    wand.execute('''DELETE FROM Chat_gates WHERE time<?''',[int(time.time())])
    wand.execute('''SELECT c.VK_ID, g.time
    FROM Chats c, Chat_gates g
    WHERE g.Chat_ID=c.Chat_ID''')
    mutes = wand.fetchall()
    for chat_id, time_ in mutes:
        vault['chats'][chat_id]['gate'] = time_
    Zconnection.commit()
    

def update_vault_enters():
    Zconnection, wand = get_conn_and_wand(st.basefile)
    vault['enters'] = {}
    wand.execute('''DELETE FROM Last_enters WHERE time<?''',[int(time.time())])
    wand.execute('''SELECT c.VK_ID, l.User_ID, l.time
    FROM Chats c, Last_enters l
    WHERE l.Chat_ID=c.Chat_ID''')
    enters = wand.fetchall()
    for chat_id, user_id, time_ in enters:
        if user_id not in vault['enters'].keys():
            vault['enters'][user_id] = [(chat_id, time_)]
        else:
            vault['enters'][user_id].append((chat_id, time_))
    Zconnection.commit()

def update_vault_admins():
    Zconnection, wand = get_conn_and_wand(st.basefile)
    vault['admins'] = {}
    wand.execute('''SELECT VK_ID, name, level FROM Admins''')
    admins = wand.fetchall()
    for admin_id, name, level in admins:
        vault['admins'][admin_id] = {
            'name':name,
            'level':level,
            'chats': [0] if level>=3 else [],
            'targets':[]
        }
    
    wand.execute('''SELECT a.VK_ID, c.VK_ID
    FROM Admins a, Chats c, Admin_fill af
    WHERE af.Chat_ID=c.Chat_ID AND af.Admin_ID=a.Admin_ID''')
    admin_fill = wand.fetchall()
    for admin_id, chat_id in admin_fill:
        vault['admins'][admin_id]['chats'].append(chat_id)

    wand.execute('''DELETE FROM Last_targets WHERE time<?''',[int(time.time())])
    wand.execute('''SELECT a.VK_ID, l.User_ID, l.time
    FROM Admins a, Last_targets l
    WHERE l.Admin_ID=a.Admin_ID''')
    targets = wand.fetchall()
    for admin_id, user_id, time_ in targets:
        vault['admins'][admin_id]['targets'].append((user_id, time_))
    Zconnection.commit()
    



def update_vault_groups():
    if 'groups' not in vault.keys():
        vault['groups'] = {}
    st.wand.execute('''SELECT g.name, c.VK_ID
    FROM Groups g, Chats c, Group_fill gf
    WHERE gf.Chat_ID=c.Chat_ID AND gf.Group_ID=g.Group_ID''')
    groups = st.wand.fetchall()
    for group_name, chat_id in groups:
        if group_name not in vault['groups'].keys():
            vault['groups'][group_name] = [chat_id]
        else:
            vault['groups'][group_name].append(chat_id)


def update_vault_all():
    update_vault_chats()
    update_vault_banlist()
    update_vault_admins()
    update_vault_enters()
    update_vault_groups()



def get_base_chat_id(chatId):
    st.wand.execute("SELECT Chat_ID FROM Chats WHERE VK_ID=?", [chatId])
    temp = st.wand.fetchall()
    return temp[0][0] if temp != [] else False

def get_base_group_id(groupName):
    st.wand.execute("SELECT Group_ID FROM Groups WHERE Name=?", [groupName])
    temp = st.wand.fetchall()
    return temp[0][0] if temp != [] else False

def get_base_admin_id(adminId):
    st.wand.execute("SELECT Admin_ID FROM Admins WHERE VK_ID=?", [adminId])
    temp = st.wand.fetchall()
    return temp[0][0] if temp != [] else False


def getList(fetch):
    return [s[0] for s in fetch] # [(x,), (y,)]

def get_admin_level(user_id):
    admin = vault['admins'].get(user_id, False)
    return admin['level'] if admin else False

def is_chat_admin(user_id, chat_id):
    if user_id not in vault['admins'].keys():
        return False
    if 0 in  vault['admins'][user_id]['chats'] or chat_id in vault['admins'][user_id]['chats']:
        return True
    return False


def get_chats_by_admin(user_id):
    admin = vault['admins'].get(user_id, False)
    return admin['chats'] if admin else []

def handle_targets(targets):                            # TODO

    return targets

def handle_enter(user_id, chat_id, time_):
    add_enter(chat_id, user_id, time_)
    update_vault_enters()
    enters = vault['enters'][user_id]
    return list(map(lambda pair:pair[0], enters))

def is_banned(user_id, chat_id):
    if user_id not in vault['banlist'].keys():
        return False
    if 0 in vault['banlist'][user_id] or chat_id in vault['banlist'][user_id]:
        return True




def test1(num=0):
    Zconnection = aiosqlite.connect(st.b)
    wand = Zconnection.cursor()
    wand.execute("PRAGMA foreign_keys=on;")
    sql = '''INSERT INTO Bans(VK_ID, Everywhere) VALUES (?,?)'''
    wand.execute(sql, [1324, 0])
    asyncio.sleep(2)
    sql = '''SELECT * FROM Bans'''
    wand.execute(sql)
    print(1,wand.fetchall())
    Zconnection.rollback()
    wand.execute(sql)
    print(1,wand.fetchall())
    return
    

def test2(num=0):
    Zconnection = aiosqlite.connect(st.b)
    wand = Zconnection.cursor()
    wand.execute("PRAGMA foreign_keys=on;")
    # sql = '''INSERT INTO Bans(VK_ID, Everywhere) VALUES (?,?)'''
    # wand.execute(sql, [4321, 1])
    sql = '''SELECT * FROM Bans'''
    wand.execute(sql)
    print(2,wand.fetchall())
    Zconnection.rollback()
    wand.execute(sql)
    print(2,wand.fetchall())
    return
    pass







#######################################################


def get_id_from_word(word:str):
    partWithId = word.split('|')[0]
    supposedId = partWithId.replace('[id','').replace('[club','-')
    try:
        return int(supposedId)
    except:
        return False

class DataBox:

    handled_targets = None
    handled_chats = None


    def __init__(self,event):
        self.event = event

    @property
    def msg(self):
        return self.event.object.object.message

    @property
    def api(self):
        return self.event.api_ctx
    
    @property
    def command(self):
        return self.msg.text.split(' ')[1]

    @property
    def admin_level(self):
        return get_admin_level(self.msg.from_id)

    @property
    def targets(self):
        if self.handled_targets is not None:
            return self.handled_targets
        targets = []
        for word in self.msg.text.split(' '):
            targ = get_id_from_word(word)
            if targ:
                targets.append(targ)
        for fwd in self.msg.fwd_messages:
            targets.append(fwd.from_id)
        targets = list(set(targets)-set([self.event.object.group_id*-1]))
        self.handled_targets = handle_targets(targets)
        return self.handled_targets
        
    @property
    def chats(self):
        if self.handled_chats is not None:
            return self.handled_chats

        supposedGroup = self.msg.text.split(' ')[2]

        chatList = []
        if supposedGroup == 'here':
            chatList =  [self.msg.peer_id]
        elif supposedGroup == 'all':
            chatList = list(vault['chats'].keys())
        else:
            chatList = vault['groups'].get(supposedGroup, False)
        if not chatList:
            try:
                chatList = list(map(int,supposedGroup.split(',')))
                chatList = [chat if chat>10000 else chat+2000000000 for chat in chatList]
            except:
                self.handled_chats = []
                return self.handled_chats

        admins_chats = get_chats_by_admin(self.msg.from_id)
        if 0 in admins_chats:
            self.handled_chats = chatList
        else:
            self.handled_chats = list(set(chatList).intersection(set(admins_chats)))
        return self.handled_chats

    def remove_target(self, target):
        if self.handled_targets is None:
            return
        if target in self.handled_targets:
            self.handled_targets.remove(target)

    def remove_chat(self, chat):
        if self.handled_chats is None:
            return
        if chat in self.handled_chats:
            self.handled_chats.remove(chat)
