"""
Find the best strategy from evolution results

Usage:
    python shinka/examples/sugar/find_best_strategy.py --results_dir results/shinka_sugar_trading/2025.10.31XXXXXX_example
"""

import argparse
import json
from pathlib import Path
import sys


def find_best_strategy(results_dir: Path):
    """Find the generation with the highest score"""

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    best_gen = None
    best_score = -999999
    best_metrics = None

    # Scan all generation directories
    gen_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('gen_')])

    if not gen_dirs:
        print(f"ERROR: No generation directories found in {results_dir}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"SCANNING EVOLUTION RESULTS")
    print(f"{'='*80}")
    print(f"Results directory: {results_dir}")
    print(f"Generations found: {len(gen_dirs)}\n")

    # Check each generation
    for gen_dir in gen_dirs:
        metrics_file = gen_dir / 'results' / 'metrics.json'
        correct_file = gen_dir / 'results' / 'correct.json'

        if not metrics_file.exists() or not correct_file.exists():
            continue

        # Load correctness status
        with open(correct_file, 'r') as f:
            correct_data = json.load(f)

        if not correct_data.get('correct', False):
            continue  # Skip incorrect strategies

        # Load metrics
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)

        score = metrics.get('combined_score', -999999)
        sharpe = metrics.get('public', {}).get('sharpe_ratio', 0)

        gen_num = int(gen_dir.name.split('_')[1])

        print(f"Gen {gen_num:3d}: Score={score:7.3f}, Sharpe={sharpe:.3f} {'✓' if score > best_score else ''}")

        if score > best_score:
            best_gen = gen_dir
            best_score = score
            best_metrics = metrics

    print(f"\n{'='*80}")

    if best_gen is None:
        print("No valid strategies found! All generations failed.")
        print("\nPossible reasons:")
        print("  - Evolution is still running")
        print("  - All strategies have errors (check logs)")
        print("  - Wrong results directory")
        sys.exit(1)

    # Display best strategy
    print(f"BEST STRATEGY FOUND")
    print(f"{'='*80}")
    print(f"Generation:     {best_gen.name}")
    print(f"Strategy Path:  {best_gen / 'main.py'}")
    print(f"\nPerformance Metrics:")
    print(f"  Combined Score: {best_score:.3f}")

    if 'public' in best_metrics:
        public = best_metrics['public']
        print(f"  Sharpe Ratio:   {public.get('sharpe_ratio', 0):.3f}")
        print(f"  Total Return:   {public.get('total_return', 0)*100:.2f}%")
        print(f"  Max Drawdown:   {public.get('max_drawdown', 0)*100:.2f}%")
        print(f"  Win Rate:       {public.get('win_rate', 0)*100:.1f}%")
        print(f"  Trades:         {public.get('num_trades', 0)}")

    print(f"\n{'='*80}")
    print(f"TO GENERATE CLIENT REPORT, RUN:")
    print(f"{'='*80}")
    print(f"python shinka/examples/sugar/run_best_strategy.py \\")
    print(f"  --strategy_path {best_gen / 'main.py'} \\")
    print(f"  --output_dir client_report_{best_gen.name}")
    print(f"{'='*80}\n")

    return best_gen


def main():
    parser = argparse.ArgumentParser(
        description='Find the best strategy from evolution results'
    )
    parser.add_argument(
        '--results_dir',
        type=str,
        required=True,
        help='Path to evolution results directory (e.g., results/shinka_sugar_trading/2025.10.31XXXXXX_example)'
    )

    args = parser.parse_args()
    results_dir = Path(args.results_dir)

    find_best_strategy(results_dir)


if __name__ == '__main__':
    main()
