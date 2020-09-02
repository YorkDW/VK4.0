import time
import modules.basemaster as base
import modules.storage as stor



class DataBox:

    handled_targets = None
    handled_chats = None
    start_time = 0


    def __init__(self,event):
        self.event = event
        self.start_time = time.perf_counter()

    @property
    def msg(self):
        return self.event.object.object.message

    @property
    def api(self):
        return self.event.api_ctx
    
    @property
    def command(self):
        try:
            return self.msg.text.split(' ')[1].lower()
        except:
            return None

    def text_list(self, pos = 'all'):                # get list of words
        text_list = self.event.object.object.message.text.split(' ')      
        if pos == 'all':
            return text_list
        elif len(text_list)<=abs(pos):
            return ""
        else:
            return text_list[pos]

    def get_by_name(self, name, type_name = False):
        for word in self.event.object.object.message.text.split(' '):
            if word.startswith(f"{name}="):
                named_param = word.split('=')[1]
                if type_name:
                    try:
                        return type_name(named_param)
                    except:
                        continue
                return word.split('=')[1]
        return ""

    @property
    def param(self):
        text_list = self.msg.text.split(' ')
        if len(text_list)>=4:
            return text_list[3]
        if len(text_list)==3:
            return text_list[2]
        
        return ""

    @property
    def admin_level(self):
        return base.get_admin_level(self.msg.from_id)

    def _get_targets(self):
        if self.handled_targets is not None:
            return self.handled_targets
        targets = []
        for word in self.msg.text.split(' '):
            targ = self.get_id_from_word(word)
            if targ:
                targets.append(targ)
        for fwd in self.msg.fwd_messages:
            targets.append(fwd.from_id)
        if self.msg.reply_message:
            targets.append(self.msg.reply_message.from_id)
        self.handled_targets = list(set(targets)-set([self.event.object.group_id*-1]))
        return self.handled_targets

    def _set_targets(self, targets:list):
        self.handled_targets = targets

    targets = property(_get_targets, _set_targets)
        
    def _get_chats(self):
        if self.handled_chats is not None:
            return self.handled_chats
        try:
            word_of_chats = self.msg.text.split(' ')[2]
        except:
            self.handled_chats = []
            return self.handled_chats

        chat_list = []

        # temporary solution for faster chat name search
        chat_name_dict = {data['name']:chat_id for chat_id, data in stor.vault['chats'].items()}

        for pointer in word_of_chats.split(','):
            if pointer == 'here':
                chat_list.append(self.msg.peer_id)

            elif pointer == 'all':
                chat_list.extend(list(stor.vault['chats'].keys()))

            elif pointer in stor.vault['groups'].keys():
                chat_list.extend(stor.vault['groups'][pointer])
            
            elif pointer in chat_name_dict.keys():
                chat_list.append(chat_name_dict[pointer])

            elif pointer.isdigit():
                chat_id = int(pointer)
                chat_list.append(chat_id if chat_id>1000 else chat_id+2*10**9)

        if not chat_list:
            self.handled_chats = []
            return self.handled_chats

        admins_chats = base.get_chats_by_admin(self.msg.from_id)

        if 0 in admins_chats:
            self.handled_chats = chat_list
        else:
            self.handled_chats = list(set(chat_list).intersection(set(admins_chats)))
            
        return self.handled_chats

    def _set_chats(self, chats:list):
        self.handled_chats = chats

    chats = property(_get_chats, _set_chats)

    def remove_target(self, target):
        if self.handled_targets is None:
            return
        if target in self.handled_targets:
            self.handled_targets.remove(target)

    @staticmethod
    def get_id_from_word(word:str):
        if not (word.startswith('[id') or word.startswith('[club')):
            return False
        partWithId = word.split('|')[0]
        supposedId = partWithId.replace('[id','').replace('[club','-')
        try:
            return int(supposedId)
        except:
            return False