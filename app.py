from email.mime import audio
from flask import Flask, send_file, request
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage
import requests
from pydub import AudioSegment
import speech_recognition as sr
import openai

def trans_wav_to_text(filepath):
    r = sr.Recognizer()
    with sr.WavFile(filepath) as source:
        audio = r.record(source)
    return r.recognize_google(audio,language="zh-TW")
        

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_SECRET_KEY')



@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # send a request to the ChatGPT API
    # openai.api_key = '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'
    openai.api_key = 'YOUR-API-KEY'
    print(event.message.text)
    MODEL = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": event.message.text},
        ],
        temperature=0,
    )

    print(response)

    # get the response from the ChatGPT API
    chatgpt_response = response

    # send the response back to the user
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=chatgpt_response['choices'][0]["message"]['content'])
    )

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    UserSendAudio = line_bot_api.get_message_content(event.message.id)
    path= './audio/'+ event.source.user_id + '.aac'
    with open(path, 'wb') as fd:
        for chunk in UserSendAudio.iter_content():
            fd.write(chunk)
    s = AudioSegment.from_file(path,"m4a")
    s.export(path[:-3]+"wav",format="wav")
    audio_message = trans_wav_to_text(path[:-3]+"wav")
    MODEL = "gpt-3.5-turbo"
    openai.api_key = 'YOUR-API-KEY'
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": audio_message},
        ],
        temperature=0,
    )

    # send the response back to the user
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response['choices'][0]["message"]['content'])
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)