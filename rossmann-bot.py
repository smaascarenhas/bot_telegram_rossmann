import pandas as pd
import json
import requests
from flask import Flask, request, Response
import os

# constants
TOKEN = '7221309848:AAF83wd8chT5JlAZD_gCqPDRKcn-nLS_s5E'

# Info about the Bot
#https://api.telegram.org/bot7221309848:AAF83wd8chT5JlAZD_gCqPDRKcn-nLS_s5E/getMe 

# get updates
#https://api.telegram.org/bot7221309848:AAF83wd8chT5JlAZD_gCqPDRKcn-nLS_s5E/getUpdates

# Webhook
#https://api.telegram.org/bot7221309848:AAF83wd8chT5JlAZD_gCqPDRKcn-nLS_s5E/setWebhook?url=https://1056-187-49-175-243.ngrok-free.app

# send message
#https://api.telegram.org/bot7221309848:AAF83wd8chT5JlAZD_gCqPDRKcn-nLS_s5E/sendMessage?chat_id=1030549012&text=

def send_message( chat_id, text ):

    url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
    url = url + 'sendMessage?chat_id={}'.format( chat_id ) 

    r = requests.post( url, json={'text': text} )
    print( 'Status Code{}'.format( r.status_code ) )

    return None


def load_dataset( store_id ):
    # loading test dataset
    df10 = pd.read_csv( 'test.csv')
    df_store_raw = pd.read_csv( 'store.csv')

    # merge test dataset + store
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:
        # remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop( 'Id', axis=1 )

        # convert Dataframe to json
        data = json.dumps( df_test.to_dict( orient='records' ) )
    
    else:
        data = 'error'

    return data

def predict( data ):
    # API Call
    url = 'https://test-api-render-dtaf.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post( url, data=data, headers=header)
    print( 'Status Code {}'.format( r.status_code ) )

    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )

    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace( '/', '' )

    try:
        store_id = int( store_id )

    except ValueError:
      
        store_id = 'error'
    
    return chat_id, store_id

# API initialize
app = Flask( __name__ )

@app.route( '/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message( message )

        if store_id != 'error':
            # loading data
            data = load_dataset( store_id )

            if data != 'error':

                # prediction
                d1 = predict( data )
                # calculation
                
                d2 = d1[['store', 'prediction']].groupby( 'store' ).sum().reset_index()

              
                msg = 'A loja número {} irá vender R${:,.2f} nas próximas 6 semanas'.format( 
                            d2['store'].values[0],
                            d2['prediction'].values[0] ) 

                send_message( chat_id, msg )
                return Response( 'Ok', status=200 )

            else:
                send_message( chat_id, 'Loja não disponível' )
                return Response( 'OK', status=200 )

        else:
          send_message( chat_id, 'O ID da loja está errado' )
          return Response( 'OK', status=200 )

    else:
        return '<h1> Rossmann Telegram BOT <h1>'

if __name__ == '__main__':
    port = os.environ.get( 'PORT', 5000 )
    app.run( host='0.0.0.0', port=port )



