# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 18:55:31 2017

@author: Boaz
"""

import gdax

book = gdax.OrderBook('BTC-USD')  # each orderbook variable can only register to one product at a time
book.start()
asks = book.get_ask()
asks
asks = book.get_asks()  # give the first order on the book
asks = book.get_asks(19410.01) # return order or None if doesnt exist
asks = [book.get_asks(i) for i in np.linspace(19409,19411,200)]
price_availabe = book.get_asks(19410.35) == None

bids = book.get_bids() # the same for bids
