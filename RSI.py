"""
    Title: RSI - Relative Strength Index (NSE)
    Description: This trading strategy executes every hour to decide 
        how to trade the stocks (100%) based on Relative Strength Index (RSI)
        calculated for 15 days lookback period
    Style tags: Systematic
    Asset class: HAL 
    Dataset: NSE
"""

from blueshift.api import(    symbol,
                            order_target_percent,
                            schedule_function,
                            date_rules,
                            time_rules,
                       )

""" Start of the strategy to define things and schedule rebalance """
def initialize(context):
    
    # universe selection
    # context.stock = symbol("HAL")   # the var name such as 'stock' here is arbitary
    # context.stock = symbol("TATAELXSI")
    context.stock = symbol("AAPL")
    # context.stock = symbol("ADANIENT")    # best

    # we need the past lookpack period data only at starting (day1)?
    context.flag = True
    context.lookback = 15

    # call rebalance function every one hour
    schedule_function(rebalance, 
                    date_rules.every_day(),
                    time_rules.every_nth_hour(1))
    # schedule_function(rebalance, 
    #                 date_rules.every_day(),
    #                 time_rules.every_minute())
    

def rebalance(context,data):
    """
        A function to rebalance the portfolio, passed on to the call
        of schedule_function above.
    """

    if context.flag:
        px = data.history(context.stock, 'close', context.lookback , '1d')
        init_rsi(px, context)  # to initialize prev_avrg params in context

    rsi = get_rsi(context, data)
    if rsi < 30:
        signal = -1  # short/ sell
    elif rsi > 70:
        signal = 1 # long/ buy
    else:
        signal = 0  # hold no position

    order_target_percent(context.stock, signal)


# to initialize prev_avrg params in context
def init_rsi(px, context):
    context.flag = False   # to only run once

    gains = []
    losses = []

    print("in init_rsi: ")
    for i in range(len(px)):
        print(i, px[i])
        if i==0:
            continue
        
        diff = px[i] - px[i-1]
        if diff > 0:
            gains.append(diff)
        elif diff < 0:
            losses.append(abs(diff))

    try:
        avrg_gain = sum(gains) / len(gains)
    except:
        avrg_gain = 0
    try:
        avrg_loss = sum(losses) / len(losses)
    except:
        avrg_loss = 0

    context.prev_avrg_gain = avrg_gain
    context.prev_avrg_loss = avrg_loss


def get_rsi(context, data):
    # we get price as a pandas series
    # can access individual prices through index like array
    # print(price)

    prev_price = data.history(context.stock, 'close', 1, '1d')
    curr_price = data.current(context.stock, 'close')
    diff = curr_price - prev_price[0]

    gain=0
    loss=0
    if diff > 0:
        gain = diff
    elif diff < 0:
        loss = abs(diff)

    lookback = context.lookback
    # print("lookback: ", lookback)

    # not dividing by lookback here
    avrg_gain = context.prev_avrg_gain * (lookback - 1) + gain
    avrg_loss = context.prev_avrg_loss * (lookback - 1) + loss

    # updating prev_avrg
    context.prev_avrg_gain = avrg_gain / lookback
    context.prev_avrg_loss = avrg_loss / lookback

    # calculating rsi
    try:
        alpha = avrg_gain / avrg_loss
        rsi = 100 - (100 / (1 + alpha))
    except:
        rsi = 100

    print("rsi: ", rsi)
    return rsi
