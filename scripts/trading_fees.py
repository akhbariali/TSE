"""Published Mofid stock/rights rates, checked 2026-11-25.

https://learning.emofid.com/trading-fees/ (buy/sell examples).
Undiscounted percentage schedule including sale tax; not fund fees or an
account-specific quote. Fee caps, rebates and execution costs are not modeled.
"""
SOURCE='https://learning.emofid.com/trading-fees/'
BUY={'tse':.003712,'ifb':.003632}
SELL=.0088
TARGET_KIND='stock_net_positive_v1'
STOCK_TYPES={300,303,309,313,400,403,404}


def break_even(market):
    return (1+BUY[market])/(1-SELL)-1


def net_return(gross_return, market):
    return (1+gross_return)*(1-SELL)/(1+BUY[market])-1
