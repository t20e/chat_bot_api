from dotenv import load_dotenv
from pathlib import Path
from flask import request, jsonify, render_template, Flask
from chat import chatWithBot, getCryptoPrice, getWeather, getCoordinates
from flask_pymongo import PyMongo
import json
from bson import json_util
from bson.objectid import ObjectId
from nltk_utils import tokenize
import requests
from datetime import datetime
import os

dotenv_path = Path('flask_app/.env')
load_dotenv(dotenv_path=dotenv_path)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = f"mongodb+srv://{os.getenv('DB_USER_NAME')}:{os.getenv('DB_PASSWORD')}@personal-projects-db.3ruyg.mongodb.net/{os.getenv('DB_NAME')}?retryWrites=true&w=majority"


mongo = PyMongo(app)
# print(mongo.db.users)
users_db = mongo.db.users
chats_db = mongo.db.chats

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
    if chat['typeAction'] != "false":
        # TODO check if theres a action type in the chat data
        if chat['typeAction'] == 'weather':
            # print(f"\n{:+>20}")
            print(chat['messages'])
            # search into the db for there conversation get the latest msg which should contain the other users location and search for that location
            return getWeather(getCoordinates(msg))
        elif chat['typeAction'] == 'crypto':
            # get last msg from chat with the crypto name
            pass
    print("\n++++++++++++++++++++++++++++++ no typeAction")
    reply = chatWithBot(msg, chat_id)
    print(reply)
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


if __name__ == '__main__':
    app.run(port=8080, debug=True)
