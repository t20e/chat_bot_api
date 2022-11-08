from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from flask_pymongo import PyMongo
import os
import json
from bson import json_util
from bson.objectid import ObjectId
from flask import request, jsonify, Flask
import random
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize, stem
import requests
from city_names import cities
from crypto_names import crypto_symbols, cryptos

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


@app.errorhandler(404)
def not_fount(e):
    return jsonify({'err': 404})


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


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as file:
    intents = json.load(file)
FILE = "data.pth"
data = torch.load(FILE)
input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]


model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

noanswer = [
    "Not sure I understand",
    "i dont understand"
]


def chatWithBot(sentence, chat_id):
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)
    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]
    print('\n++++++++++++++ tag:', tag)
    if tag == 'crypto':
        return getCrypto(sentence, chat_id)
    elif tag == 'weather':
        # check if theres a city name from the res msg in the list
        for i, word in enumerate(sentence):
            word = word.lower()
            if(i + 1 != len(sentence)):
                sentence[i+1] = sentence[i+1].lower()
                if f"{word} {sentence[i+1]}" in cities:
                    print(
                        f'\n++++++ ====> seperate words in cities {word} {sentence[i+1]}')
                    return getWeather(getCoordinates(f"{word} {sentence[i+1]}"))
            # check to see if a word is dived into two words such as new york, las vegas etc
            elif word in cities:
                print('here')
                print(f'\n++++++ ====>word in cities {word}')
                return getWeather(getCoordinates(f"{word}"))
            else:
                chat = chats_db.update_one({"_id": ObjectId(chat_id)}, {
                                           "$set": {"typeAction": "weather"}})
                print(chat)
    elif tag == "riddle":
        return getRiddle(chat_id)
    # probibility
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent['tag']:
                return({"msg": f"{random.choice(intent['responses'])}"})
    else:
        return {'err': noanswer[random.randint(0, len(noanswer) - 1)]}


couldnt_fetch = 'sorry i could not fetch that, try entering its full name or symbol instead!'


def getRiddle(chat_id):
    try:
        req = requests.get(os.getenv("RIDDLE_API"))
        res = req.json()
        riddle = res['riddle']
        riddleAnwer = res['answer']
        print('\n riddle:',  riddle, '\nriddle answer:', riddleAnwer)
        # add riddle to type action
        riddleAction = {
            "riddle": {
                "riddleAnswer": riddleAnwer
            }
        }
        chat = chats_db.update_one({"_id": ObjectId(chat_id)}, {
                                   "$set": {"typeAction": riddleAction}})
        return ({'msg': riddle})
    except requests.exceptions.HTTPError as err:
        return({"msg": "sry their was an error fetching that api"})


def getCrypto(sentence, chat_id):
    words = []
    for s in sentence:
        words.append(s.lower())
    # print('\n+++++++++++ words', words)
    crypto = False
    for idx, word in enumerate(words):
        for c_name in cryptos:
            if c_name == word:
                crypto = crypto_symbols[cryptos.index(word)]
                break
        for c_symbol in reversed(crypto_symbols):
            if c_symbol == word:
                crypto = c_symbol
                break
    if crypto == False:
        chat = chats_db.update_one({"_id": ObjectId(chat_id)}, {
            "$set": {"typeAction": "crypto"}})
        return {"msg": couldnt_fetch}
        # put crypto in typeAction
    return getCryptoPrice(crypto)


def getCryptoPrice(crypto):
    orignal = crypto
    crypto = crypto.lower()
    # first check if they spelled the whole name
    if crypto in cryptos:
        crypto = crypto_symbols[cryptos.index(crypto)]
    crypto = crypto.upper()
    crypto = crypto + "USDT"
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" + crypto
    req = requests.get(url).json()
    print('\n+++++++++++++++++++ res\n', req)
    if 'price' not in req:
        return {"msg": couldnt_fetch}
    else:
        return {'msg': f"The price of {orignal} is ${ str(round(float(req['price']), 2))}"}


def getWeather(res):
    print(res, 'res from lambda\n')
    if res[0] == 'err':
        return {'err': "sorry didnt understand you, please try another location"}
    try:
        req = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast?lat={res[1]}&lon={res[0]}&appid={os.getenv('WEATHER_APP_API_KEY')}")
        res = req.json()
        # print('\n res from get weather api', res)
        # if 'message' in res:
        #     print(res)
        #     return {'msg': "sorry didnt understand you, please try another location"}
        city = res['city']['name']
        weather_type = res['list'][0]['weather'][0]['description']
        temp = round(int(res['list'][0]['main']['temp']) * 1.8 - 459.67)
        # print(city, weather_type, temp)
        return ({"msg": f"The weather in {city} is {weather_type}, the temperate is {temp}°"})
    except requests.exceptions.HTTPError as err:
        return({"err": err})


def getCoordinates(location):
    try:
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
            print(res)
            print('didnt understand word')
            err = ['err']
            return err
        else:
            return req.json()['Results'][0]['Place']['Geometry']['Point']
    except requests.exceptions.HTTPError as err:
        print(err)
        return(err)


if __name__ == '__main__':
    app.run(port=8080)
