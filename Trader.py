# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 22:48:39 2017

@author: Boaz
"""
import numpy as np
import gdax
import time

def round2(number):
    number_round = np.round(number,2)
    if number_round > number:
        number = number_round - 0.01
    else:
        number = number_round
        
def Calculate_action(history, Current_Price,dt = 27,threshold_up = 0.01,threshold_down = 0.005,peak_width = 0,valley_width = 0):
    dx = Current_Price/ history[dt]
    # flag up or down trend if:
    # 1. ratio with earlier price crosses threshold
    # 2. prices are rising/falling for at least [peak_width]/[valley_width] minutes
    up = dx >= 1+threshold_up
    down = dx <= 1-threshold_down    
    # Encode actions
    actions = (up+0-down)  
    return actions

def calculate_NoFeePrice():
    pass
    

Simulation = True

if not Simulation:    
    key = 'key'
    b64secret = 'secret'
    passphrase = 'pass'
    my_client = gdax.authenticated_client(key, b64secret, passphrase,)    
    account_id = 'id'
    my_account = my_client.get_account(account_id)
    

gdax_client = gdax.PublicClient()
History = [H[4] for H in gdax_client.get_product_historic_rates('BTC-USD')]

start_time = time.clock()
counter = 0
usd = 0
btc = 0

if Simulation:
    btc = 0.5724704676797485

with open('log.txt','a+') as log_file:
    log_file.write('*** Started new run at {0} ***'.format(time.asctime()))
    while True:
        try:        
            Current_price = float(gdax_client.get_product_ticker('BTC-USD')['price'])
        except:
            print('failed getting current price, trying again')
            time.sleep(5)
            continue
        action = Calculate_action(History,Current_price)    
        if action == 1:
            if not Simulation:        
                for balance in my_client.get_account(account_id):
                    if balance['currency'] == 'USD':
                        usd = round2(balance['available'])                
                order = {
                'funds': usd,        
                'side': 'buy',
                'product_id': 'BTC-USD',
                'type' : 'market'}
                my_client.buy(order)              
            else:
                btc = btc + usd/Current_price
                usd = 0
                
        if action == -1:
            if not Simulation:
                for balance in my_client.get_account(account_id):
                    if balance['currency'] == 'BTC':
                        btc = round2(balance['available'])
                order = {
                'size': btc,        
                'side': 'sell',
                'product_id': 'BTC-USD',
                'type' : 'market'}
                my_client.sell(order)
            else:
                usd = usd + btc*Current_price
                btc = 0
        log_text = "Time time is {3}, action was {0} and we now have {1}$ and {2}BTC. Price now is {4} and history ref is {5}, ratio is {6}".format(action,usd,btc,time.asctime(),Current_price,History[27],Current_price/History[27])
        log_file.write(log_text + '\n')
        print(log_text)
        if time.clock() - start_time > 60:
            start_time = time.clock()
            History.append(Current_price)
                    
        time.sleep(10) 
        counter += 1
        if counter > 12:
            try:
                History = [H[4] for H in gdax_client.get_product_historic_rates('BTC-USD')]                
                counter = 0
                print('updated history')
            except:
                print('Failed update history')
            
        
        