from dotenv import load_dotenv
from pathlib import Path
from chat import chatWithBot, getCryptoPrice, getWeather, getCoordinates
import json
from bson import json_util
from bson.objectid import ObjectId
from nltk_utils import tokenize
from flask import request, jsonify
from datetime import datetime
import os
from __init__ import app, users_db, chats_db


replace_words_user = ["lastName", "firstName", "email", "age"]
replace_words_other = ["datetime", "weather"]

months_names = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@app.route('/api/chatbot/', methods=['GET'])
def chatbot():
    # print(msg)
    msg = request.args.get('msg')
    user_id = request.args.get('user_id')
    chat_id = request.args.get('chat_id')
    #  check to see if theres a type in the chat data
    chat = chats_db.find_one({"_id": ObjectId(chat_id)})
    # print('\n chat:', chat)
    if chat['typeAction'] != "false":
        # TODO check if theres a action type in the chat data
        updatedChat = chats_db.update_one({"_id": ObjectId(chat_id)}, {
                                          "$set": {"typeAction": "false"}})
        if chat['typeAction'] == 'weather':
            # print(f"\n{:+>20}")
            print('\n last message',  chat['messages']
                  [len(chat['messages'])-1]['body'][0])
            # search into the db for there conversation get the latest msg which should contain the other users location and search for that location
            chat_msg = chat['messages'][len(chat['messages'])-1]['body'][0]
            # TODO then update the chat to remove the typeAction
            return getWeather(getCoordinates(chat_msg))
        elif chat['typeAction'] == 'crypto':
            # get last msg from chat with the crypto name
            return getCryptoPrice(chat['messages'][len(chat['messages'])-1]['body'][0])
        elif chat['typeAction']['riddle']:
            if msg.lower() == chat['typeAction']['riddle']['riddleAnswer'].lower():
                print('\n user got it correct riddle answer')
                return jsonify(chatWithBot('I know', chat_id))
            else:
                print('\n riddle answer ==> ',
                      chat['typeAction']['riddle']['riddleAnswer'])
                return({'msg': chat['typeAction']['riddle']['riddleAnswer']})
    print("\n++++++++++++++++++++++++++++++ no typeAction")
    reply = chatWithBot(msg, chat_id)
    print(reply)
    if('err' not in reply):
        if "%" in reply['msg']:
            reply['msg'] = formatString(reply['msg'], user_id)
    return jsonify(reply)


def formatString(reply, user_id):
    user = users_db.find_one({"_id": ObjectId(user_id)})
    # print(user['firstName'])
    reply = tokenize(reply)
    # print(reply)
    for word in reply:
        if word == "%":
            del reply[reply.index(word)]
        if word in replace_words_user:
            reply[reply.index(word)] = user[word]
        elif word in replace_words_other:
            if word == replace_words_other[0]:
                now = datetime.now()
                # dd/mm/YY H:M:S
                date_time = now.strftime("%m %d %Y %H:%M:%S")
                month = months_names[int(date_time[0] + date_time[1]) - 1]
                new_time = month + date_time[2:]
                reply[reply.index(word)] = new_time
    reply = " ".join(reply)
    return reply
    # format it on the client side js


def type():
    pass
