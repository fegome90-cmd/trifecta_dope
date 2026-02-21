#!/usr/bin/env python3
"""
Variance Analysis for HN Benchmark Results
Agent 5 (Variance Analysis) - hn-benchmark-squad
"""

import csv
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any
import math


@dataclass
class MetricStats:
    """Statistical summary for a metric."""
    name: str
    values: List[float] = field(default_factory=list)
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    variance: float = 0.0
    cv: float = 0.0  # Coefficient of Variation
    min_val: float = 0.0
    max_val: float = 0.0
    outliers: List[float] = field(default_factory=list)

    def calculate(self) -> None:
        """Calculate all statistics."""
        if not self.values:
            return

        self.mean = statistics.mean(self.values)
        self.median = statistics.median(self.values)
        self.min_val = min(self.values)
        self.max_val = max(self.values)

        if len(self.values) > 1:
            self.std_dev = statistics.stdev(self.values)
            self.variance = statistics.variance(self.values)
        else:
            self.std_dev = 0.0
            self.variance = 0.0

        # Coefficient of variation (CV)
        if self.mean != 0:
            self.cv = (self.std_dev / abs(self.mean)) * 100
        else:
            self.cv = float('inf')

        # Outliers: values > 2 standard deviations from mean
        if self.std_dev > 0:
            lower_bound = self.mean - 2 * self.std_dev
            upper_bound = self.mean + 2 * self.std_dev
            self.outliers = [v for v in self.values if v < lower_bound or v > upper_bound]


@dataclass
class ScenarioStats:
    """Statistics for a scenario type (baseline or cli)."""
    scenario: str
    wall_time: MetricStats = field(default_factory=lambda: MetricStats("wall_time_s"))
    avg_tool_rtt: MetricStats = field(default_factory=lambda: MetricStats("avg_tool_rtt_ms"))
    p95_tool_rtt: MetricStats = field(default_factory=lambda: MetricStats("p95_tool_rtt_ms"))
    pcc_total_tokens: MetricStats = field(default_factory=lambda: MetricStats("pcc_total_tokens"))
    tool_calls: MetricStats = field(default_factory=lambda: MetricStats("tool_calls"))
    zero_hit_rate: MetricStats = field(default_factory=lambda: MetricStats("zero_hit_rate"))
    baseline_total_tokens: MetricStats = field(default_factory=lambda: MetricStats("baseline_total_tokens"))

    def add_row(self, row: Dict[str, Any]) -> None:
        """Extract and add metrics from a CSV row."""
        # Wall time
        if row.get('wall_time_s'):
            try:
                self.wall_time.values.append(float(row['wall_time_s']))
            except (ValueError, TypeError):
                pass

        # Tool RTT
        if row.get('avg_tool_rtt_ms'):
            try:
                val = float(row['avg_tool_rtt_ms'])
                if val > 0:  # Only include non-zero RTT (baseline has 0 tools)
                    self.avg_tool_rtt.values.append(val)
            except (ValueError, TypeError):
                pass

        if row.get('p95_tool_rtt_ms'):
            try:
                val = float(row['p95_tool_rtt_ms'])
                if val > 0:
                    self.p95_tool_rtt.values.append(val)
            except (ValueError, TypeError):
                pass

        # PCC tokens
        if row.get('pcc_total_tokens'):
            try:
                val = int(float(row['pcc_total_tokens']))
                if val > 0:
                    self.pcc_total_tokens.values.append(val)
            except (ValueError, TypeError):
                pass

        # Tool calls
        if row.get('tool_calls'):
            try:
                val = int(float(row['tool_calls']))
                self.tool_calls.values.append(val)
            except (ValueError, TypeError):
                pass

        # Zero hit rate
        if row.get('zero_hit_rate'):
            try:
                self.zero_hit_rate.values.append(float(row['zero_hit_rate']))
            except (ValueError, TypeError):
                pass

        # Baseline total tokens
        if row.get('baseline_total_tokens'):
            try:
                val = int(float(row['baseline_total_tokens']))
                if val > 0:
                    self.baseline_total_tokens.values.append(val)
            except (ValueError, TypeError):
                pass

    def finalize(self) -> None:
        """Calculate all statistics."""
        for metric in [self.wall_time, self.avg_tool_rtt, self.p95_tool_rtt,
                       self.pcc_total_tokens, self.tool_calls, self.zero_hit_rate,
                       self.baseline_total_tokens]:
            metric.calculate()


def read_csv_files(csv_dir: Path) -> tuple[ScenarioStats, ScenarioStats]:
    """Read all CSV files and aggregate statistics."""
    baseline = ScenarioStats("baseline")
    cli = ScenarioStats("cli")

    csv_files = list(csv_dir.glob("hn_runs*.csv"))

    for csv_path in csv_files:
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scenario = row.get('scenario', '')
                    status = row.get('status', '')

                    # Skip invalid runs for variance analysis of successful runs
                    if status == 'invalid':
                        continue

                    if scenario == 'baseline':
                        baseline.add_row(row)
                    elif scenario == 'cli':
                        cli.add_row(row)
        except Exception as e:
            print(f"Warning: Could not read {csv_path}: {e}")

    baseline.finalize()
    cli.finalize()

    return baseline, cli


def calculate_sample_size_for_cv(current_cv: float, target_cv: float, confidence: float = 0.95) -> int:
    """
    Estimate required sample size to achieve target CV.

    Uses the formula: n_required = n_current * (current_cv / target_cv)^2
    Adjusted for confidence interval.
    """
    if current_cv <= target_cv:
        return len([])  # Already at target

    # Conservative estimate assuming n_current is the current sample size
    n_current = 10  # Typical current sample size

    # Required samples scales with square of CV ratio
    n_required = n_current * (current_cv / target_cv) ** 2

    # Add margin for confidence
    n_required *= (1 / confidence)

    return math.ceil(n_required)


def format_stat(value: float, precision: int = 4) -> str:
    """Format a statistic value."""
    if isinstance(value, float):
        if math.isinf(value):
            return "∞"
        return f"{value:.{precision}f}"
    return str(value)


def generate_markdown_report(baseline: ScenarioStats, cli: ScenarioStats) -> str:
    """Generate a markdown variance analysis report."""

    lines = [
        "# HN Benchmark - Variance Analysis Report",
        "",
        "**Agent:** 5 (Variance Analysis)",
        "**Date:** 2026-02-19",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report analyzes statistical variance across HN benchmark runs to identify:",
        "- Stability of key metrics (wall time, tool RTT, token counts)",
        "- Outliers and their causes",
        "- Coefficient of variation (CV) for reliability assessment",
        "- Sample size recommendations for future benchmarking",
        "",
        "## Summary Statistics",
        "",
        "### Baseline Scenario Statistics",
        "",
        "| Metric | N | Mean | Median | Std Dev | Variance | CV (%) | Min | Max | Outliers |",
        "|--------|---|------|--------|---------|----------|-------|-----|-----|----------|",
    ]

    for metric in [baseline.wall_time, baseline.avg_tool_rtt, baseline.p95_tool_rtt,
                   baseline.pcc_total_tokens, baseline.tool_calls, baseline.zero_hit_rate,
                   baseline.baseline_total_tokens]:
        if metric.values:
            lines.append(
                f"| {metric.name} | {len(metric.values)} | "
                f"{format_stat(metric.mean)} | {format_stat(metric.median)} | "
                f"{format_stat(metric.std_dev)} | {format_stat(metric.variance)} | "
                f"{format_stat(metric.cv, 2)} | {format_stat(metric.min_val)} | "
                f"{format_stat(metric.max_val)} | {len(metric.outliers)} |"
            )
        else:
            lines.append(f"| {metric.name} | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")

    lines.extend([
        "",
        "### CLI Scenario Statistics",
        "",
        "| Metric | N | Mean | Median | Std Dev | Variance | CV (%) | Min | Max | Outliers |",
        "|--------|---|------|--------|---------|----------|-------|-----|-----|----------|",
    ])

    for metric in [cli.wall_time, cli.avg_tool_rtt, cli.p95_tool_rtt,
                   cli.pcc_total_tokens, cli.tool_calls, cli.zero_hit_rate,
                   cli.baseline_total_tokens]:
        if metric.values:
            lines.append(
                f"| {metric.name} | {len(metric.values)} | "
                f"{format_stat(metric.mean)} | {format_stat(metric.median)} | "
                f"{format_stat(metric.std_dev)} | {format_stat(metric.variance)} | "
                f"{format_stat(metric.cv, 2)} | {format_stat(metric.min_val)} | "
                f"{format_stat(metric.max_val)} | {len(metric.outliers)} |"
            )
        else:
            lines.append(f"| {metric.name} | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")

    # Variance Analysis
    lines.extend([
        "",
        "---",
        "",
        "## Variance Analysis",
        "",
    ])

    # Wall time analysis
    lines.extend([
        "### Wall Time Stability",
        "",
        f"**Baseline:** CV = {format_stat(baseline.wall_time.cv, 2)}% "
        f"({'LOW' if baseline.wall_time.cv < 5 else 'MEDIUM' if baseline.wall_time.cv < 15 else 'HIGH'})",
        f"**CLI:** CV = {format_stat(cli.wall_time.cv, 2)}% "
        f"({'LOW' if cli.wall_time.cv < 5 else 'MEDIUM' if cli.wall_time.cv < 15 else 'HIGH'})",
        "",
    ])

    if baseline.wall_time.values and cli.wall_time.values:
        baseline_cv = baseline.wall_time.cv
        cli_cv = cli.wall_time.cv
        stable = "BOTH STABLE" if baseline_cv < 10 and cli_cv < 10 else "NEEDS INVESTIGATION"
        lines.append(f"**Verdict:** {stable}")
        lines.append("")

    # Tool RTT analysis
    lines.extend([
        "### Tool RTT Stability",
        "",
        f"**Average Tool RTT (CLI):** CV = {format_stat(cli.avg_tool_rtt.cv, 2)}%",
        f"**P95 Tool RTT (CLI):** CV = {format_stat(cli.p95_tool_rtt.cv, 2)}%",
        "",
    ])

    # Token analysis
    lines.extend([
        "### Token Count Stability",
        "",
        f"**PCC Total Tokens (CLI):** CV = {format_stat(cli.pcc_total_tokens.cv, 2)}%",
        f"**Baseline Total Tokens:** CV = {format_stat(baseline.baseline_total_tokens.cv, 2)}%",
        "",
    ])

    # Outlier Analysis
    lines.extend([
        "---",
        "",
        "## Outlier Analysis",
        "",
    ])

    all_outliers = []
    for scenario_name, scenario in [("Baseline", baseline), ("CLI", cli)]:
        for metric in [scenario.wall_time, scenario.avg_tool_rtt, scenario.p95_tool_rtt,
                       scenario.pcc_total_tokens, scenario.tool_calls]:
            if metric.outliers:
                for outlier in metric.outliers:
                    all_outliers.append({
                        'scenario': scenario_name,
                        'metric': metric.name,
                        'value': outlier,
                        'z_score': abs((outlier - metric.mean) / metric.std_dev) if metric.std_dev > 0 else 0
                    })

    if all_outliers:
        lines.append("| Scenario | Metric | Outlier Value | Z-Score |")
        lines.append("|----------|--------|---------------|---------|")
        for o in sorted(all_outliers, key=lambda x: x['z_score'], reverse=True):
            lines.append(f"| {o['scenario']} | {o['metric']} | {format_stat(o['value'])} | {format_stat(o['z_score'], 2)} |")
    else:
        lines.append("*No outliers detected (values within ±2σ)*")

    lines.append("")

    # Comparison: Baseline vs CLI
    lines.extend([
        "---",
        "",
        "## Baseline vs CLI Comparison",
        "",
        "| Metric | Baseline CV (%) | CLI CV (%) | More Stable | Ratio (CLI/Baseline) |",
        "|--------|----------------|------------|-------------|---------------------|",
    ])

    metrics_to_compare = [
        ("Wall Time", baseline.wall_time, cli.wall_time),
        ("Avg Tool RTT", baseline.avg_tool_rtt, cli.avg_tool_rtt),
        ("P95 Tool RTT", baseline.p95_tool_rtt, cli.p95_tool_rtt),
        ("Total Tokens", baseline.pcc_total_tokens, cli.pcc_total_tokens),
    ]

    for name, base_metric, cli_metric in metrics_to_compare:
        if base_metric.values and cli_metric.values:
            more_stable = "Baseline" if base_metric.cv < cli_metric.cv else "CLI"
            ratio = cli_metric.cv / base_metric.cv if base_metric.cv > 0 else float('inf')
            lines.append(
                f"| {name} | {format_stat(base_metric.cv, 2)} | "
                f"{format_stat(cli_metric.cv, 2)} | {more_stable} | {format_stat(ratio, 2)}x |"
            )

    lines.append("")

    # Sample Size Recommendations
    lines.extend([
        "---",
        "",
        "## Sample Size Recommendations",
        "",
        "Based on observed variance, here are recommendations for N trials:",
        "",
    ])

    lines.extend([
        "| Scenario | Current CV | Target CV (5%) | Recommended N | Current N | Gap |",
        "|----------|------------|----------------|---------------|-----------|-----|",
    ])

    for scenario_name, scenario in [("Baseline", baseline), ("CLI", cli)]:
        cv = scenario.wall_time.cv
        current_n = len(scenario.wall_time.values)
        if cv > 5:
            # Required N scales with (current_cv/target_cv)^2
            required_n = calculate_sample_size_for_cv(cv, 5.0)
            # Scale based on current sample size
            required_n = max(required_n, int(current_n * (cv / 5.0) ** 2))
            gap = max(0, required_n - current_n)
        else:
            required_n = current_n
            gap = 0

        lines.append(
            f"| {scenario_name} | {format_stat(cv, 2)}% | 5% | "
            f"{required_n} | {current_n} | {gap} |"
        )

    lines.extend([
        "",
        "### Key Findings:",
        "",
    ])

    # Stability verdict
    if cli.wall_time.cv < 5:
        lines.append("1. **CLI wall time is STABLE** (CV < 5%) - 3-5 trials sufficient")
    elif cli.wall_time.cv < 15:
        lines.append("1. **CLI wall time is MODERATELY STABLE** (CV 5-15%) - 5-10 trials recommended")
    else:
        lines.append("1. **CLI wall time is UNSTABLE** (CV > 15%) - 10+ trials required")

    if baseline.wall_time.cv < 5:
        lines.append("2. **Baseline wall time is STABLE** (CV < 5%) - 3-5 trials sufficient")
    elif baseline.wall_time.cv < 15:
        lines.append("2. **Baseline wall time is MODERATELY STABLE** (CV 5-15%) - 5-10 trials recommended")
    else:
        lines.append("2. **Baseline wall time is UNSTABLE** (CV > 15%) - 10+ trials required")

    lines.extend([
        "",
        "---",
        "",
        "## Statistical Significance Assessment",
        "",
    ])

    # Sample size check
    total_n = len(baseline.wall_time.values) + len(cli.wall_time.values)
    if total_n < 30:
        lines.append(f"⚠️ **WARNING:** Total sample size (N={total_n}) is below 30.")
        lines.append("   Statistical significance tests (t-test, Mann-Whitney U) require larger samples.")
        lines.append("   Current analysis is descriptive only.")
    else:
        lines.append(f"✓ Sample size (N={total_n}) is adequate for statistical significance testing.")

    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "### For Future Benchmarking:",
        "",
    ])

    if cli.wall_time.cv < 5:
        lines.append("- Use **N=5** trials per scenario for stable metrics")
        lines.append("- Report mean ± 95% confidence interval")
    else:
        recommended_n = min(20, max(5, int(10 * (cli.wall_time.cv / 10))))
        lines.append(f"- Use **N={recommended_n}** trials per scenario to account for variance")
        lines.append("- Investigate sources of variance (system load, network, cache state)")

    lines.extend([
        "",
        "### For Reporting:",
        "",
        "- Always report: mean, median, std dev, CV, N",
        "- Include outlier analysis in benchmark reports",
        "- Use median for skewed distributions (high CV)",
        "- Use mean for normally distributed metrics (low CV)",
        "",
        "---",
        "",
        f"*Report generated by Agent 5 (Variance Analysis)*",
        f"*Data sources: {len(list(Path('data').glob('hn_runs*.csv')))} CSV files*",
    ])

    return "\n".join(lines)


def main():
    """Main entry point."""
    csv_dir = Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/data")

    print("Agent 5: Variance Analysis")
    print("=" * 50)
    print(f"Reading CSV files from: {csv_dir}")

    baseline, cli = read_csv_files(csv_dir)

    print(f"Baseline samples: {len(baseline.wall_time.values)}")
    print(f"CLI samples: {len(cli.wall_time.values)}")

    report = generate_markdown_report(baseline, cli)

    output_path = Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/hn_results_agent5_variance.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\nReport written to: {output_path}")

    # Print key stats
    print("\n" + "=" * 50)
    print("KEY STATISTICS:")
    print("=" * 50)
    print(f"Baseline Wall Time: CV = {baseline.wall_time.cv:.2f}%")
    print(f"CLI Wall Time: CV = {cli.wall_time.cv:.2f}%")
    print(f"CLI Avg Tool RTT: CV = {cli.avg_tool_rtt.cv:.2f}%")
    print(f"CLI P95 Tool RTT: CV = {cli.p95_tool_rtt.cv:.2f}%")


if __name__ == "__main__":
    main()
