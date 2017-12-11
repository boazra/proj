# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 22:48:39 2017

@author: Boaz
"""
import numpy as np
import gdax
import time

def Calculate_action(history):
    pass
    #use agents...
    
key = 'key'
b64secret = 'secret'
passphrase = 'pass'

gdax_client = gdax.PublicClient()
my_client = gdax.authenticated_client(key, b64secret, passphrase,)

account_id = 'id'
my_account = my_client.get_account(account_id)
History = gdax_client.get_product_historic_rates('BTC-USD')
time_start = time.clock()
counter = 0
usd = 0
btc = 0

start_time = time.clock()

while True:
    Current_price = gdax_client.get_product_ticker('BTC-USD')['price']    
    action = Calculate_action(History,Current_price)
    if action == 1:        
        for balance in my_client.get_account(account_id):
            if balance['currency'] == 'USD':
                usd = balance['available']
                
        order = {
        'funds': np.round(usd,2),        
        'side': 'buy',
        'product_id': 'BTC-USD',
        'type' : 'market'}
        my_client.buy(order)              
        
    if action == -1:
        for balance in my_client.get_account(account_id):
            if balance['currency'] == 'BTC':
                btc = balance['available']        
        order = {
        'size': np.round(btc,2),        
        'side': 'sell',
        'product_id': 'BTC-USD',
        'type' : 'market'}
        my_client.sell(order)
            
    if time.clock() - start_time > 60:
        start_time = time.clock()
        History.append(Current_price)
        History.remove(History[0])
    
    time.sleep(5) 
    if counter > 12:
        History = gdax_client.get_product_historic_rates('BTC-USD')
        counter = 0
    
    