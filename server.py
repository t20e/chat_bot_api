from dotenv import load_dotenv
from pathlib import Path
from flask import request, jsonify, render_template, Flask
from chat import chatWithBot
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

replace_words_user = ["lastName", "firstName"]
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


def getCoordinates(location):
    try:

        # url = os.getenv('URL_LAMBDA')
        data = {
            "body": {
                "address": location
            }
        }
        req = requests.get(os.getenv("URL_LAMBDA"), json=data, headers={
                           "Content-Type": "application/json", "x-api-key": os.getenv("API_GATWAY_KEY")})
        res = req.json()
        print('\n++++++++++++++++++++++++++++++RESPONSE')
        if 'message' in res:
            print('didnt understand word')
            print(res)
            return False
        else:
            return req.json()['Results'][0]['Place']['Geometry']['Point']
    except requests.exceptions.HTTPError as err:
        print(err)
        return(err)


def getWeather(res):
    print(res, 'res from lambda\n')
    if res == False:
        return {'msg': "sorry didnt understand you, please try another location"}
    try:
        req = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast?lat={res[1]}&lon={res[0]}&appid={os.getenv('WEATHER_APP_API_KEY')}")
        res = req.json()
        if 'message' in res:
            return {'msg': "sorry didnt understand you, please try another location"}
        city = res['city']['name']
        weather_type = res['list'][0]['weather'][0]['description']
        temp = round(int(res['list'][0]['main']['temp']) * 1.8 - 459.67)
        # print(city, weather_type, temp)
        return jsonify({"msg": f"The weather in {city} is {weather_type}, the temperate is {temp}°"})
    except requests.exceptions.HTTPError as err:
        return(err)


@app.route('/api/chatbot/', methods=['GET'])
def chatbot():
    # print(msg)
    msg = request.args.get('msg')
    user_id = request.args.get('user_id')
    chat_id = request.args.get('chat_id')
    #  check to see if theres a type in the chat data
    chat = chats_db.find_one({"_id": ObjectId(chat_id)})
    if chat['typeAction'] != "false":
        if chat['typeAction'] == 'weather':
            # search into the db for there conversation get the latest msg which should contain the other users location and search for that location
            return getWeather(getCoordinates(msg))
        elif chat['typeAction'] == 'time':
            pass
    print("\n++++++++++++++++++++++++++++++ no typeAction")
    reply = chatWithBot(msg)
    print(reply)
    if "%" in reply:
        reply = formatString(reply, user_id)
    return jsonify({'msg': reply})


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
    app.run(port=8000, debug=True)
