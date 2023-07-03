"""
    Title: Buy and Hold (NSE) using Simple Moving Average (SMA)
    Description: This is a long only strategy which rebalances the 
        portfolio weights every month at month start.
    Style tags: Systematic
    Asset class: Equities, Futures, ETFs, Currencies and Commodities
    Dataset: NSE
"""
# from blueshift_library.technicals.indicators import sma
from blueshift.library.technical.indicator import sma
from blueshift.api import(    symbol,
                            order_target_percent,
                            schedule_function,
                            date_rules,
                            time_rules,
                       )

def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    
    # universe selection
    context.stock = symbol("ASIANPAINT")
    
    # Call rebalance function on the first trading day of each month after 2.5 hours from market open
    schedule_function(rebalance,
                    date_rules.every_day(),
                    time_rules.market_close(hours=0, minutes=30))


def rebalance(context,data):
    """
        A function to rebalance the portfolio, passed on to the call
        of schedule_function above.
    """

    px = data.history(context.stock, 'close', 255, '1d')
    # signal = ma_crossover(px)

    order_target_percent(context.stock, 1)      

def ma_crossover(price):
    fast_ma = sma(price, 50)
    slow_ma = sma(price, 200)

    if fast_ma > slow_ma:
        return 1  # long/buy
    return 0  # no position 


