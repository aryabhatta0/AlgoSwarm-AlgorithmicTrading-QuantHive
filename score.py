
sharpe_ratio = 1.56
cumulative_returns = 3103.74  # %
annual_returns = 102.87  # %
annual_volatility = 54.23   # %
max_drawdown = -38.63  # %

# metric defined in PS
score = 0.2*sharpe_ratio + 0.2*(cumulative_returns/100) + 0.1*(annual_returns/100) - 0.25*(annual_volatility/100) - 0.25*(max_drawdown/100)
print(score)