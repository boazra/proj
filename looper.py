# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 22:48:39 2017

@author: Boaz
"""
import numpy as np
import gdax
import time

def update_price_mat(history,products,currencies,old_prices):     
    result = np.diag(np.ones(len(currencies)))
    for i in range(len(history)):        
        msg = history.pop(0)    
        if not type(msg) is dict:
            continue
        if not ('product_id' and 'price' in msg.keys()):
            continue
        prod = msg['product_id']
        if prod in products:
            old_prices[products.index(prod)] = msg['price']
    
    for i in range(len(products)):
        cur = products[i].split('-')
        result[currencies.index(cur[0]),currencies.index(cur[1])] = old_prices[i]
        result[currencies.index(cur[1]),currencies.index(cur[0])] = 1/old_prices[i]
    return result, old_prices
    
def get_best_loop(prices,currencies,products,money_type=-1):
    if prices.ndim != 2:
        # failed with matrix
        return -1,0,0            
    
    sel = np.array([prices[i,:] * prices[:,j]/prices[i][j] for i in range(len(prices)) for j in range(len(prices))])
    if money_type == -1:        
        max_val = np.nanmax(sel)
        if max_val < 1.01:
            # not interesting enough
            return -2,0,0 
        index = np.unravel_index(np.nanargmax(sel),(len(prices),len(prices),len(prices)))
        p = currencies[index[2]],currencies[index[1]],currencies[index[0]]
    else:
        sel = np.array([prices[i,:] * prices[:,j]/prices[i][j] for i in [money_type] for j in range(len(prices))])
        max_val = np.nanmax(sel)
        if max_val < 1.001:
            # not interesting enough
            return -2,0,0
        index = np.unravel_index(np.nanargmax(sel),(len(prices),len(prices)))
        p = currencies[money_type],currencies[index[1]],currencies[index[0]]
        
    orders = []    
    orders.append([prod for prod in products if p[0] in prod and p[1] in prod][0])
    orders.append([prod for prod in products if p[1] in prod and p[2] in prod][0])
    orders.append([prod for prod in products if p[2] in prod and p[0] in prod][0])    
    return orders,p, max_val
        

def round2(number):
    number_round = np.round(number,2)
    if number_round > number:
        number = number_round - 0.01
    else:
        number = number_round        
        
def calculate_NoFeePrice():
    pass

def get_balance(client, acc_id,currency_name):
    for balance in client.get_account(acc_id):
                    if balance['currency'] ==  currency_name:
                        return round2(balance['available'])
    return 0

def check_prod_in_history(products,history):
    for p in products:
        found = False
        for h in history:
            if not type(h) is dict:
                continue
            if not 'product_id' in h.keys():
                continue
            if h['product_id'] == p:
                found = True
                continue
        if found == False:
            return False
    return True
            
short_history = [0]
#products = ['BTC-USD', 'BTC-EUR','ETH-USD','ETH-BTC', 'ETH-EUR','LTC-USD','LTC-BTC', 'LTC-EUR', ]
products = ['BTC-USD', 'ETH-USD','ETH-BTC', 'LTC-USD','LTC-BTC']
currencies = ['BTC', 'ETH', 'LTC', 'USD']
web_client = gdax.WebsocketClient(mongo_collection=short_history, message_type='subscribe', should_print=False, channels=[{ "name": "ticker", "product_ids": products }])
web_client.start()
time.sleep(10)

Simulation = True
fee = 0

if not Simulation:    
    key = 'key'
    b64secret = 'secret'
    passphrase = 'pass'
    my_client = gdax.authenticated_client(key, b64secret, passphrase,)    
    account_id = 'id'
    my_account = my_client.get_account(account_id)
   
produc_prices = np.ones(len(products))*np.nan
start_time = time.clock()
counter = 0

if Simulation:
    wallet = dict()
    for c in currencies:
        wallet[c] = 0
    wallet['USD'] = 10000

with open('log.txt','a+') as log_file:
    log_file.write('*** Started new run at {0} ***'.format(time.asctime()))
    while True:                
        try:                  
            if not web_client.ws.connected:
                web_client.start()
                time.sleep(5)
            prices_matrix, produc_prices = update_price_mat(short_history,products,currencies,produc_prices)
            prices_matrix[prices_matrix==0] = np.nan
            if sum(np.isnan(np.ravel(prices_matrix))) > 2:
                print('error getting prices')
                time.sleep(5)
                continue
        except:
            print('failed getting current price, trying again')
            time.sleep(5)
            continue
        
        if not Simulation:
            traded_currency = 3 # np.nanargmax([get_balance(my_client,account_id,currencies[i]) * prices[i,0] for i in range(len(currencies))])            
        else:
            traded_currency = 3 #np.nanargmax(np.array([v for v in wallet.values()])*prices[:,0])
        orders,p,max_val = get_best_loop(prices_matrix,currencies,products,traded_currency)
        
        if orders == -1:
            print('price matrix is wrong')
            time.sleep(5)
            continue
        
        if orders == -2:
            print('no good loop found for currency {0}'.format(traded_currency))
            time.sleep(5)
            continue
                
        if not Simulation:       
            currency = orders[0].split('-')[1]            
            available_money = get_balance(my_client,account_id,currency)            
            currency = orders[1].split('-')[0]            
            temp_money = get_balance(my_client,account_id,currency)
            order = {
            'funds': available_money,        
            'side': 'buy',
            'product_id': orders[0],
            'type' : 'market'}
            my_client.buy(order)              
            
            # wait for order to happen                          
            available_money = -1
            while not available_money > temp_money:
                time.sleep(5)                        
                available_money = get_balance(my_client,account_id,currency)            
            currency = orders[2].split('-')[0]            
            temp_money = get_balance(my_client,account_id,currency)
                                         
            order = {
            'size': available_money,        
            'side': 'sell',
            'product_id': orders[1],
            'type' : 'market'}
            my_client.sell(order)
                        
            available_money = -1
            while not available_money > temp_money:
                time.sleep(5)                        
                available_money = get_balance(my_client,account_id,currency)  
            currency = orders[0].split('-')[1]            
            temp_money = get_balance(my_client,account_id,currency)                     
            order = {
            'size': available_money,        
            'side': 'sell',
            'product_id': orders[2],
            'type' : 'market'}
            my_client.sell(order)
                       
            available_money = -1
            while not available_money > temp_money:                
                time.sleep(5)                        
                available_money = get_balance(my_client,account_id,currency)   
            
        else:                 
            
            currency = orders[0].split('-')[1]                    
            row = currencies.index(currency)
            available_money = wallet[currency]
            wallet[currency] = 0
                   
            currency1 = orders[0].split('-')[0]                          
            col = currencies.index(currency1)                        
            wallet[currency1] += (available_money * prices_matrix[row,col])*(1-fee)
            #order_msg = ' Bought {0} of {1} at {2} {3}.'.format(available_money * prices_matrix[row,col], currency1, prices_matrix[row,col], currency )                           
            available_money = wallet[currency1]
            wallet[currency1] = 0
            
            currency2 = orders[2].split('-')[0]             
            row = currencies.index(currency2)
            wallet[currency2] += (available_money * prices_matrix[col,row])*(1-fee)
            #order_msg += ' Bought {0} of {1} at {2} {3}.'.format(available_money * prices_matrix[col,row], currency2, prices_matrix[col,row], currency1 )                           
            available_money = wallet[currency2]
            wallet[currency2] = 0
            
            currency = orders[0].split('-')[1]            
            col = currencies.index(currency)
            wallet[currency] += (available_money * prices_matrix[row,col])*(1-fee)
            #order_msg += ' Bought {0} of {1} at {2} {3}.'.format(available_money * prices_matrix[row,col], currency, prices_matrix[row,col], currency2 )                           
            
            log_text = 'Order : {0}. Prices : {1}. Order profit : {2:.3%}.  Current balance :'.format(p,produc_prices,max_val-1)
            for i in range(len(currencies)):
                log_text += ' {0} = {1}.'.format(currencies[i],wallet[currencies[i]])
            #log_text += order_msg
                
        log_text = "Time is {0}. {1}".format(time.asctime(),log_text)
        log_file.write(log_text + '\n')
        print(log_text)        
        time.sleep(30) 
        
        