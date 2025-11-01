# Sugar Trading Strategy - Client Demonstration Guide

This guide shows how to run the evolved trading strategy and generate professional reports for client presentation.

## Quick Start

### 1. Run Evolution (if not already done)
```bash
shinka_launch variant=sugar_trading_example
```

Wait for evolution to complete or reach a good strategy (monitor with `shinka_visualize`).

### 2. Find the Best Strategy
```bash
python shinka/examples/sugar/find_best_strategy.py \
  --results_dir results/shinka_sugar_trading/2025.10.31XXXXXX_example
```

This will scan all generations and show the best performing strategy with its path.

### 3. Generate Client Report
```bash
python shinka/examples/sugar/run_best_strategy.py \
  --strategy_path results/shinka_sugar_trading/2025.10.31XXXXXX_example/gen_XX/main.py \
  --output_dir client_report
```

## What Gets Generated

The client report includes:

### 📄 **executive_summary.txt**
Professional text report with:
- Backtest period details
- Key performance metrics (Sharpe, returns, drawdown)
- Trade statistics (win rate, avg win/loss)
- Risk-adjusted metrics (Calmar ratio, risk/reward)

### 📊 **equity_curve.png**
High-resolution chart showing:
- Strategy cumulative returns over time
- Drawdown visualization
- Performance metrics overlay
- Professional formatting suitable for presentations

### 📈 **trade_analysis.png**
4-panel analysis:
- P&L distribution histogram
- Cumulative P&L by trade
- Win rate by direction (long vs short)
- Holding period distribution

### 💹 **price_signals.png**
Price chart with trading signals:
- Sugar futures price over time
- Green triangles (▲) for long entries
- Red triangles (▼) for short entries
- Easy to understand entry/exit points

### 📑 **trade_log.csv**
Detailed spreadsheet of all trades:
- Entry/exit dates and prices
- Direction (LONG/SHORT)
- P&L percentage
- Holding period
- Can be opened in Excel/Google Sheets

### 🔧 **metrics.json**
Machine-readable metrics for:
- Integration with other systems
- Automated reporting
- Further analysis

## Example Output

```
================================================================================
BEST STRATEGY FOUND
================================================================================
Generation:     gen_23
Strategy Path:  results/.../gen_23/main.py

Performance Metrics:
  Combined Score: 2.145
  Sharpe Ratio:   2.34
  Total Return:   78.23%
  Max Drawdown:   -6.45%
  Win Rate:       58.7%
  Trades:         52
================================================================================
```

## Client Presentation Tips

### For Meetings
1. Start with **executive_summary.txt** - Print or share as PDF
2. Show **equity_curve.png** - Demonstrates consistent growth
3. Highlight **Sharpe ratio > 1.75** - Strong risk-adjusted returns
4. Discuss **trade_log.csv** - Shows systematic approach

### Key Talking Points
- ✅ **Out-of-sample validation**: Results are on unseen data (last 30% of period)
- ✅ **Multi-modal approach**: Combines news sentiment + price + options data
- ✅ **Transparent strategy**: No blackbox ML, interpretable mathematical formulas
- ✅ **Risk-controlled**: Max drawdown limits protect capital
- ✅ **Realistic costs**: 0.1% commission per trade included in backtest

### Risk Disclaimers
Always include:
> "This is a backtest on historical data. Past performance does not guarantee future results. The strategy was tested on validation data not used during training, but market conditions change over time."

## Advanced Usage

### Run on Different Validation Split
```bash
python shinka/examples/sugar/run_best_strategy.py \
  --strategy_path results/.../gen_XX/main.py \
  --val_ratio 0.2 \
  --output_dir client_report_20pct_val
```

### Generate Multiple Reports
Compare different strategies:
```bash
# Best strategy
python shinka/examples/sugar/run_best_strategy.py \
  --strategy_path results/.../gen_23/main.py \
  --output_dir reports/gen_23_best

# Alternative strategy
python shinka/examples/sugar/run_best_strategy.py \
  --strategy_path results/.../gen_18/main.py \
  --output_dir reports/gen_18_alternative
```

## What the Client Sees

### Executive Summary Example
```
================================================================================
SUGAR COMMODITY TRADING STRATEGY - PERFORMANCE REPORT
Strategy: gen_23
Generated: 2025-10-31 16:45:32
================================================================================

BACKTEST PERIOD
--------------------------------------------------------------------------------
Training Period:   2021-09-01 to 2024-04-03
Validation Period: 2024-04-04 to 2025-05-09
Total Days:        280

KEY PERFORMANCE METRICS
--------------------------------------------------------------------------------
Sharpe Ratio:      2.341  (Target: > 1.75) ✓
Total Return:      78.23%
Max Drawdown:      -6.45%
Win Rate:          58.7%
Number of Trades:  52
Avg Daily Return:  0.245%
Daily Volatility:  1.876%

TRADE STATISTICS
--------------------------------------------------------------------------------
Total Trades:        52
Winning Trades:      31 (59.6%)
Losing Trades:       21 (40.4%)
Average Win:         4.32%
Average Loss:        -2.18%
Best Trade:          12.45%
Worst Trade:         -5.23%
Avg Holding Period:  4.8 days

RISK-ADJUSTED PERFORMANCE
--------------------------------------------------------------------------------
Annualized Return:   70.45%
Risk/Reward Ratio:   12.13
Calmar Ratio:        10.92
```

## Troubleshooting

### "No valid strategies found"
- Check if evolution is still running
- Look for errors in generation logs: `results/.../gen_X/results/correct.json`
- Verify data files are accessible

### "Strategy file not found"
- Double-check the path from `find_best_strategy.py` output
- Use tab-completion for file paths
- Ensure you're in the repository root directory

### Charts not generating
- Install matplotlib: `pip install matplotlib`
- Check write permissions for output directory

## Next Steps

After generating the client report:

1. **Review locally** - Check all files look correct
2. **Create presentation** - Use charts in PowerPoint/Google Slides
3. **Prepare Q&A** - Understand the strategy logic (see initial.py EVOLVE-BLOCK)
4. **Forward test** - Consider paper trading before live deployment

## Production Deployment

⚠️ **Important**: This is a backtest tool. For live trading:
1. Implement real-time data feeds
2. Add order execution system
3. Include risk management (position limits, stop-losses)
4. Monitor strategy performance continuously
5. Have kill-switch for emergencies

---

**Questions?** Check the main README or evolution logs for more details.
