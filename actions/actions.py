import os
import json
import re
from typing import Dict, Text, Any, List
import logging
from urllib import response
from dateutil import parser
import sqlalchemy as sa
import sqlite3
from numpy import random
import actions.mysql as mysql

import twilio
from twilio.rest import Client

import pymongo

import spacy
import en_core_web_sm
import nltk
from nltk.corpus import wordnet
from bltk.langtools import PosTagger
from bltk.langtools import Tokenizer

import bangla
from banglanum2words import num_convert
from num2words import num2words

import datetime
from datetime import date

from rasa_sdk.events import ReminderScheduled

#Global variable is here
#-----------------------------------------------------
nlp = en_core_web_sm.load()
nlu = spacy.load("en_core_web_sm")
UserText = None
GlobalList = []
flag = False
#-----------------------------------------------------

from rasa_sdk.events import SlotSet, ActionReverted, UserUttered, Form, BotUttered
from rasa_sdk.forms import REQUESTED_SLOT

from rasa_sdk.interfaces import Action
from rasa_sdk.events import (
    SlotSet,
    EventType,
    ActionExecuted,
    SessionStarted,
    Restarted,
    FollowupAction,
    UserUtteranceReverted,
    AllSlotsReset,
)
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher

from actions.parsing import (
    parse_duckling_time_as_interval,
    parse_duckling_time,
    get_entity_details,
    parse_duckling_currency,
)

from actions.profile_db import create_database, ProfileDB

from actions.custom_forms import CustomFormValidationAction
from rasa_sdk.types import DomainDict
from actions.converter import is_ascii, BnToEn_Word, BnToEn

db_manager = mysql.DBManager()
logger = logging.getLogger(__name__)

# The profile database is created/connected to when the action server starts
# It is populated the first time `ActionSessionStart.run()` is called.

PROFILE_DB_NAME = os.environ.get("PROFILE_DB_NAME", "profile")
PROFILE_DB_URL = os.environ.get("PROFILE_DB_URL", f"sqlite:///{PROFILE_DB_NAME}.db")
ENGINE = sa.create_engine(PROFILE_DB_URL)
create_database(ENGINE, PROFILE_DB_NAME)

profile_db = ProfileDB(ENGINE)


class ActionSessionStart(Action):
    """Executes at start of session"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_session_start"

    @staticmethod
    def _slot_set_events_from_tracker(
        tracker: "Tracker",
    ) -> List["SlotSet"]:
        """Fetches SlotSet events from tracker and carries over keys and values"""

        # when restarting most slots should be reset
        relevant_slots = ["currency"]

        return [
            SlotSet(
                key=event.get("name"),
                value=event.get("value"),
            )
            for event in tracker.events
            if event.get("event") == "slot" and event.get("name") in relevant_slots
        ]

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Executes the custom action"""
        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        events.extend(self._slot_set_events_from_tracker(tracker))

        # create a mock profile by populating database with values specific to tracker.sender_id
        profile_db.populate_profile_db(tracker.sender_id)
        currency = profile_db.get_currency(tracker.sender_id)

        #-----------------------------------------Session Id Exists or Not-------------------------------
        
        sv=tracker.current_slot_values()
        sv_json_object = json.dumps(sv, indent = 4)
        phone = tracker.get_slot("phone_number")
        print("session started and set everything Null to DB initially")
        account = db_manager.set_session_id(
                tracker.sender_id, phone, sv_json_object
            )
        print(account)
        
        #---------------------------------------------------------------------------------------------------------------

        # initialize slots from mock profile
        events.append(SlotSet("currency", currency))

        # add `action_listen` at the end
        events.append(ActionExecuted("action_listen"))

        return events


class ActionRestart(Action):
    """Executes after restart of a session"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_restart"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Executes the custom action"""
        return [Restarted(), FollowupAction("action_session_start")]

class ActionResetSlots(Action):
    """action_reset_all_slots"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_all_slots"
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        print ("slots are being reset")
        return [AllSlotsReset()]

class ResetCardNumber(Action):
    """action_reset_card_number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_card_number"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        print("Reset Slot Function Called.")
        return[
                SlotSet("card_number", None),
            ]

class ActionCallCut(Action):
    """Action_Call_Cut"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "Action_Call_Cut"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        res = tracker.latest_message['intent'].get('name')
        print(f"intent from user is {res}")
        """Executes the action"""
        print("Action_Call_Cut")
        if tracker.latest_message['intent'].get('name') == "affirm":
            print(tracker.latest_message['intent'].get('name'))
            dispatcher.utter_message(text="CC")
        if tracker.latest_message['intent'].get('name') == "deny":
            print(tracker.latest_message['intent'].get('name'))
            dispatcher.utter_message(text="CC")
        return[]

class ResetAmount(Action):
    """action_reset_AMOUNT"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_AMOUNT"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        print("Reset Slot Function Called.")
        return[
                SlotSet("amount-of-money", None),
            ]
class AffirmOrDenyCardNumber(Action):
    """action_check_response"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_response"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["card_number"] = None
            print(tracker.slots["card_number"])
            print(tracker.latest_message['intent'].get('name'))
            # return [FollowupAction('card_bill_form_c_number')]
            return [SlotSet("card_number", None), Form("card_bill_form_c_number")]

class ActionCardnumberCard(FormValidationAction):
    """validate_card_bill_form_c_number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_card_bill_form_c_number"

    async def validate_card_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        
        print("validate card number")
        card = tracker.get_slot("card_number")
        print("card Number is : ", card)
        
        
        #BANGLA Check Here
        if (not is_ascii(card)):  #If Bangla then enter here. is_ascii(otp) True for English
            cn = None
            if card.isnumeric():
                cn = BnToEn(card)
                print(str(cn))
                card = str(cn)
                print("card Number is ", card)
                tracker.slots["card_number"] = card
                if len(card)!=10 or card == None:
                    dispatcher.utter_message(response="utter_invalidCARDnumber")
                    return {"card_number": None}
                else:
                    print("Correct card Number")
                    # account = db_manager.set_slot_value(tracker.sender_id, "card_number", card)
                    return {"card_number": card}
        else:
            if len(card)!=10 or card == None:
                dispatcher.utter_message(response="utter_invalidCARDnumber")
                return {"card_number": None}
            else:
                print("Correct card Number")
                # account = db_manager.set_slot_value(tracker.sender_id, "card_number", card)
                return {"card_number": card}


class ActionValidateAMOUNT(FormValidationAction):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_card_bill_form_amount"
    async def validate_amount_of_money(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        print("CCV in amount validation:", tracker.get_slot("CCV"))
        amount = tracker.get_slot("amount-of-money")
        print("amount inside function: ", amount)

        account_balance = profile_db.get_account_balance(tracker.sender_id)

        number = None
        #BANGLA Check Here
        if(not is_ascii(amount)):  #If Bangla then enter here
            print("Hello, Check Bangla")
            if amount.isnumeric():
                number = BnToEn(amount)
                amount = str(number)
                print("Number : ", number)
                print(amount)
                if(int(amount)<=0):
                    dispatcher.utter_message(response="utter_invalidAMOUNT")
                    # print("1")
                    return {"amount-of-money": None}
                else:
                    # print("2")
                    # account = db_manager.set_slot_value(tracker.sender_id, 'amount-of-money', amount)
                    return {"amount-of-money": amount}
            else:
                # print("3")
                return[ SlotSet("amount-of-money", None),
                        ]
        else:
            # print("4")
            if(int(amount)<=0):
                # print("5")
                dispatcher.utter_message(response="utter_invalidAMOUNT")
                return {"amount-of-money": None}
            else:
                # account = db_manager.set_slot_value(tracker.sender_id, 'amount-of-money', amount)
                print("Amount is ", amount)
                return {"amount-of-money": amount}

class ResetACNumber(Action):
    """action_reset_account_number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_account_number"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("Reset Slot Function Called.")
        return[
                SlotSet("account_number", None),
            ]
class ResetPIN(Action):
    """action_reset_PIN"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_PIN"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        print("Reset Slot Function Called.")
        return[
                SlotSet("PIN", None),
            ]

class ResetPINandACnumer(Action):
    """action_reset_PINandACnumer"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_PINandACnumer"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        print("Reset AC number and PIN Function Called.")
        # return[
        #         SlotSet("PIN", None),
        #         SlotSet("account_number", None),
        #     ]
        return[
                SlotSet("PIN", None),
            ]

class AffirmOrDenyACNumber(Action):
    """action_check_AC_Number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_AC_Number"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["account_number"] = None
            print(tracker.slots["account_number"])
            print(tracker.latest_message['intent'].get('name'))
            # return [FollowupAction('card_bill_form_c_number')]
            return [SlotSet("account_number", None), Form("check_Balance_ACnum_form")]

class ActionACnumber(FormValidationAction):
    """validate_check_Balance_ACnum_form"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_check_Balance_ACnum_form"

    async def validate_account_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        print("validate_account_number")
        ac = tracker.get_slot("account_number")
        print("AC Number is : ", ac)
        
        #BANGLA Check Here
        if (not is_ascii(ac)):  #If Bangla then enter here. is_ascii(otp) True for English
            cn = None
            if ac.isnumeric():
                cn = BnToEn(ac)
                print(str(cn))
                ac = str(cn)
                print("account Number is ", ac)
                tracker.slots["account_number"] = ac
                if len(ac)!=8 or ac == None:
                    dispatcher.utter_message(response="utter_invalidACNumber")
                    return {"account_number": None}
                else:
                    print("Correct account Number")
                    account = db_manager.set_slot_value(tracker.sender_id, "account_number", ac)
                    # return {"account_number": ac}
                    return [SlotSet("account_number", ac), FollowupAction('action_tell_ACNumber')]
        else:
            if len(ac)!=8 or ac == None:
                dispatcher.utter_message(response="utter_invalidACNumber")
                return {"account_number": None}
            else:
                print("Correct account Number")
                # if tracker.get_slot('account_number') in domain['slots']['account_number']['value']:
                #     return [SlotSet("account_number", ac), FollowupAction('action_tell_ACNumber'), SlotSet("account_check","False")]
                # account = db_manager.set_slot_value(tracker.sender_id, "account_number", ac)
                # return {"account_number": ac}
    
                return [SlotSet("account_number", ac), FollowupAction('action_tell_ACNumber')]

class ActionTellACnumber(Action):

    def name(self) -> Text:
        return "action_tell_ACNumber"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # tell_ACNumber = next(tracker.get_latest_entity_values("account_number"), None)
        tell_ACNumber = tracker.get_slot("account_number")
        check = True
        if tracker.get_slot("account_check")=="False":
            check = False
        number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        if(tell_ACNumber!=None):
            wr=''
            for c in tell_ACNumber:
                wr=wr+' '+number[int(c)]

        wr2 = wr.split(" ")
        for i in range(len(wr2)):
            wr2[i] = wr2[i]+","
        wr = ' '.join(wr2)
        if not tell_ACNumber:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []
        
        msg = f"আপনি বলেছেন, {wr} । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        wr_r=wr.split(',') # reverse text for last 3 digit
        else_msg = f"লাস্ট ডিজিট {wr_r[-4:-1]} কি আপনার একাউন্ট নাম্বার। ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {wr}, '। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        print(check)
        print(type(check))
        if check:
            dispatcher.utter_message(text=msg)
            return [SlotSet("account_check","False")]
        else:
            dispatcher.utter_message(text=else_msg)
            return []

class AffirmOrDenyPIN(Action):
    """action_check_PIN"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_PIN"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["PIN"] = None
            print(tracker.slots["PIN"])
            print(tracker.latest_message['intent'].get('name'))
            return [SlotSet("PIN", None), Form("check_Balance_PIN_form")]

class ActionAccountCnumber(FormValidationAction):
    """validate_check_Balance_PIN_form"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_check_Balance_PIN_form"

    async def validate_PIN(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        print("validate_PIN")
        pin = tracker.get_slot("PIN")
        print("PIN Number is : ", pin)
        
        #BANGLA Check Here
        if (not is_ascii(pin)):  #If Bangla then enter here. is_ascii(otp) True for English
            cn = None
            if pin.isnumeric():
                cn = BnToEn(pin)
                print(str(cn))
                pin = str(cn)
                print("pin Number is ", pin)
                tracker.slots["PIN"] = pin
                if len(pin)!=4 or pin == None:
                    dispatcher.utter_message(response="utter_invalidPIN")
                    return {"PIN": None}
                else:
                    print("Correct pin Number")
                    # account = db_manager.set_slot_value(tracker.sender_id, "PIN", pin)
                    return {"PIN": pin}
        else:
            if len(pin)!=4 or pin == None:
                dispatcher.utter_message(response="utter_invalidPIN")
                return {"PIN": None}
            else:
                print("Correct pin Number")
                # account = db_manager.set_slot_value(tracker.sender_id, "PIN", pin)
                return {"PIN": pin}

class ActionShowBalance(Action):
    """Shows the balance of bank or credit card accounts"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_show_balance"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        """Executes the custom action"""
        account_type = tracker.get_slot("account_type")

        if account_type == "credit":
            # show credit card balance
            credit_card = tracker.get_slot("credit_card")
            available_cards = profile_db.list_credit_cards(tracker.sender_id)

            if credit_card and credit_card.lower() in available_cards:
                current_balance = profile_db.get_credit_card_balance(
                    tracker.sender_id, credit_card
                )
                dispatcher.utter_message(
                    response="utter_credit_card_balance",
                    **{
                        "credit_card": credit_card.title(),
                        "credit_card_balance": f"{current_balance:.2f}",
                    },
                )
            else:
                for credit_card in profile_db.list_credit_cards(tracker.sender_id):
                    current_balance = profile_db.get_credit_card_balance(
                        tracker.sender_id, credit_card
                    )
                    dispatcher.utter_message(
                        response="utter_credit_card_balance",
                        **{
                            "credit_card": credit_card.title(),
                            "credit_card_balance": f"{current_balance:.2f}",
                        },
                    )
        else:
            # show bank account balance
            # account_balance = profile_db.get_account_balance(tracker.sender_id)
            account_balance=106000
            account_balance=str(int(account_balance))
            amount = tracker.get_slot("amount_transferred")
            if amount:
                amount = float(tracker.get_slot("amount_transferred"))
                init_account_balance = account_balance + amount
                dispatcher.utter_message(
                    response="utter_changed_account_balance",
                    init_account_balance=f"{init_account_balance:.2f}",
                    account_balance=f"{account_balance:.2f}",
                )
            else:
                bangla_numeric_string = bangla.convert_english_digit_to_bangla_digit(account_balance)
                print(bangla_numeric_string)

                account_balance=num_convert.number_to_bangla_words(bangla_numeric_string)
                dispatcher.utter_message(
                    response="utter_account_balance",
                    init_account_balance=account_balance,
                )

        events = []
        active_form_name = tracker.active_form.get("name")
        if active_form_name:
            # keep the tracker clean for the predictions with form switch stories
            events.append(UserUtteranceReverted())
            # trigger utter_ask_{form}_AA_CONTINUE_FORM, by making it the requested_slot
            #events.append(SlotSet("AA_CONTINUE_FORM", None))
            # avoid that bot goes in listen mode after UserUtteranceReverted
            events.append(FollowupAction(active_form_name))

        return events


class ActionTellPIN(Action):

    def name(self) -> Text:
        return "action_tell_pin"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tell_pin = next(tracker.get_latest_entity_values("PIN"), None)
        number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        if(tell_pin!=None):
            wr=''
            for c in tell_pin:
                wr=wr+' '+number[int(c)]
        
        wr2 = wr.split(" ")
        for i in range(len(wr2)):
            wr2[i] = wr2[i]+","
        wr = ' '.join(wr2)
    
        if not tell_pin:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"আপনি বলেছেন, {wr} । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {wr}, '। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        dispatcher.utter_message(text=msg)
        return []

class ResetBkashTransectionVALUES(Action):
    """action_reset_BkashTransectionVALUES"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_BkashTransectionVALUES"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("Reset bKash related info.")
        # return[
        #         SlotSet("phone_number", None),
        #         SlotSet("account_number", None),
        #         SlotSet("amount-of-money", None),
        #     ]
        return[
                SlotSet("phone_number", None),
                SlotSet("amount-of-money", None),
            ]
class ActionValidatePhoneNumber(FormValidationAction):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_phone_number_form"

    async def validate_phone_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        
        print("validate_phone_number")
        phone = tracker.get_slot("phone_number")
        print("phone Number is : ", phone)
        
        #BANGLA Check Here
        if (not is_ascii(phone)):  #If Bangla then enter here. is_ascii(otp) True for English
            cn = None
            if phone.isnumeric():
                cn = BnToEn(phone)
                print(str(cn))
                phone = str(cn)
                print("phone Number is ", phone)
                tracker.slots["phone_number"] = phone
                if len(phone)!=11 or phone == None:
                    dispatcher.utter_message(response="utter_invalidphone")
                    return {"phone_number": None}
                else:
                    print("Correct phone Number")
                    # account = db_manager.set_slot_value(tracker.sender_id, "phone_number", phone)
                    return {"phone_number": phone}
        else:
            if len(phone)!=11 or phone == None:
                dispatcher.utter_message(response="utter_invalidphone")
                return {"phone_number": None}
            else:
                print("Correct phone Number")
                # account = db_manager.set_slot_value(tracker.sender_id, "phone_number", phone)
                return {"phone_number": phone}

class ActionTellphone(Action):

    def name(self) -> Text:
        return "action_tell_PhoneNumber"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
            
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        tell_phone = next(tracker.get_latest_entity_values("phone_number"), None)
        number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        if(tell_phone!=None):
            wr=''
            for c in tell_phone:
                wr=wr+' '+number[int(c)]

        wr2 = wr.split(" ")
        for i in range(len(wr2)):
            wr2[i] = wr2[i]+","
        wr = ' '.join(wr2)

        if not tell_phone:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"আপনি বলেছেন, {wr} । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {wr}, '। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        dispatcher.utter_message(text=msg)
        return []

class AffirmOrDenyPhoneNumber(Action):
    """action_check_phone_Number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_phone_Number"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check phone Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["phone_Number"] = None
            print(tracker.slots["phone_Number"])
            print(tracker.latest_message['intent'].get('name'))
            # return [FollowupAction('card_bill_form_c_number')]
            return [SlotSet("phone_Number", None), Form("phone_number_form")]

class ActionTellamount(Action):

    def name(self) -> Text:
        return "action_tell_Amount"

    def run(
            self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        tell_amount = next(tracker.get_latest_entity_values("amount-of-money"), None)

        bangla_numeric_string = bangla.convert_english_digit_to_bangla_digit(tell_amount)
        print(bangla_numeric_string)
        print(type(bangla_numeric_string))
        print('bangla_numeric_string: ', len(str(bangla_numeric_string)))
        if(len(str(bangla_numeric_string))>8):
            account=bangla_numeric_string
        else:
            account = num_convert.number_to_bangla_words(bangla_numeric_string)
        # number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        # if(tell_amount!=None):
        #     wr=''
        #     for c in tell_amount:
        #         wr=wr+' '+number[int(c)]

        if not tell_amount:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"আপনি বলেছেন, {account} টাকা। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {account}, 'টাকা। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        dispatcher.utter_message(text=msg)
        return []

class AffirmOrDenyAmount(Action):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_amount"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check amount Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["amount-of-money"] = None
            print(tracker.slots["amount-of-money"])
            print(tracker.latest_message['intent'].get('name'))
            # return [FollowupAction('card_bill_form_c_number')]
            return [SlotSet("amount-of-money", None), Form("card_bill_form_amount")]

class ResetPINandCARDnumer(Action):
    """action_reset_PINandCARDnumer"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_PINandCARDnumer"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        global UserText
        print(tracker.latest_message['intent'].get('name'))
        UserText = tracker.latest_message.get('text')
        print(f"User Input: {UserText}")
        """Executes the action"""
        print("Reset AC number and PIN Function Called.")
        return[
                SlotSet("PIN", None),
                SlotSet("card_number", None),
            ]
class ActionTellCardNumber(Action):

    def name(self) -> Text:
        return "action_tell_CardNumber"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        tell_card = next(tracker.get_latest_entity_values("card_number"), None)
        number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        if(tell_card!=None):
            wr=''
            for c in tell_card:
                wr=wr+' '+number[int(c)]

        wr2 = wr.split(" ")
        for i in range(len(wr2)):
            wr2[i] = wr2[i]+","
        wr = ' '.join(wr2)
        
        if not tell_card:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"আপনি বলেছেন, {wr} । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {wr}, '। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        dispatcher.utter_message(text=msg)
        return []

counter=0
class OutOfScope(Action):
    """Action_out_of_scope"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "Action_out_of_scope"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        global counter
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("out_of_scope")
        Input = tracker.latest_message.get('text')
        print(f"User Input was:{Input}")
        print(type(Input))
        if(counter>1):
            dispatcher.utter_message(response="utter_AT")
            counter=0
            return []
            
        if tracker.latest_message['intent'].get('name') == "out_of_scope":
            counter=counter+1
            if "কি মেয়ে নাকি ছেলে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_1")
            elif "ঘুরতে যাবে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_2")
            elif "তোমার প্রেমে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_3")
            elif "বিবাহিত" in Input or "বিয়ে" in Input or "অবিবাহিত" in Input or "আনমেরিড" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_4")
            elif "দিনটা কেমন" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_5")
            elif "কি বুদ্ধিমান" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_6")
            elif "প্রিয় পিকআপ লাইন" in Input or "পিকআপ লাইন" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_7")
            elif "কখনো প্রেমে পরেছ" in Input or "প্রেমে পরেছ" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_8")
            elif "আজকে জন্মদিন" in Input or "জন্মদিন" in Input or "বার্থডে" in Input or "জন্মদিন আজকে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_9")
            elif "এলিয়েন" in Input or "এলিয়েন কি সত্যি" in Input or "মহাজাগতিক প্রানী" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_10")
            elif "সিরি" in Input or "সিরি কে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_Siri")
            elif "করটানা" in Input or "কর্টানা" in Input or "করটানা কে" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_Cortana")
            elif "আলেক্সা" in Input or "এলেক্সা কে" in Input or "আলেক্সা কে" in Input or "এলেক্সা" in Input:
                dispatcher.utter_message(response="utter_Out_of_scope_funny_Alexa")
            else:
                dispatcher.utter_message(response="utter_out_of_scope")
        else:
            dispatcher.utter_message(response="utter_default")
        
        return []

class CreditCardLimitInformation(Action):
    """Action_Card_limit_info"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "Action_Card_limit_info"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        global UserText
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print(f"User Input was:{UserText}")
        print(type(UserText))
        if "লিমিট" in UserText:
            dispatcher.utter_message(response="utter_card_limit")
        elif "কার্ড ব্যালেন্স" in UserText or "ব্যালেন্স" in UserText or "এভেইলেবল এমাউন্ট" in UserText:
            dispatcher.utter_message(response="utter_card_balance")
        elif "আউটস্টেন্ডং" in UserText or "খরচ" in UserText or "ডিউ" in UserText or "বিল" in UserText:
            dispatcher.utter_message(response="utter_card_outstanding")
        else:
            dispatcher.utter_message(response="utter_card_info")
            return []

class actionDateTime(Action):
    """Action_Current_DateTime"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "Action_Current_DateTime"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        text = tracker.latest_message.get('text')
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print(f"User Input was:{text}")
        months = ["জানুয়ারি", "ফেব্রুয়ারী", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগষ্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
        today = date.today()
        now = datetime.datetime.now()
        DATE = today.strftime("%B %d, %Y")
        print("DATE =", DATE)
        year = today.strftime("%Y")
        Y = bangla.convert_english_digit_to_bangla_digit(str(year))
        Y = num_convert.number_to_bangla_words(Y)
        print(Y)
        month = today.strftime("%m")
        month = int(month) - 1
        print("before loop month: ", month)
        Mon = months[month]
        print(Mon)
        day = today.strftime("%d")
        D = bangla.convert_english_digit_to_bangla_digit(str(day))
        D = num_convert.number_to_bangla_words(D)
        print(D)
        print(f"Year: {year}, month: {month}, day: {day}")
        time = now.strftime("%H:%M:%S")
        print("time =", time)

        hour = now.strftime("%H")
        minutes = now.strftime("%M")

        print (f"hour: {hour} and minute: {minutes}")
        if(int(hour)>12):
            hour=str(int(hour) - 12)
        H = bangla.convert_english_digit_to_bangla_digit(str(hour))
        hour = num_convert.number_to_bangla_words(H)
        M = bangla.convert_english_digit_to_bangla_digit(str(minutes))
        Minutes = num_convert.number_to_bangla_words(M)
        
        

        d_msg = f"আজকের তারিখ হচ্ছে, {D}, {Mon}, {Y} ।"
        msg = f"এখন সময়, {hour} টা বেজে {Minutes} মিনিট।"
        message = f"এখন সময়, {hour} টা বেজে {Minutes} মিনিট। আজকের তারিখ হচ্ছে, {D}, {Mon}, {Y} ।"
        dispatcher.utter_message(text = message)

        if "তারিখ" in text:
            pass
            # dispatcher.utter_message(text = d_msg)
        if "সময়" in text:
            pass
            # dispatcher.utter_message(response="utter_card_balance")
        # else:
        #     dispatcher.utter_message(response="utter_card_info")
        
        return []

class ActionChequeNumber(FormValidationAction):
    """validate_cheque_form"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_cheque_form"

    async def validate_cheque_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        active_loop = tracker.active_loop.get('name')
        print(f"active loop is, {active_loop}")
        SLT = tracker.slots.get('name')
        print(f"the rasa is requesting for {SLT}")
        
        print("validate_cheque_number")
        cheque = tracker.get_slot("cheque_number")
        print("cheque Number is : ", cheque)
        
        #BANGLA Check Here
        if (not is_ascii(cheque)):  #If Bangla then enter here. is_ascii(otp) True for English
            cn = None
            if cheque.isnumeric():
                cn = BnToEn(cheque)
                print(str(cn))
                cheque = str(cn)
                print("cheque Number is ", cheque)
                tracker.slots["cheque_number"] = cheque
                if len(cheque)!=6 or cheque == None:
                    dispatcher.utter_message(response="utter_invalidCHEQUEnumber")
                    return {"cheque_number": None}
                else:
                    print("Correct cheque Number")
                    # account = db_manager.set_slot_value(tracker.sender_id, "cheque_number", cheque)
                    return [SlotSet("cheque_number", cheque), FollowupAction('action_tell_ChequeNumber')]
        else:
            if len(cheque)!=6 or cheque == None:
                dispatcher.utter_message(response="utter_invalidCHEQUEnumber")
                return {"cheque_number": None}
            else:
                print("Correct cheque Number")
                # account = db_manager.set_slot_value(tracker.sender_id, "cheque_number", cheque)
                return [SlotSet("cheque_number", cheque), FollowupAction('action_tell_ChequeNumber')]

class ActionTellChequeNumber(Action):

    def name(self) -> Text:
        return "action_tell_ChequeNumber"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tell_ACNumber = next(tracker.get_latest_entity_values("cheque_number"), None)
        
        number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
        if(tell_ACNumber!=None):
            wr=''
            for c in tell_ACNumber:
                wr=wr+' '+number[int(c)]

        wr2 = wr.split(" ")
        for i in range(len(wr2)):
            wr2[i] = wr2[i]+","
        wr = ' '.join(wr2)
        if not tell_ACNumber:
            msg = f"দুঃখিত, আপনার কথাটি বুঝতে পারিনি ।"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"আপনি বলেছেন, {wr} । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।"
        print('আপনি বলেছেন,', {wr}, '। সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।')
        dispatcher.utter_message(text=msg)
        return []

class AffirmOrDenyCHEQUE(Action):
    """action_check_Cheque_Number"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_check_Cheque_Number"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        """Executes the action"""
        print("response check Function Called.")

        if tracker.latest_message['intent'].get('name') == "affirm":
            print("Got, Yes")
            print(tracker.latest_message['intent'].get('name'))
        if tracker.latest_message['intent'].get('name') == "deny":
            tracker.slots["cheque_number"] = None
            print(tracker.slots["cheque_number"])
            print(tracker.latest_message['intent'].get('name'))
            return [SlotSet("cheque_number", None), Form("cheque_form")]

class ResetChequeANDamount(Action):
    """action_reset_ChequeANDamount"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_reset_ChequeANDamount"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        print("Reset Cheque number and amount-of-money Function Called.")
        return[
                SlotSet("cheque_number", None),
                SlotSet("amount-of-money", None),
            ]

class ActionCard_Activation(Action):
    """action_Card_Activation"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_Card_Activation"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        # dispatcher.utter_message(response="utter_card_activation")
        return[
            SlotSet("Father_Name", None),
            SlotSet("Mother_Name", None),
            SlotSet("Birth_Date", None),
        ]
class E_Commerce_Request(Action):
    """action_E_Commerce_Request"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_E_Commerce_Request"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        # dispatcher.utter_message(response="utter_E_Commerce_Request")
        return[
            SlotSet("Father_Name", None),
            SlotSet("Mother_Name", None),
            SlotSet("Birth_Date", None),
        ]

class ActionCard_Close(Action):
    """action_Card_Close"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_Card_Close"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print(tracker.latest_message['intent'].get('name'))
        """Executes the action"""
        # dispatcher.utter_message(response="utter_Card_Close")
        return[
            SlotSet("card_number", None),
            SlotSet("Father_Name", None),
            SlotSet("Mother_Name", None),
            SlotSet("Birth_Date", None),
        ]

class ActionGetParentsName(FormValidationAction):
    """validate_get_parents_name_form"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_get_parents_name_form"

    async def validate_Father_Name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        active_loop = tracker.active_loop.get('name')
        print(f"active loop is, {active_loop}")
        SLT = tracker.slots.get('name')
        print(f"the rasa is requesting for {SLT}")
        
        print("validate_Father_Name")
        Name = tracker.get_slot("Father_Name")
        print("Name is in validate form and it is ", Name)

        #NAME can't be a number
        for character in Name:
            if character.isdigit():
                dispatcher.utter_message(response="utter_invalidNAME")
                return [SlotSet("Father_Name", None)]
        if Name!=None:
            if (len(Name) < 4):
                dispatcher.utter_message(response="utter_invalidNAME")
                return {"Father_Name": None}
            else:
                return [SlotSet("Father_Name", Name), FollowupAction('')]
        else:
            dispatcher.utter_message(response="utter_invalidNAME")
            return {"Father_Name": None}
    async def validate_Mother_Name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        active_loop = tracker.active_loop.get('name')
        print(f"active loop is, {active_loop}")
        SLT = tracker.slots.get('name')
        print(f"the rasa is requesting for {SLT}")
        
        print("validate_Mother_Name")
        Name = tracker.get_slot("Mother_Name")
        print("Name is in validate form and it is ",Name)

        #USERNAME can't be a number
        for character in Name:
            if character.isdigit():
                dispatcher.utter_message(response="utter_invalidNAME")
                return [SlotSet("Mother_Name", None)]
        if Name!=None:
            if (len(Name) < 4):
                dispatcher.utter_message(response="utter_invalidNAME")
                return {"Mother_Name": None}
            else:
                return [SlotSet("Mother_Name", Name), FollowupAction('')]
        else:
            dispatcher.utter_message(response="utter_invalidNAME")
            return {"Mother_Name": None}

class ActionGetBirthDate(FormValidationAction):
    """validate_Birthdate_form"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "validate_Birthdate_form"

    async def validate_Birth_Date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
    
        """Executes the action"""
        print(tracker.latest_message['intent'].get('name'))
        print(tracker.latest_message['intent']['confidence'])
        active_loop = tracker.active_loop.get('name')
        print(f"active loop is, {active_loop}")
        SLT = tracker.slots.get('name')
        print(f"the rasa is requesting for {SLT}")
        
        print("validate_Birth_Date")
        Bdate = tracker.get_slot("Birth_Date")
        print("Name is in validate form and it is ", Bdate)

        if Bdate!=None:
            return [SlotSet("Birth_Date", Bdate), FollowupAction('')]
        else:
            dispatcher.utter_message(response="utter_invalidBDATE")
            return {"Birth_Date": None}

class ActionGreet(Action):
    """action_greet"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_greet"
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        currentTime = datetime.datetime.now()
        currentTime.hour

        if 3<= currentTime.hour < 12:
           print('Good morning.')
           dispatcher.utter_message(response="utter_greet_morning")
        elif 12 <= currentTime.hour < 17:
            print('Good afternoon.')
            dispatcher.utter_message(response="utter_greet_afternoon")
        elif 17 <= currentTime.hour < 19:
            print('Good evening.')
            dispatcher.utter_message(response="utter_greet_evening")
        elif 19 <= currentTime.hour < 3:
            print('Good night.')
            dispatcher.utter_message(response="utter_greet_night")
        else:
            print('Good unknown time.')
            dispatcher.utter_message(response="utter_greet")

        return []

