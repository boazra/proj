
# coding: utf-8

# In[1]:

import glob
import matplotlib.pyplot as plt
import matplotlib.collections as mc
import pandas as pd
import numpy as np

##### Load data

# In[2]:

files = glob.glob("*.csv")
data = None
for f in files:
    if data is None:
        data = pd.read_csv(f, skipfooter = 2, engine='python')
    else:
        data = pd.concat([data, pd.read_csv(f, skipfooter = 2, engine='python')])

data.columns = ['date', 'price']
data = data.drop_duplicates('date')
data = data.reset_index(drop=True)
data.date = pd.to_datetime(data.date)
data = data.sort_values(by=['date'])
price = np.array(data.price)


##### Utility functions

# In[3]:

def evaluate_strategy(price, actions, action_price):
    '''Evaluate strategy and return growth
    
    price: historical price data
    actions: decision at each point: -1 = sell, 0 = no action, 1 = buy
    action_price: usd price for each action
    '''
    #result = np.ones(len(actions)) # Growth history
    btc = 1                        # Current number of btc
    usd = 0                        # Current number of usd
    last_action = None             # Last non-zero action
    
    # Loop for every time point
    for i, a in enumerate(actions):
        if a != 0:
            if last_action is None:
                # First action
                # If it is a sell, skip action
                # Otherwise perform first purchase
                
                if a == -1:
                    continue            
                btc = 1
                usd = 0
                last_action = a
                continue
        
            # Do trade
            if a == 1:
                # Buy                
                if usd == 0:
                    last_action = a
                    continue
                btc = (usd-action_price)/price[i]
                usd = 0
            else:
                # Sell
                if btc == 0:                    
                    last_action = a
                    continue
                usd = btc*price[i]-action_price
                btc = 0
            
            last_action = a

        #result[i] = (usd + btc * price[i]) / price[0]
    result = (usd + btc * price[i]) / price[0]
    return result

def filtmat(X, axis, func, **kwargs):
    return np.apply_along_axis(lambda m: func(m, **kwargs), axis=axis, arr=X)

def moving_sum(X, n, axis=0):
    return filtmat(X, axis, np.convolve, v=np.ones(n), mode="full")

def moving_average(X, n, axis=0):
    return moving_sum(X, n-1, axis)/n

def moving_range(X, n, axis=0):
    return filtmat(X, axis, lambda m: [np.ptp(m[i:i+n-1]) for i in range(m.shape[0])])

def moving_ratio(X, n, axis=0):
    return filtmat(X, axis, lambda m: m[n-1:]/m[:-n+1])

def vertical_lines(X, **kwargs):
    lc = mc.LineCollection([[(x, -100), (x, 1e6)] for x in X], **kwargs)
    plt.gca().add_collection(lc)
            

def get_actions(price,dt = 15,threshold_up = 0.01,threshold_down = 0.005,peak_width = 0,valley_width = 0,start = 0, end = np.inf):               
    if end == np.inf:
        end = price.shape[0]-1
    dx = moving_ratio(price, dt)[start:end]
    # flag up or down trend if:
    # 1. ratio with earlier price crosses threshold
    # 2. prices are rising/falling for at least [peak_width]/[valley_width] minutes
    up = (dx >= 1+threshold_up) & (moving_sum(dx > 1, max(1, peak_width)) >= peak_width)[max(1, peak_width)-1:]
    down = (dx <= 1-threshold_down) & (moving_sum(dx < 1, max(1, valley_width)) >= valley_width)[ max(1, valley_width)-1:]
    
    # Encode actions
    actions = (up+0-down)  
    return actions

def evaluate_strategies(price,action_price,start_vector = [0], end_vector = [np.inf], dt_vector=[16],threshold_up_vector = [0.01],threshold_down_vector = [0.005] ,peak_width_vector = [0] ,valley_width_vector = [0]):
    if end_vector == [np.inf]:
        end_vector = [price.shape[0]-1]
    matrix_size = len(start_vector) *len(end_vector) *len(dt_vector) *len(threshold_up_vector) *len(threshold_down_vector) *len(peak_width_vector) * len(valley_width_vector) 
    results = np.empty(matrix_size,)
    index = 0
    for s in start_vector:
        for e in end_vector:
            for dt in dt_vector:
                for tup in threshold_up_vector:
                    for tdown in threshold_down_vector:
                        for pwid in peak_width_vector:
                            for vwid in valley_width_vector:                                
                                results[index] = evaluate_strategy(price[s:e], get_actions(price,dt,tup,tdown,pwid,vwid,s,e), action_price)  *100
                                index += 1
    return results

action_price = 1
dt_vector=range(3,50)
start_vector=range(0,10000,1000)
results = evaluate_strategies(price,action_price,dt_vector=dt_vector,start_vector=start_vector)
shaped_results = np.reshape(results,(len(start_vector),len(dt_vector)))
plt.plot(shaped_results.transpose())
plt.figure()
plt.imshow(shaped_results)
'''
# Period to evaluate
start, end = 0, data.price.shape[0]-1

# Price per action
action_price = 1
 
actions = get_actions(data)       
# Set repeated actions (consecutive sell/buy actions) to 0

# Save decision points
idx_down = np.where(actions==-1)[0]
idx_up = np.where(actions==1)[0]

# Some plots for visual inspcetion

# In[5]:

plt.figure(0, figsize=(15,30))
plt.subplot(2,1,1)
plt.axhline(1, color='black')

# plot decision boundaries
plt.axhline(1-threshold_down, color='black', dashes=[2,5])
plt.axhline(1+threshold_up, color='black', dashes=[2,5])

# plot moving ratio
plt.plot(moving_ratio(data.price, dt)[start:end])        
plt.xlabel("Minutes")
plt.ylabel("Growth")

# plot actions
plt.plot(idx_up, dx[idx_up], 'og')
plt.plot(idx_down, dx[idx_down], 'or')

# plot actual price and decisions
plt.subplot(2,1,2)
plt.plot(data.price.values[start:end])
plt.plot(idx_up, data.price.as_matrix()[start:end][idx_up], 'og')
plt.plot(idx_down, data.price.as_matrix()[start:end][idx_down], 'or')
plt.xlabel("Minutes")
plt.ylabel("Price")

pass


##### Evalueate strategy

# In[6]:

result = evaluate_strategy(data.price.values[start:end], actions, action_price)
plt.figure(1, figsize=(15,15))
plt.plot(result)
plt.xlabel("Minutes")
plt.ylabel("Growth")
print("Strategy result: %.0f%%\nMarket result: %.0f%%" % (result[-1]*100, 
                                                          data.price.values[end]/data.price.values[start]*100))
print("Actions: %d" % sum(actions != 0))


# Test random strategy

# In[7]:

# Generate random actions
p_action = 0.1
actions = (np.random.uniform(0, 1, (2,actions.shape[0])) < p_action).sum(0)-1

# Set repeated actions (consecutive sell/buy actions) to 0
_a = actions[0]
for i, a in enumerate(actions):
    if a != 0:
        if a == _a:
            actions[i] = 0
        _a = a

# Save decision points
idx_down = np.where(actions==-1)[0]
idx_up = np.where(actions==1)[0]

result = evaluate_strategy(data.price.values[start:end], actions, action_price)
plt.figure(1, figsize=(15,15))
plt.plot(result)
plt.xlabel("Minutes")
plt.ylabel("Growth")
print("Strategy result: %.0f%%\nMarket result: %.0f%%" % (result[-1]*100, 
                                                          data.price.values[end]/data.price.values[start]*100))
print("Actions: %d" % sum(actions != 0))

'''
