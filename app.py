import os
import datetime
import logging
import uuid
import socketio
from aiohttp import web
from rasa_sdk.executor import ActionExecutor
from rasa_sdk.interfaces import ActionExecutionRejection

import bangla
from banglanum2words import num_convert

import json
import pprint          
                                           
import sys
sys.path.append('.')

ASK_PIN='আপনার চার ডিজিটের টি পিন নাম্বার বলুন'
ASK_PHONE ='আপনার এগার সংখ্যার ফোন নাম্বার বলুন'
ASK_MONEY='টাকার পরিমাণ বলুন'
ASK_OK='ঠিক আছে'
ASK_CARD = 'আপনার দশ ডিজিট এর কার্ড নাম্বার বলুন'

from utils.bot_factory import BotFactory

from utils.converter import BnToEn_Word, BnToEn

logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


# Action executor config
executor = ActionExecutor()
executor.register_package('actions')


# Load JS File
async def js(request):
    return web.FileResponse('templates/index.js')
    
    
# Home page
async def index(request):
    index_file = open('templates/index.html')
    print(request)
    return web.Response(body=index_file.read().encode('utf-8'), headers={'content-type': 'text/html'})              
        
def isASCII(data):
    try:
        data.encode().decode('ASCII')
    except UnicodeDecodeError:
        return False
    else:
        return True
        
def getNumber(string):
    number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
    st=string.split(' ')
    wr=''
    #for i,w in enumerate(st):
    #    if(w in number):            
    #        wr=wr+str(number.index(w))
    #else:
    #    wr=wr+' '+w
        
    for i,w in enumerate(st):
            for j, n in enumerate(number):
                if(w==n):
                    if(st[i-1]=='ডাবল'):
                        wr=wr+str(j)
                    if(st[i-1]=='ট্রিপল'):
                        wr=wr+str(j)+str(j)
                    wr=wr+str(j)
    print('##############################')
    print(wr)
    if(len(wr)>1):
        #if(len(wr)>4 and len(wr)<=6):
        #    print('########################')
        #    return wr[:4]
        #if(len(wr)>8):
        #    print('########################')
        #    return wr[:8]
        return wr
    else:
      return string
        
# Action endpoint
resposnse_text=['s']
async def webhook(request):
    """Webhook to retrieve action calls."""
    
    try:
    	action_call = await request.json()
    	data = action_call
    except Exception as ex:
    	action_call = await request.post()
    	data = {"sender": '', "message": '', "metadata": ''}
    	for i in action_call:
    		if(i==0):
    			data['sender'] = action_call[i]
    		if(i==1):
    			data['message'] = action_call[i]
    		if(i==2):
    			data['metadata'] = action_call[i]
    	
    print("Request:")
    print(action_call)
    lang='en'
    if(data['metadata']=='en'):
        lang='en'
    else:
        lang='bn'
    

    lang='bn'
    
    number_string=getNumber(data['message'])
    number_string=" ".join(number_string.split())
    print(number_string)
    #number_string=getAmount(number_string)
    #new_number_string=bangla.convert_english_digit_to_bangla_digit(str(number_string))
    global resposnse_text
    
    if(len(number_string)>0):
        data['message']=number_string
             
    
    #for dollar rate manupulation
    if('রেট' in data['message'] or 'ডলার' in data['message'] or 'এক্সচেঞ্জ' in data['message']):
        print('changed text')
        data['message']='আজকে ডলার এর রেট কত'
    #for card limit manupulation
    if('ব্যালেন্স' in data['message'] and 'কার্ড' in data['message']):
        print('changed text')
        data['message']='আমার ক্রেডিট কার্ড এর লিমিট কত টাকা'
    #for OK statement
    if(ASK_OK in data['message']):
        print('changed text')
        data['message']=ASK_OK
    #for PIN manupulation
    if(resposnse_text[-1]==ASK_PIN):
        print('changed text')
        if(len(data['message'])>4):
            data['message']=data['message'][:4]
        data['message']=data['message']+' পিন'
    if(resposnse_text[-1]==ASK_PHONE):
        print('changed text')
        if(len(data['message'])>11):
            data['message']=data['message'][:11]
            print(f"Data {data['message']}.")
        data['message']=data['message']+' ফোন নাম্বার'

    if(resposnse_text[-1]==ASK_MONEY):
        print('changed text')
        data['message']=data['message']+' টাকা'
    
    if(resposnse_text[-1]==ASK_CARD):
        print('changed text')
        if(len(data['message'])>10):
            data['message']=data['message'][:10]
            print(f"Data {data['message']}.")
        data['message']='আমার কার্ড নাম্বার '+data['message']
    try:
        #response = await executor.run(action_call)
        start_time=datetime.datetime.now()
        response = await BotFactory.getOrCreate(lang).handle_text(data['message'],sender_id=data['sender'])
        end_time=datetime.datetime.now()
        if(len(response) > 0):
            f = open("log_voice.txt", "a")
            f.write(str(start_time)+"\t"+str(data['sender'])+"\t"+str(data['message'])+"\n")
            f.write(str(end_time)+"\t"+"Disha\t"+str(response[0]['text'])+"\n")
            f.close()
            #global resposnse_text
            resposnse_text.append(response[0]['text'])
            
            a_dictionary = {"recipient_id" : response[0]['recipient_id'], "text" : response[0]['text'], "cause_code" : ''}
            
            if(resposnse_text[-1]=='আপনাকেও ধন্যবাদ'):
                a_dictionary['cause_code']='230'
                resposnse_text=['s']
            elif(resposnse_text[-1]=='আপনার কল টি এক জন কাস্টমার কেয়ার প্রতিনিধির কাছে ট্রান্সফার করা হচ্ছে'):
                a_dictionary['cause_code']='231'
                resposnse_text=['s']
            else:
                a_dictionary['cause_code']='0'
                
            response[0]=a_dictionary
        print("Response:")
        print(type(response))
        print(response)
    except ActionExecutionRejection as e:
        logger.error(str(e))
        response = {"error": str(e), "action_name": e.action_name}
        response.status_code = 400
        return response

    return web.json_response(response)
    
# Web app routing
app = web.Application()
app.add_routes([
    web.get('/', index),
    web.get('/js', js),
    web.post('/webhooks/rest/webhook', webhook),
    web.static('/static', 'static')
])

# Instantiate all bot agents
bots = BotFactory.createAll()

# Websocket through SocketIO with support for regular HTTP endpoints
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
sio.attach(app)

@sio.on('session_request')
async def on_session_request(sid, data):
    if data is None:
        data = {}
    if 'session_id' not in data or data['session_id'] is None:
        data['session_id'] = uuid.uuid4().hex
    await sio.emit('session_confirm', data['session_id'])

@sio.on('user_uttered')
async def on_user_uttered(sid, message):
    print(sid)
    custom_data = message.get('customData', {})
    lang = custom_data.get('lang', 'en')
    campaign = custom_data.get('campaign', False)
    print('lang: '+lang)
    print('campaign: '+str(campaign))
    
    
    user_message = message.get('message', '')
    print(user_message)
    f = open("log.txt", "a")
    f.write(str(sid)+"\t"+str(user_message)+"\n")
    f.close()
    
    
    number_string=getNumber(user_message)
    if(len(number_string)>0):
        user_message=number_string
        
        
    print("new user message")
    print(user_message)                                
                                           

    bot_responses = await bots[lang].handle_text(user_message,None,None,sid) #await BotFactory.getOrCreate(lang).handle_text(user_message)
    print("Response:")
    print(bot_responses)
    
    tracker = bots[lang].tracker_store.get_or_create_tracker(sid)
    state = tracker.current_state()
    res={"tracker": state}
    
    pp = pprint.PrettyPrinter(width=41, compact=True)
    pp.pprint(res)
      
    for bot_response in bot_responses:
        json = __parse_bot_response(bot_response)
        print(json)
        await sio.emit('bot_uttered', json, room=sid)


def __parse_bot_response(bot_response):
    # Images require a special schema
    if 'image' in bot_response:
        return { 'attachment': { 'type': 'image', 'payload': { 'src': bot_response['image'] }}}
    else:
        if 'buttons' in bot_response:
            # The JS client only shows the buttons when they arrive as 'quick_replies'
            bot_response['quick_replies'] = bot_response['buttons']
            del bot_response['buttons']

        # Remove the 'recipient_id', because the client can't handle it
        return {k: v for k, v in bot_response.items() if not k.startswith('recipient_id')}

def __create_env_js(host, port):
    f = None
    try:
        f = open("static/js/env.js", "w+")
        server_url=os.getenv('API_SERVER_URL', 'http://' + host + ':' + str(port))
        dict = {'serverUrl': server_url}
        f.write('Env=' + repr(dict))
    finally:
        if f is not None:
            f.close()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5004))
    __create_env_js(host, port)
    web.run_app(app, host=host, port=port)
