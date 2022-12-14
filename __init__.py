from dotenv import load_dotenv
from pathlib import Path
from flask import Flask
from flask_pymongo import PyMongo
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
