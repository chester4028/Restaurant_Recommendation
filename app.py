import os
import sys
import json
import client
import template_json
from datetime import datetime
from send_msg import sendtofb
import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    if "text" in messaging_event["message"] :
                        message_text = messaging_event["message"]["text"]  # the message's text
                        message_text = message_text.encode('utf-8').lower()

                        reply = handle_message( message_text, sender_id)

                        if type(reply) == str :
                            send_message( sender_id, reply )
                        else : #template
                            send_template_message( reply )
                        pass

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "text": message_text
        }
    })
    sendtofb(data)

def send_template_message(reply):
    data = json.dumps(reply.template)
    sendtofb(data)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


def handle_message(message_text, recipient_id):

    if u'有空'.encode("utf8") in message_text or u'閒'.encode("utf8") in message_text :
        return '要作什麼呢?'

    if u'出門'.encode("utf8") in message_text :
        return '外面天氣怎麼樣呢?'

    if u'早安'.encode("utf8") in message_text :
        return '早安!'

    if u'天氣'.encode("utf8") in message_text :
        if u'雨'.encode("utf8") in message_text :
            return '下雨路上濕滑，騎車的話要小心!'
        if u'糟'.encode("utf8") in message_text or u'不好'.encode("utf8") in message_text or u'不太好'.encode("utf8") in message_text :
            return '好的 出門要注意安全喔 🙂'
        if u'不錯'.encode("utf8") in message_text or u'普通'.encode("utf8") in message_text or u'可以'.encode("utf8") in message_text or u'好'.encode("utf8") in message_text :
            return '好的 一路順風 🙂'

    if u'不舒服'.encode("utf8") in message_text or u'感冒'.encode("utf8") in message_text :
        return '多多休息，要記得看醫生喔'

    if u'餐廳'.encode("utf8") in message_text or u'吃飯'.encode("utf8") in message_text or u'吃的'.encode("utf8") in message_text or u'吃什麼'.encode("utf8") in message_text or u'午餐'.encode("utf8") in message_text or u'晚餐'.encode("utf8") in message_text:
        rec_result = connect_server(message_text, recipient_id) ;
        restaurant = template_json.Template_json(recipient_id,template_type=1)
        for item in rec_result :
            restaurant.addItem( item['title'], item['picture'], item['picture'], item['address'])
        return restaurant

    return '😵😵不太懂剛剛的話呢'

def connect_server(message_text, recipient_id):
    conn = client.Connect()
    return conn.recommend_request('116534363970746295906', '22.997689, 120.221135')




if __name__ == '__main__':
    app.run(debug=True)
