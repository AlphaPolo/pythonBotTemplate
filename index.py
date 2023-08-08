localhostDebug = False

import json
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models.sources import SourceUser


from history import HistoryManager
from chatgpt import ChatGPT


class FakeValidator(object):

    def __init__(self, channel_secret):
        self.channel_secret = channel_secret.encode('utf-8')

    def validate(self, body, signature):
        return True


chatGpt = ChatGPT()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", ""))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", ""))

if localhostDebug:
    line_handler.parser.signature_validator = FakeValidator("")

app = Flask(__name__)
historyManager = HistoryManager()

# domain root
@app.route('/')
def home():
    return 'Hello, World ChatBot!'

@app.route("/webhook", methods=['POST'])
def callback():
    if localhostDebug:
        signature = ""        
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)
        try:
            line_handler.handle(json.loads(body)["postData"]["contents"], signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'
    else:
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']
        
        # get request body as text
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            line_handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print('handle message')
    text = event.message.text
    if not isinstance(event.source, SourceUser):
        return
    if event.source.user_id is None:
        return
    user_id = event.source.user_id
    historyManager.add_msg(user_id, text)
    history = historyManager.get_msg(user_id)
    gpt_response = chatGpt.ask(event.message.text)
    # gpt_response = text + f" :{len(history)}"
    print(gpt_response)

    if localhostDebug:
        return
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=gpt_response)
    )
    return

if __name__ == "__main__":
    app.run()