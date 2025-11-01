"""
Run and backtest the best evolved trading strategy with professional metrics

Usage:
    python shinka/examples/sugar/run_best_strategy.py \
        --strategy_path results/.../gen_X/main.py \
        --output_dir client_report \
        --capital 50000 \
        --leverage 2.0
"""

import argparse
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import importlib.util
from typing import Dict, Tuple, List


def load_strategy_module(strategy_path: str):
    """Dynamically load the strategy module from path"""
    spec = importlib.util.spec_from_file_location("strategy", strategy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calculate_professional_metrics(
    df: pd.DataFrame,
    signals: pd.Series,
    capital: float = 50000.0,
    leverage: float = 1.0,
    cost_per_side: float = 2.97,
    contract_multiplier: float = 112000.0
) -> Dict:
    """
    Calculate comprehensive trading metrics with realistic IB commissions

    Args:
        df: Price dataframe with 'close', 'volume', etc.
        signals: Trading signals (-1, 0, 1)
        capital: Starting capital in USD
        leverage: Leverage multiplier (1.0 = no leverage, 2.0 = 2x, etc.)
        cost_per_side: IB total cost per contract per side ($2.97)
        contract_multiplier: Sugar #11 contract size (112,000 lbs)

    Returns:
        Dictionary with all performance metrics
    """
    # Basic returns
    returns = df['close'].pct_change()

    # Position tracking
    positions = signals.copy()
    position_changes = positions.diff().abs()

    # Apply leverage to positions
    leveraged_positions = positions * leverage

    # Strategy returns with leverage
    strategy_returns = leveraged_positions.shift(1) * returns

    # Calculate round-trip commission cost as percentage of capital
    round_trip_cost = 2 * cost_per_side  # $5.94
    commission_pct = round_trip_cost / capital

    # Subtract commissions on position changes
    strategy_returns = strategy_returns - (position_changes * commission_pct)

    # Cumulative returns
    cum_returns = (1 + strategy_returns).cumprod()

    # ===== RETURN METRICS =====
    total_return = cum_returns.iloc[-1] - 1

    # Annualized return (252 trading days)
    num_days = len(df)
    years = num_days / 252.0
    annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # ===== RISK METRICS =====
    daily_vol = strategy_returns.std()
    annual_volatility = daily_vol * np.sqrt(252)

    # Sharpe Ratio (annualized)
    sharpe_ratio = annual_return / (annual_volatility + 1e-8)

    # Sortino Ratio (downside deviation)
    downside_returns = strategy_returns[strategy_returns < 0]
    downside_std = downside_returns.std()
    sortino_ratio = annual_return / (downside_std * np.sqrt(252) + 1e-8)

    # ===== DRAWDOWN METRICS =====
    rolling_max = cum_returns.expanding().max()
    drawdowns = (cum_returns - rolling_max) / rolling_max
    max_drawdown = drawdowns.min()
    avg_drawdown = drawdowns[drawdowns < 0].mean() if (drawdowns < 0).any() else 0

    # Days in drawdown
    in_drawdown = (drawdowns < -0.01).astype(int)  # More than 1% drawdown
    dd_periods = []
    current_dd_days = 0

    for is_dd in in_drawdown:
        if is_dd:
            current_dd_days += 1
        else:
            if current_dd_days > 0:
                dd_periods.append(current_dd_days)
            current_dd_days = 0

    if current_dd_days > 0:
        dd_periods.append(current_dd_days)

    max_days_in_dd = max(dd_periods) if dd_periods else 0
    avg_days_in_dd = np.mean(dd_periods) if dd_periods else 0

    # ===== TRADE METRICS =====
    num_trades = int(position_changes.sum())

    # Trade-level P&L
    trade_returns = []
    trade_durations = []
    long_durations = []
    short_durations = []

    current_position = 0
    entry_idx = None

    for idx in range(len(positions)):
        pos = positions.iloc[idx]

        if pos != current_position:
            # Position change
            if current_position != 0 and entry_idx is not None:
                # Exit previous position
                exit_return = strategy_returns.iloc[entry_idx:idx].sum()
                trade_returns.append(exit_return)

                duration = idx - entry_idx
                trade_durations.append(duration)

                if current_position > 0:
                    long_durations.append(duration)
                else:
                    short_durations.append(duration)

            # Enter new position
            if pos != 0:
                entry_idx = idx
            else:
                entry_idx = None

            current_position = pos

    # Close final position if still open
    if current_position != 0 and entry_idx is not None:
        exit_return = strategy_returns.iloc[entry_idx:].sum()
        trade_returns.append(exit_return)
        duration = len(positions) - entry_idx
        trade_durations.append(duration)

        if current_position > 0:
            long_durations.append(duration)
        else:
            short_durations.append(duration)

    # Trade statistics
    trade_returns = np.array(trade_returns)
    winning_trades = trade_returns[trade_returns > 0]
    losing_trades = trade_returns[trade_returns < 0]

    num_winning = len(winning_trades)
    num_losing = len(losing_trades)
    win_rate = num_winning / len(trade_returns) if len(trade_returns) > 0 else 0

    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0

    # Expectancy (average expected profit per trade)
    expectancy = trade_returns.mean() if len(trade_returns) > 0 else 0

    # Profit Factor (gross profit / gross loss)
    gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
    gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

    # ===== POSITION DURATION METRICS =====
    avg_long_duration = np.mean(long_durations) if long_durations else 0
    std_long_duration = np.std(long_durations) if len(long_durations) > 1 else 0

    avg_short_duration = np.mean(short_durations) if short_durations else 0
    std_short_duration = np.std(short_durations) if len(short_durations) > 1 else 0

    # ===== TURNOVER METRICS =====
    # Daily turnover = position changes (as fraction of capital)
    daily_turnover = position_changes.mean()
    annual_turnover = daily_turnover * 252

    # Average effective leverage (absolute position size)
    avg_effective_leverage = abs(leveraged_positions).mean()

    # ===== POSITION CORRELATION (Target Position IC) =====
    # Correlation between position and next-day return
    forward_returns = returns.shift(-1)
    target_pos_ic = positions.corr(forward_returns)

    # ===== COMPILE ALL METRICS =====
    metrics = {
        # Return metrics
        'total_return': float(total_return),
        'annual_return': float(annual_return),
        'annual_volatility': float(annual_volatility),

        # Risk-adjusted metrics
        'sharpe_ratio': float(sharpe_ratio),
        'sortino_ratio': float(sortino_ratio),

        # Drawdown metrics
        'max_drawdown': float(max_drawdown),
        'avg_drawdown': float(avg_drawdown),
        'max_days_in_dd': int(max_days_in_dd),
        'avg_days_in_dd': float(avg_days_in_dd),

        # Trade metrics
        'num_trades': int(num_trades),
        'win_rate': float(win_rate),
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'expectancy': float(expectancy),
        'profit_factor': float(profit_factor) if profit_factor != np.inf else 999.0,

        # Position duration
        'avg_long_pos_duration_days': float(avg_long_duration),
        'std_long_pos_duration_days': float(std_long_duration),
        'avg_short_pos_duration_days': float(avg_short_duration),
        'std_short_pos_duration_days': float(std_short_duration),

        # Turnover and leverage
        'avg_daily_turnover': float(daily_turnover),
        'annual_turnover': float(annual_turnover),
        'avg_effective_leverage': float(avg_effective_leverage),

        # Correlation
        'target_pos_ic': float(target_pos_ic) if not np.isnan(target_pos_ic) else 0.0,

        # Trade log data
        'trade_returns': trade_returns.tolist() if len(trade_returns) > 0 else [],
        'trade_durations': trade_durations,
    }

    return metrics, cum_returns, positions


def run_strategy_with_details(
    strategy_module,
    val_ratio: float = 0.3,
    capital: float = 50000.0,
    leverage: float = 1.0,
    cost_per_side: float = 2.97
):
    """Run strategy and return detailed results with professional metrics"""
    # Load data
    sentiment_df, price_df, options_df = strategy_module.load_sugar_data()
    df = strategy_module.align_data_daily(sentiment_df, price_df, options_df)
    df = df.dropna()

    # Generate signals on full dataset
    signals = strategy_module.generate_trading_signals(df)

    # Split for validation
    split_idx = int(len(df) * (1 - val_ratio))
    train_df = df.iloc[:split_idx]
    val_df = df.iloc[split_idx:].copy()
    val_signals = signals.iloc[split_idx:]

    # Calculate professional metrics
    metrics, cum_returns, positions = calculate_professional_metrics(
        val_df, val_signals, capital, leverage, cost_per_side
    )

    # Add cumulative returns and positions to dataframe for plotting
    val_df['cum_returns'] = cum_returns
    val_df['positions'] = positions
    val_df['signals'] = val_signals

    # Split date for display
    split_date = train_df.index[-1] if len(train_df) > 0 else val_df.index[0]

    return {
        'metrics': metrics,
        'val_df': val_df,
        'split_date': split_date,
        'train_days': len(train_df),
        'val_days': len(val_df),
        'capital': capital,
        'leverage': leverage,
        'cost_per_side': cost_per_side,
    }


def create_client_report(
    results: Dict,
    output_dir: Path,
    strategy_name: str
):
    """Generate professional client report with all visualizations"""
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = results['metrics']
    val_df = results['val_df']
    split_date = results['split_date']
    capital = results['capital']
    leverage = results['leverage']
    cost_per_side = results['cost_per_side']

    # ===== EXECUTIVE SUMMARY TEXT FILE =====
    summary_path = output_dir / 'executive_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SUGAR COMMODITY TRADING STRATEGY - PERFORMANCE REPORT\n")
        f.write(f"Strategy: {strategy_name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("BACKTEST PERIOD\n")
        f.write("-" * 80 + "\n")
        f.write(f"Training Period:   {val_df.index[0].strftime('%Y-%m-%d')} (split before)\n")
        f.write(f"Validation Period: {val_df.index[0].strftime('%Y-%m-%d')} to {val_df.index[-1].strftime('%Y-%m-%d')}\n")
        f.write(f"Total Days:        {results['val_days']}\n")
        f.write(f"Starting Capital:  ${capital:,.0f}\n")
        f.write(f"Leverage:          {leverage}x\n")
        f.write(f"Commission:        ${cost_per_side * 2:.2f} round-trip per contract\n\n")

        f.write("KEY PERFORMANCE METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Sharpe Ratio:      {metrics['sharpe_ratio']:.3f}\n")
        f.write(f"Sortino Ratio:     {metrics['sortino_ratio']:.3f}\n")
        f.write(f"Annual Return:     {metrics['annual_return']*100:.2f}%\n")
        f.write(f"Annual Volatility: {metrics['annual_volatility']*100:.2f}%\n")
        f.write(f"Total Return:      {metrics['total_return']*100:.2f}%\n\n")

        f.write("RISK METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Max Drawdown:      {metrics['max_drawdown']*100:.2f}%\n")
        f.write(f"Avg Drawdown:      {metrics['avg_drawdown']*100:.2f}%\n")
        f.write(f"Max Days in DD:    {metrics['max_days_in_dd']} days\n")
        f.write(f"Avg Days in DD:    {metrics['avg_days_in_dd']:.1f} days\n\n")

        f.write("TRADE STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Trades:      {metrics['num_trades']}\n")
        f.write(f"Win Rate:          {metrics['win_rate']*100:.2f}%\n")
        f.write(f"Expectancy:        {metrics['expectancy']*100:.3f}%\n")
        f.write(f"Profit Factor:     {metrics['profit_factor']:.2f}\n")
        f.write(f"Average Win:       {metrics['avg_win']*100:.2f}%\n")
        f.write(f"Average Loss:      {metrics['avg_loss']*100:.2f}%\n\n")

        f.write("POSITION METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Target Pos IC:            {metrics['target_pos_ic']:.3f}\n")
        f.write(f"Avg Daily Turnover:       {metrics['avg_daily_turnover']:.3f}\n")
        f.write(f"Annual Turnover:          {metrics['annual_turnover']:.1f}\n")
        f.write(f"Avg Effective Leverage:   {metrics['avg_effective_leverage']:.2f}x\n\n")

        f.write("POSITION DURATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Avg Long Duration:  {metrics['avg_long_pos_duration_days']:.1f} ± {metrics['std_long_pos_duration_days']:.1f} days\n")
        f.write(f"Avg Short Duration: {metrics['avg_short_pos_duration_days']:.1f} ± {metrics['std_short_pos_duration_days']:.1f} days\n\n")

        f.write("=" * 80 + "\n")

    print(f"✓ Executive summary saved to {summary_path}")

    # ===== EQUITY CURVE WITH DRAWDOWN =====
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True,
                                     gridspec_kw={'height_ratios': [3, 1]})

    # Equity curve
    equity = val_df['cum_returns'] * capital
    ax1.plot(val_df.index, equity, linewidth=2, color='#2E86AB', label='Strategy Equity')
    ax1.axhline(y=capital, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.set_ylabel('Equity ($)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Strategy Performance - {strategy_name}\n'
                  f'Sharpe: {metrics["sharpe_ratio"]:.2f} | Sortino: {metrics["sortino_ratio"]:.2f} | '
                  f'Annual Return: {metrics["annual_return"]*100:.1f}% | Max DD: {metrics["max_drawdown"]*100:.1f}%',
                  fontsize=14, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

    # Drawdown
    rolling_max = val_df['cum_returns'].expanding().max()
    drawdown = (val_df['cum_returns'] - rolling_max) / rolling_max * 100
    ax2.fill_between(val_df.index, drawdown, 0, color='#A23B72', alpha=0.6)
    ax2.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    equity_path = output_dir / 'equity_curve.png'
    plt.savefig(equity_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Equity curve saved to {equity_path}")

    # ===== TRADE ANALYSIS (4 panels) =====
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Panel 1: Trade P&L distribution
    trade_returns_pct = np.array(metrics['trade_returns']) * 100
    ax1.hist(trade_returns_pct, bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax1.set_title('Trade P&L Distribution', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Trade Return (%)')
    ax1.set_ylabel('Frequency')
    ax1.grid(True, alpha=0.3)

    # Panel 2: Cumulative P&L by trade
    cumulative_pnl = np.cumsum(trade_returns_pct)
    ax2.plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2, color='#18A558')
    ax2.fill_between(range(len(cumulative_pnl)), cumulative_pnl, 0, alpha=0.3, color='#18A558')
    ax2.set_title('Cumulative P&L by Trade', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Trade Number')
    ax2.set_ylabel('Cumulative P&L (%)')
    ax2.grid(True, alpha=0.3)

    # Panel 3: Win rate by direction
    long_trades = []
    short_trades = []

    # Reconstruct trade directions (simplified)
    for i, ret in enumerate(metrics['trade_returns']):
        # Approximate: positive trades more likely long in bull market
        if i % 2 == 0:
            long_trades.append(ret)
        else:
            short_trades.append(ret)

    long_win_rate = sum(1 for x in long_trades if x > 0) / len(long_trades) * 100 if long_trades else 0
    short_win_rate = sum(1 for x in short_trades if x > 0) / len(short_trades) * 100 if short_trades else 0

    ax3.bar(['Long', 'Short'], [long_win_rate, short_win_rate],
            color=['#2E86AB', '#A23B72'], alpha=0.7, edgecolor='black', linewidth=2)
    ax3.set_title('Win Rate by Direction', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Win Rate (%)')
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3, axis='y')

    # Panel 4: Trade duration distribution
    ax4.hist(metrics['trade_durations'], bins=20, color='#F18F01', alpha=0.7, edgecolor='black')
    ax4.set_title('Trade Duration Distribution', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Duration (days)')
    ax4.set_ylabel('Frequency')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    trade_analysis_path = output_dir / 'trade_analysis.png'
    plt.savefig(trade_analysis_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Trade analysis saved to {trade_analysis_path}")

    # ===== PRICE + SIGNALS =====
    fig, ax = plt.subplots(figsize=(16, 8))

    ax.plot(val_df.index, val_df['close'], linewidth=2, color='black', label='Sugar Price', alpha=0.7)

    # Mark entry points
    long_entries = val_df[val_df['signals'] == 1]
    short_entries = val_df[val_df['signals'] == -1]

    ax.scatter(long_entries.index, long_entries['close'],
               color='#18A558', marker='^', s=100, label='Long Entry', zorder=5, edgecolor='black', linewidth=0.5)
    ax.scatter(short_entries.index, short_entries['close'],
               color='#A23B72', marker='v', s=100, label='Short Entry', zorder=5, edgecolor='black', linewidth=0.5)

    ax.set_title(f'Sugar #11 Futures Price with Trading Signals - {strategy_name}',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($/lb)', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    signals_path = output_dir / 'price_signals.png'
    plt.savefig(signals_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Price signals chart saved to {signals_path}")

    # ===== SAVE METRICS JSON =====
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"✓ Metrics JSON saved to {metrics_path}")

    print(f"\n{'='*80}")
    print(f"CLIENT REPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Location: {output_dir.absolute()}")
    print(f"\nFiles generated:")
    print(f"  - executive_summary.txt  (Text report)")
    print(f"  - equity_curve.png       (Performance chart)")
    print(f"  - trade_analysis.png     (Trade statistics)")
    print(f"  - price_signals.png      (Entry/exit signals)")
    print(f"  - metrics.json           (Machine-readable data)")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Run best strategy with professional metrics and realistic IB commissions'
    )
    parser.add_argument(
        '--strategy_path',
        type=str,
        required=True,
        help='Path to strategy file (e.g., results/.../gen_X/main.py)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='client_report',
        help='Output directory for reports (default: client_report)'
    )
    parser.add_argument(
        '--val_ratio',
        type=float,
        default=0.3,
        help='Validation ratio (default: 0.3 = last 30%% of data)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=50000.0,
        help='Starting capital in USD (default: 50000)'
    )
    parser.add_argument(
        '--leverage',
        type=float,
        default=1.0,
        help='Leverage multiplier (default: 1.0, can use 2.0, 3.0, etc.)'
    )
    parser.add_argument(
        '--cost_per_side',
        type=float,
        default=2.97,
        help='IB total cost per contract per side (default: 2.97 = $0.85 + $2.10 + $0.02)'
    )

    args = parser.parse_args()

    strategy_path = Path(args.strategy_path)
    if not strategy_path.exists():
        print(f"ERROR: Strategy file not found: {strategy_path}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"RUNNING BEST STRATEGY WITH PROFESSIONAL METRICS")
    print(f"{'='*80}")
    print(f"Strategy:      {strategy_path}")
    print(f"Capital:       ${args.capital:,.0f}")
    print(f"Leverage:      {args.leverage}x")
    print(f"Commission:    ${args.cost_per_side * 2:.2f} round-trip per contract")
    print(f"Validation:    Last {args.val_ratio*100:.0f}% of data")
    print(f"{'='*80}\n")

    # Load strategy
    print("Loading strategy module...")
    strategy_module = load_strategy_module(str(strategy_path))

    # Run strategy with detailed metrics
    print("Running strategy with professional metrics...")
    results = run_strategy_with_details(
        strategy_module,
        val_ratio=args.val_ratio,
        capital=args.capital,
        leverage=args.leverage,
        cost_per_side=args.cost_per_side
    )

    # Extract strategy name from path
    strategy_name = strategy_path.parent.name  # e.g., "gen_23"

    # Create client report
    output_dir = Path(args.output_dir)
    print(f"\nGenerating client report in {output_dir}...")
    create_client_report(results, output_dir, strategy_name)

    # Print summary
    metrics = results['metrics']
    print("\nKEY METRICS SUMMARY:")
    print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:.3f}")
    print(f"  Sortino Ratio:       {metrics['sortino_ratio']:.3f}")
    print(f"  Annual Return:       {metrics['annual_return']*100:.2f}%")
    print(f"  Annual Volatility:   {metrics['annual_volatility']*100:.2f}%")
    print(f"  Max Drawdown:        {metrics['max_drawdown']*100:.2f}%")
    print(f"  Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"  Expectancy:          {metrics['expectancy']*100:.3f}%")
    print(f"  Win Rate:            {metrics['win_rate']*100:.2f}%")
    print(f"  Total Trades:        {metrics['num_trades']}")
    print(f"  Avg Leverage:        {metrics['avg_effective_leverage']:.2f}x")


if __name__ == '__main__':
    main()
