from googletrans import Translator, LANGCODES

language_list = list(LANGCODES.keys())

class Messages_translator:
    __lang = "en"
    __trans = Translator()

    def __init__(self, language: str, to_eng: bool | None = False):
        Messages_translator.__lang = LANGCODES[f"{language}"]
        if to_eng == True:
            self.from_lang = Messages_translator.__lang
            self.to_lang = "en"
        else:
            self.from_lang = "en"
            self.to_lang = Messages_translator.__lang

    def translate(self, *args):
        for_translated_list = list(args)
        list_length = len(for_translated_list)
        if Messages_translator.__lang == "en":
            if list_length == 1:
                return for_translated_list[0]
            else:
                return for_translated_list
        else:
            translated_list = Messages_translator.__translate_list(self, for_translated_list)
            if list_length == 1:
                return translated_list[0]
            else:
                return translated_list

    def __translate_text(self, _text: str):
        if type(_text) != str:
            raise TypeError("Only str could be translated.")
        trs = Messages_translator.__trans
        return trs.translate(_text, src=self.from_lang, dest=self.to_lang).text

    def __translate_list(self, _list: list) -> list:
        instance_list = list()
        for item in _list:
            if type(item) == str:
                item_trs = Messages_translator.__translate_text(self, item)
            elif type(item) == list:
                item_trs = Messages_translator.__translate_list(self, item)
            elif type(item) == dict:
                item_trs = Messages_translator.__translate_dict(self, item)
            else:
                raise TypeError("How could...? You've got an error in list translation")
            instance_list.append(item_trs)
        return instance_list

    def __translate_dict(self, _dict: dict) -> dict:
        instance_dict = dict()
        dict_keys_list = list(_dict.keys())
        dict_values_list = list(_dict.values())
        for index, value in enumerate(dict_values_list):
            if type(value) == str:
                value_trs = Messages_translator.__translate_text(self, value)
            elif type(value) == dict:
                value_trs = Messages_translator.__translate_dict(self, value)
            elif type(value) == list:
                value_trs = Messages_translator.__translate_list(self, value)
            else:
                raise TypeError("How could...? You've got an error in dict translation")
            instance_dict[f"{dict_keys_list[index]}"] = value_trs
        return instance_dict

class UI_messages(Messages_translator):
    __system_messages_dict = {
        "title":
        """Chatbot for you!""",
        "choice":
        """Choose""",
        "write":
        """Write""",
        "wait":
        """Please wait a moment...""",
        "complete":
        """Action complete!""",
        "send_to_ai": {
            "request":
            """Send a message to the ai!""",
            "error":
            """Oh... you might forget to fill the form above! Can you double-check? I need some information about your baby's poop to help you!"""
        },
        "reset":
        """Reset""",
        "poop_info_request":
        """Tell me some informations about your baby's poop!""",
        "form": {
            "color_info" : {
                "request" :
                """Write your baby's poop color.""",
                "contents":
                ["Red", "Green", "Black", "White", "Brown", "Ambiguous"],
                "suffix":
                """The stool color of my baby was""",
                "error":
                """You must tell me about poop color!"""
                },
            "form_info" : {
                "request":
                """Choose the baby poop's form""",
                "contents":
                ["severe diarrhea", "diarrhea", "normal", "constipation", "severe constipation"],
                "suffix":
                """The stool of my baby was"""
                },
            "blood_info" : {
                "request":
                """Does your baby's poop have any blood?""",
                "contents":
                ["not-bloody", "bloody"],
                "suffix":
                """The stool of my baby seemed to be"""
                }
            },
        "RAG":{
            "request":
            """Start preparation for < R A G >!""",
            "error":
            """You have to prepare RAG thorough left sidebar for me to diagnosis."""
            },
        "model": {
            "request":
            """Load <Chat_model>!""",
            "error":
            """You have to set a chat model thorough left sidebar for me to diagnosis."""
            },
        "chain": {
            "num":
            """How many documents do you wanna contain for <<RAG search>?""",
            "start":
            """Start making diagnosis"""
        },
        "chat": {
            "start":
            """You can start chat about the diagnosis now on!""",
            "label":
            """Chat Start!"""
        }
    }
    __ai_messages_dict = {
        "intro" :
        """Good day. I am present to alleviate your concerns. 
        \nIt brings me satisfaction to know that you have entrusted me with aiding in the resolution of your worries.
        \nI am committed to offering my utmost efforts to address your concerns.
        \nMight you kindly provide details regarding the infant's symptoms?""",

        "form_submitted" :
        """Understood. I believe I have an understanding of the symptoms the baby exhibited.
        \nAdditionally, do you have any further information you would like to provide?
        \nPlease feel free to share any additional details.""",

        "check_user_input" :
        """Do you think the explanation you sent is enough?
        \nPlease correct and send the explanation until you are satisfied, and press the button below if you are satisfied""",

        "chain" :
        """Understood. Could you please wait for a moment?
        \nI will provide an assessment of the baby's health status within a few minutes."""
        }
    __user_messages_dict = {
        "user_confirmed":
        """I am satisfied with my explanation."""
    }

    def system_messages(self):
        messages: dict = super().translate(UI_messages.__system_messages_dict)
        return messages
    def ai_messages(self):
        messages: dict = super().translate(UI_messages.__ai_messages_dict)
        return messages 
    def user_messages(self):
        messages: dict = super().translate(UI_messages.__user_messages_dict)
        return messages

    @classmethod
    def format_messages_for_form(cls):
        form_choices_dict = dict()
        form_suffix_dict = dict()
        form_option_list = list(cls.__system_messages_dict["form"].keys())
        for item in form_option_list:
            form_choices_dict[item] = cls.__system_messages_dict["form"][item]["contents"]
            form_suffix_dict[item] = cls.__system_messages_dict["form"][item]["suffix"]
        return form_choices_dict, form_suffix_dict