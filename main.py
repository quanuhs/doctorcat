import vk_api

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent, VkBotEventType
from MyData import db, client
import json
from User import User
import sqlite3 as sql
import random

from bson.objectid import ObjectId
from config import key, group_id, db_key
from AI import detect_intent_texts



vk = vk_api.VkApi(token=key)
vk._auth_token()
vk.get_api()
longpoll = VkBotLongPoll(vk, group_id)

# f_json = open("json_test.json", "r", encoding='UTF-8', errors='ignore')
# json_answers = json.loads(f_json.read())
# f_json.close()

file = open("buttons.txt", "r", encoding="utf-8")
options = file.read()
file.close()


def msg(user_id, text, keyboard):
    vk.method("messages.send",
              {"user_id": user_id,
               "message": text,
               "keyboard": keyboard,
               "random_id": 0})


def get_button(label, color, payload):
    return {
        "action": {
            "type": "text",
            "payload": json.dumps(payload),
            "label": label
        },
        "color": color
    }

def get_action_button(label, color, payload):
    return {
        "action": {
            "type": "callback",
            "payload": json.dumps(payload),
            "label": label
        },
        "color": color
    }

def create_keyboard(btn, inline, *args):
    keyboard = {
        "inline": inline,
        "buttons": btn
    }

    if len(args) == 1:
        keyboard.update({"one_time": args[0]})

    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))
    return keyboard


def main_keyboard(user):

    if user.notify:
        notify = get_button(get_text("b_notify_on"), "positive", "!notify")
    else:
        notify = get_button(get_text("b_notify_off"), "secondary", "!notify")


    buttons = [
        [get_button(get_text("b_delete"), "negative", "!delete")]
    ]

    return create_keyboard(buttons, False)


def options_keys(user, last_input):
    if last_input == "None":
        msg(user.user_id, get_text("no_selection_found"), None)

    text = options.split("\n")
    if str(last_input).isnumeric():
        last_input = int(last_input) - 1

        if len(text) > last_input >= 0:
            user.update_status('p')

            user.update_additional_status("\n[" + text[last_input] + "]\n")
            res = detect_intent_texts("doctorcat-coka", user_id, [text[last_input]], "ru-RU")
            msg(user.user_id, str(res),  create_keyboard([[get_button(get_text("send_task"), "primary", "!send")]], False))
            return

    buttons = []
    for i in range(len(text)):
        buttons.append([get_button(text[i], "primary", "%s" % (i+1))])

    msg(user.user_id, get_text("chose"), create_keyboard(buttons, True))
    return


def chat_msg(data, is_doctor, text, *args):

    address = ""

    if not is_doctor:
        address = get_text("user") + ' ' + get_text("user_text")
    else:
        address = get_text("specialist")

    if args:
        address = get_text("system")

    if not is_doctor:
        if data["status"] == "vk":
            msg(data["vkID"], address + '\n' + text, create_keyboard([[get_button(get_text("b_end"), "negative", "!drop")]], False))

    else:
        if data["platform"] == "vk":
            msg(data["userID"], address + '\n' + text, None)
        elif data["platform"] == "tg":
            pass

def delete_user(user):
    if user.in_conversation:
        doctors_data = db.doctors.find_one({"_id": user.doctors_id})
        chat_msg(doctors_data, False, get_text("left"), create_keyboard([[get_button("Начать", "primary", "")]], False, True))
    if user.platform == "vk":
        msg(user.user_id, get_text("deleted"), create_keyboard([[get_button("Начать", "positive", "")]], False, True))

    user.delete()
    return

def user_input_handler(request, user, payload):
    request_lower = request.lower()
    payload = str(payload).replace("\"", "")

    if payload != "None":
        command = payload
    else:
        command = request_lower

    if command == "!delete" or request_lower == "!delete":
        delete_user(user)
        return

    if user.in_conversation:
        if user.doctors_id:
            doctors_data = db.doctors.find_one({"_id": user.doctors_id})
            chat_msg(doctors_data, False, event.message.text)
            return

    elif user.status == 'i':
        if command == "!notify":
            user.update_notify(not user.notify)
            if user.notify:
                msg(user.user_id, get_text("notify_on"), main_keyboard(user))
            else:
                msg(user.user_id, get_text("notify_off"), main_keyboard(user))


    elif command == "!test" and user.status == "":
        user.update_status('t')
        #msg(user_id, get_text("instruction_test"), create_keyboard([[get_button(get_text("connect"), "primary", "!problem")]], False, True))
        options_keys(user, payload)

    elif command == "!problem" and user.status == "":
        user.update_status('p')
        msg(user.user_id, get_text("instruction"), None)
        return

    elif command == "!connect" and user.status == 'r':
        user.update_status('i')
        msg(user_id, get_text("get_cozy"), main_keyboard(user))
        user.create_token()
        return

    elif command == "!send" and user.status == 'p':
        if user.additional_status == "":
            msg(user.user_id, get_text("error_null_discr"), None)
            return

        user.update_status('r')
        msg(user.user_id, get_text("bot_sad"),
            create_keyboard([[get_button(get_text("delete_me"), "primary", "!delete")], [get_button(get_text("connect"), "positive", "!connect")]], False))
        return

    elif command == "!accept" and user.status == 'r':
        user.delete()
        return

    elif user.status == 't':
        options_keys(user, payload)
        return

    if user.status == 'p':
        user.update_additional_status(user.additional_status + '\n' + request)
        res = detect_intent_texts("doctorcat-coka", user_id, [str(request)], "ru-RU")
        msg(user.user_id, str(res),  create_keyboard([[get_button(get_text("send_task"), "primary", "!send")]], False))
        return


def get_text(text):
    connect = sql.connect("lang.db")
    q = connect.cursor()
    q.execute("SELECT * FROM language WHERE Script = '%s'" % text.lower())
    res = q.fetchall()

    if len(res) == 0:
        return text
    else:
        return res[random.randint(0, len(res)-1)][1]


if __name__ == '__main__':
    while True:
        try:
            for event in longpoll.listen():
                if event.message:
                    # Проверяем нахождения пользователя у нас в базе данных
                    user_id = event.message.from_id
                    user_data = db.users.find_one({"userID": user_id, "platform": "vk"})
                    doctors_data = db.doctors.find_one({"vkID": str(user_id)})
                    print(doctors_data)

                    if not (doctors_data is None):
                        if doctors_data["patientID"] != "":
                            user_data = db.users.find_one({"_id": ObjectId(doctors_data["patientID"])})
                            print(user_data)
                            if user_data is None:
                                continue

                            patient = User(user_data)
                            print(event.message.payload)
                            if event.message.text.lower() == "!drop" or event.message.payload == "\"!drop\"":
                                msg(user_id, get_text("end"), create_keyboard([[get_button("Начать", "primary", "")]], False))
                                chat_msg(user_data, True, get_text("end"), True)
                                delete_user(patient)
                                continue

                            if patient.status != 'b':
                                patient.update_status('b')
                                patient.update_doctor(doctors_data["_id"])
                                msg(patient.user_id, get_text("connected"), None)
                            else:
                                chat_msg(user_data, True, event.message.text)
                            continue
                        else:
                            chat_msg(doctors_data, False, get_text("no_user_found"), True)

                    if user_data is None:
                        # Если не нашли, то создаём его.
                        db.users.insert_one({
                                        "platform": 'vk',
                                        "userID": user_id,
                                        "status": '',
                                        "additional": "",
                                        "hasTask": False,
                                        "notify": False,
                                        "task": {
                                            "description": "",
                                            "qualifications": "",
                                            "doctorsID": ""
                                        }

                                                })


                        msg(user_id, get_text("greeting"),
                            create_keyboard([[get_button(get_text("b_greeting"), "primary", "!test")]], True))

                    else:

                        # Если нашли, то выполняем действия.

                        request = event.message.text
                        payload = event.message.payload

                        user_input_handler(request, User(user_data), payload)
        except Exception as e:
            print("error", e)
