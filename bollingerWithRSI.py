"""
    Title: Bollinger Band Strategy (NSE)
    Description: This is a long short strategy based on bollinger bands
        and SMA dual signals
    Style tags: Systematic Fundamental
    Asset class: Equities, Futures, ETFs and Currencies
    Dataset: NSE
"""
from blueshift.library.technicals.indicators import bollinger_band, ema

from blueshift.finance import commission, slippage
from blueshift.api import(  symbol,
                            order_target_percent,
                            set_commission,
                            set_slippage,
                            schedule_function,
                            date_rules,
                            time_rules,
                       )

def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    # universe selection
    context.securities = [symbol('ADANIENT'), symbol("TATAELXSI")]
    # context.securities = [symbol('TATAELXSI'), symbol('ADANIENT')]
    # context.securities = [symbol('NIFTY-I'),symbol('BANKNIFTY-I')]
    # context.stock = symbol("HAL")
    # context.stock = symbol("TATAELXSI")
    # context.stock = symbol("ADANIENT")

    # define strategy parameters
    context.params = {'indicator_lookback':375,
                      'indicator_freq':'1m',
                      'buy_signal_threshold':0.5,
                      'sell_signal_threshold':-0.5,
                      'SMA_period_short':15,
                      'SMA_period_long':60,
                      'BBands_period':300,
                      'trade_freq':60,  # 5
                      'leverage':1}     # 2

    # indicator_lookback & indicator_freq : past data params to use to generate signals
    # trade_freq: run_strategy will be scheduled every trade_freq mins
    # leverage: scaling factor to decide bet size

    # RSI
    context.rsiflag = True
    context.rsilookback = 15
    context.prev_avrg_gain = dict((security,0) for security in context.securities)
    context.prev_avrg_loss = dict((security,0) for security in context.securities)
    context.rsi = dict((security, 50) for security in context.securities)    # curr rsi of each stock

    # variables to track signals and target portfolio
    context.signals = dict((security,0) for security in context.securities)    # -1/0/1
    context.target_position = dict((security,0) for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))
    
    freq = int(context.params['trade_freq'])
    schedule_function(run_strategy, date_rules.every_day(),
                      time_rules.every_nth_minute(freq))
    
    schedule_function(stop_trading, date_rules.every_day(),
                      time_rules.market_close(minutes=30))
    
    context.trade = True

# to initialize prev_avrg params in context
def init_rsi(context, data):
    context.rsiflag = False   # to only run once

    price_data = data.history(context.securities, 'close', context.rsilookback , '1d')

    for security in context.securities:
        px = price_data.loc[:,security].values

        gains = []
        losses = []

        # print("in init_rsi: ")
        for i in range(len(px)):
            # print(i, px[i])
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

        # context.prev_avrg_gain = avrg_gain
        context.prev_avrg_gain[security] = avrg_gain
        context.prev_avrg_loss[security] = avrg_loss

# called at a preset time before the market opens, every day
def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    """
        A function to define core strategy steps
    """
    # For RSI
    if context.rsiflag:
        # px = data.history(context.securities, 'close', context.rsilookback , '1d')
        init_rsi(context, data)  # to initialize prev_avrg params in context

    if not context.trade:
        return
    
    generate_signals(context, data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
    """
        A function to rebalance - all execution logic goes here
    """
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
    """
        A function to define target portfolio
    """
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        if context.signals[security] > context.params['buy_signal_threshold']:
            context.target_position[security] = weight
        elif context.signals[security] < context.params['sell_signal_threshold']:
            context.target_position[security] = -weight
        else:
            context.target_position[security] = 0

def get_rsi(context, data):
    # we get price as a pandas series
    # can access individual prices through index like array
    # print(price)

    prev_price = data.history(context.securities, 'close', 1, '1d')
    curr_price = data.current(context.securities, 'close')               # ind price iss se kaise nikale?
    # print("curr_price: ", curr_price)
    # print("curr type= ", type(curr_price))   # pd series

    # print("prev_price: ", prev_price)
    # print(type(prev_price))    # dataframe

    # print("\n\n")
    # security = context.securities[0]      # = Equity(ADANIENT [17])
    # print("Security: ", security)
    # try:
    #     print("#1: ",curr_price.loc[security])
    # except:
    #     print("FAULTTT in curr")
    # try:
    #     print("#1.2: ",curr_price.values[0])
    # except:
    #     print("FAULTTT in curr1.2")
    
    # try:
    #     print("#2", prev_price[security].iloc[0])
    # except:
    #     print("FAULTTT in prev")
    # try:
    #     print("#2.2", prev_price.iloc[0, 0])
    # except:
    #     print("FAULTTT in prev2.2")

    for security in context.securities:
        diff = 0
        try:
            diff = curr_price.loc[security] - prev_price[security].iloc[0]
        except:
            print("Couldn't take diff in get_rsi")
            return

        gain=0
        loss=0
        if diff > 0:
            gain = diff
        elif diff < 0:
            loss = abs(diff)

        lookback = context.rsilookback
        # print("lookback: ", lookback)

        # not dividing by lookback here
        avrg_gain = context.prev_avrg_gain[security] * (lookback - 1) + gain
        avrg_loss = context.prev_avrg_loss[security] * (lookback - 1) + loss

        # updating prev_avrg
        context.prev_avrg_gain[security] = avrg_gain / lookback
        context.prev_avrg_loss[security] = avrg_loss / lookback

        # calculating rsi
        try:
            alpha = avrg_gain / avrg_loss
            rsi = 100 - (100 / (1 + alpha))
        except:
            rsi = 100

        print("For ", security)
        print("rsi: ", rsi)
        context.rsi[security] = rsi
        # return rsi

def generate_signals(context, data):
    """
        A function to define define the signal generation
    """
    try:
        price_data = data.history(context.securities, 'close',
            context.params['indicator_lookback'],
            context.params['indicator_freq'])
    except:
        return

    # update rsi
    get_rsi(context, data)

    for security in context.securities:
        px = price_data.loc[:,security].values
        # context.signals[security] = signal_function(px, context.params)
        context.signals[security] = signal_function(px, context.params, context, security)

def signal_function(px, params, context, security):
    """
        The main trading logic goes here, called by generate_signals above
    """
    upper, mid, lower = bollinger_band(px,params['BBands_period'])
    if upper - lower == 0:
        return 0
    
    # exponential moving average
    ind2 = ema(px, params['SMA_period_short'])
    ind3 = ema(px, params['SMA_period_long'])
    last_px = px[-1]
    dist_to_upper = 100*(upper - last_px)/(upper - lower)

    if dist_to_upper > 95:
        return -1
    elif dist_to_upper < 5:
        return 1

    curr_rsi = context.rsi[security]
    if curr_rsi < 30:
        return -1  # short/ sell
    elif curr_rsi > 70:
        return 1 # long/ buy
    else:
        return 0  # hold no position

    if dist_to_upper > 40 and dist_to_upper < 60 and ind2-ind3 < 0:
        return -1
    elif dist_to_upper > 40 and dist_to_upper < 60 and ind2-ind3 > 0:
        return 1
    else:
        return 0
