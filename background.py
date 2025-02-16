from flask import Flask
from flask import request
from threading import Thread
import time
import requests
import logging

app = Flask('')

@app.route('/')
def home():
    logging.info(f"Запрос получен: {request.method} от {request.remote_addr}")
    return "bot online"

def run():
  app.run(host='0.0.0.0', port=8000)

def keep_alive():
  t = Thread(target=run)
  t.start()