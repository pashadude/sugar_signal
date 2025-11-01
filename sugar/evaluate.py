"""
Evaluator for Sugar Trading Strategy Evolution
"""

import os
import argparse
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from shinka.core import run_shinka_eval


def validate_trading_metrics(
    run_output: Dict[str, float],
) -> Tuple[bool, Optional[str]]:
    """
    Validates trading strategy results.

    Args:
        run_output: Dictionary with trading metrics from run_experiment

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    required_keys = ['sharpe_ratio', 'max_drawdown', 'total_return',
                     'num_trades', 'win_rate']

    # Check all required keys are present
    for key in required_keys:
        if key not in run_output:
            return False, f"Missing required metric: {key}"

    # Check for NaN or infinite values
    for key in required_keys:
        value = run_output[key]
        if not np.isfinite(value):
            return False, f"Invalid value for {key}: {value}"

    # Sharpe ratio should be reasonable (not extremely high)
    sharpe = run_output['sharpe_ratio']
    if abs(sharpe) > 10:
        return False, f"Suspiciously high Sharpe ratio: {sharpe}"

    # Max drawdown should be between -1 and 0
    max_dd = run_output['max_drawdown']
    if max_dd > 0 or max_dd < -1:
        return False, f"Invalid max drawdown: {max_dd} (should be between -1 and 0)"

    # Number of trades should be positive
    num_trades = run_output['num_trades']
    if num_trades < 0:
        return False, f"Invalid number of trades: {num_trades}"

    # Win rate should be between 0 and 1
    win_rate = run_output['win_rate']
    if win_rate < 0 or win_rate > 1:
        return False, f"Invalid win rate: {win_rate} (should be between 0 and 1)"

    return True, "Strategy validated successfully"


def get_trading_kwargs(run_index: int) -> Dict[str, Any]:
    """
    Provides keyword arguments for trading strategy runs

    Args:
        run_index: Index of the run (0, 1, 2, ...)

    Returns:
        Dictionary of kwargs to pass to run_experiment
    """
    # Use 30% of data for validation
    return {"val_ratio": 0.3}


def aggregate_trading_metrics(
    results: List[Dict[str, float]], results_dir: str
) -> Dict[str, Any]:
    """
    Aggregates metrics for trading strategy evaluation.
    Assumes num_runs=1 for simplicity.

    Args:
        results: List of result dictionaries from run_experiment
        results_dir: Directory to save additional results

    Returns:
        Dictionary with aggregated metrics and combined_score
    """
    if not results:
        return {"combined_score": -999.0, "error": "No results to aggregate"}

    metrics = results[0]

    # Extract key metrics
    sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
    max_drawdown = metrics.get('max_drawdown', 0.0)
    total_return = metrics.get('total_return', 0.0)
    num_trades = metrics.get('num_trades', 0)
    win_rate = metrics.get('win_rate', 0.0)

    # Calculate combined score with financial logic
    # Primary: Sharpe ratio (want to maximize)
    # Secondary: Max drawdown penalty (want to minimize absolute value)
    # Formula: Sharpe - 0.5 * |max_drawdown|
    # Note: No trade penalty - commissions already penalize overtrading naturally

    # Drawdown penalty: 0.5 weight (so -20% drawdown = -0.1 penalty)
    drawdown_penalty = 0.5 * abs(max_drawdown)

    # Combined score: Sharpe minus drawdown penalty
    combined_score = sharpe_ratio - drawdown_penalty

    # For tracking purposes only (not used in score)
    trade_penalty = 0.0

    # Minimum threshold: if Sharpe < 0.5, strategy is not viable (below risk-free + noise)
    if sharpe_ratio < 0.5:
        combined_score = min(combined_score, -0.5)

    # Public metrics (visible to Shinka for mutation prompts)
    public_metrics = {
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "total_return": float(total_return),
        "num_trades": int(num_trades),
        "win_rate": float(win_rate),
    }

    # Private metrics (not visible to Shinka, but saved)
    private_metrics = {
        "mean_return": float(metrics.get('mean_return', 0.0)),
        "std_return": float(metrics.get('std_return', 0.0)),
        "drawdown_penalty": float(drawdown_penalty),
        "trade_penalty": float(trade_penalty),
    }

    # Text feedback for Shinka (optional)
    text_feedback = f"""
Strategy Performance Summary:
- Sharpe Ratio: {sharpe_ratio:.3f}
- Max Drawdown: {max_drawdown:.2%}
- Total Return: {total_return:.2%}
- Number of Trades: {int(num_trades)}
- Win Rate: {win_rate:.2%}

Combined Score: {combined_score:.3f}
(Formula: Sharpe - 0.5*|MaxDD| - TradePenalty)
Drawdown Penalty: {drawdown_penalty:.3f}
Trade Penalty: {trade_penalty:.3f}
"""

    aggregated = {
        "combined_score": float(combined_score),
        "public": public_metrics,
        "private": private_metrics,
        "text_feedback": text_feedback.strip(),
    }

    return aggregated


def main(program_path: str, results_dir: str):
    """Runs the sugar trading strategy evaluation using shinka.eval."""
    print(f"Evaluating program: {program_path}")
    print(f"Saving results to: {results_dir}")
    os.makedirs(results_dir, exist_ok=True)

    num_experiment_runs = 1  # Run once on validation set

    # Define a nested function to pass results_dir to the aggregator
    def _aggregator_with_context(
        r: List[Dict[str, float]],
    ) -> Dict[str, Any]:
        return aggregate_trading_metrics(r, results_dir)

    metrics, correct, error_msg = run_shinka_eval(
        program_path=program_path,
        results_dir=results_dir,
        experiment_fn_name="run_experiment",
        num_runs=num_experiment_runs,
        get_experiment_kwargs=get_trading_kwargs,
        validate_fn=validate_trading_metrics,
        aggregate_metrics_fn=_aggregator_with_context,
    )

    if correct:
        print(" Evaluation and Validation completed successfully.")
    else:
        print(f" Evaluation or Validation failed: {error_msg}")

    print("\nMetrics:")
    for key, value in metrics.items():
        if key == 'text_feedback':
            print(f"\n{value}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sugar trading strategy evaluator using shinka.eval"
    )
    parser.add_argument(
        "--program_path",
        type=str,
        default="initial.py",
        help="Path to program to evaluate (must contain 'run_experiment')",
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results",
        help="Directory to save results (metrics.json, correct.json)",
    )
    parsed_args = parser.parse_args()
    main(parsed_args.program_path, parsed_args.results_dir)
