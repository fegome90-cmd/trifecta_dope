"""Telemetry ASCII Charts.

Generate simple ASCII charts for terminal display.
"""

from typing import List, Tuple


def draw_line_chart(
    data: List[Tuple[str, int]],
    width: int = 60,
    height: int = 10
) -> str:
    """Draw ASCII line chart.

    Args:
        data: List of (label, value) tuples
        width: Chart width in characters
        height: Chart height in lines

    Returns:
        ASCII chart string
    """
    if not data:
        return "No data to display"

    # Extract values
    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    if not values:
        return "No data to display"

    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        # All same value, draw flat line
        max_val += 1

    # Create Y axis scale
    y_scale = height / (max_val - min_val)

    # Build chart
    lines = []

    # Y axis labels
    for i in range(height, -1, -1):
        val_at_level = min_val + (height - i) / height * (max_val - min_val)
        label = f"{int(val_at_level):>4} ┤" if i % 2 == 0 else "     ┤"

        # Build line
        line_chars = []
        for val in values:
            scaled = int((val - min_val) * y_scale)
            if scaled >= height - i:
                line_chars.append("───")
            else:
                line_chars.append("   ")

        lines.append(label + "".join(line_chars))

    # X axis labels
    x_label = "     " + "".join(f" {l:<3}" for l in labels)
    lines.append("     └" + "─" * (3 * len(labels)) + "→")

    return "\n".join(lines)


def draw_bar_chart(
    data: List[Tuple[str, int]],
    max_bar_width: int = 40
) -> str:
    """Draw ASCII bar chart.

    Args:
        data: List of (label, value) tuples
        max_bar_width: Maximum width of bar

    Returns:
        ASCII chart string
    """
    if not data:
        return "No data to display"

    # Find max value for scaling
    max_val = max(d[1] for d in data) if data else 1

    # Calculate label width
    max_label_len = max(len(d[0]) for d in data) if data else 0

    lines = []
    for label, value in data:
        # Scale bar width
        bar_width = int(value / max_val * max_bar_width)
        bar = "█" * bar_width

        # Format line
        line = f"{label:<{max_label_len}} │ {value:>4} {bar}"
        lines.append(line)

    return "\n".join(lines)


def draw_histogram(
    data: List[int],
    bins: int = 10
) -> str:
    """Draw ASCII histogram.

    Args:
        data: List of numeric values
        bins: Number of histogram bins

    Returns:
        ASCII histogram string
    """
    if not data:
        return "No data to display"

    min_val = min(data)
    max_val = max(data)

    if max_val == min_val:
        max_val += 1

    bin_size = (max_val - min_val) / bins
    counts = [0] * bins

    # Count values in each bin
    for val in data:
        bin_idx = int((val - min_val) / bin_size)
        if bin_idx >= bins:
            bin_idx = bins - 1
        counts[bin_idx] += 1

    # Find max count for scaling
    max_count = max(counts) if counts else 1

    # Draw histogram
    lines = []
    for i, count in enumerate(counts):
        bin_start = min_val + i * bin_size
        bin_end = bin_start + bin_size
        bar_width = int(count / max_count * 40)

        bar = "█" * bar_width
        line = f"{bin_start:>6.1f} - {bin_end:>6.1f} │ {count:>4} {bar}"
        lines.append(line)

    return "\n".join(lines)


def generate_chart(
    segment_path,
    chart_type: str = "hits",
    days: int = 7
) -> str:
    """Generate chart from telemetry data.

    Args:
        segment_path: Path to segment directory
        chart_type: Type of chart ("hits", "latency", "errors", "commands")
        days: Number of days to include

    Returns:
        ASCII chart string
    """
    from .telemetry_reports import load_telemetry_data, filter_events_by_date

    events, _, _ = load_telemetry_data(segment_path)
    events = filter_events_by_date(events, days)

    if chart_type == "commands":
        # Bar chart of command usage
        from collections import Counter
        cmd_counts = Counter(e["cmd"] for e in events)
        data = [(cmd, count) for cmd, count in cmd_counts.most_common(10)]

        title = f"Command Usage (Last {days} days)"
        chart = draw_bar_chart(data)

    elif chart_type == "hits":
        # Daily search hits
        from datetime import datetime, timedelta, timezone
        from collections import defaultdict

        daily_hits = defaultdict(int)
        for event in events:
            if event["cmd"] == "ctx.search":
                try:
                    ts = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
                    day = ts.date().isoformat()
                    hits = event.get("result", {}).get("hits", 0)
                    daily_hits[day] += hits
                except (KeyError, ValueError):
                    pass

        data = list(daily_hits.items())
        if not data:
            return "No search data found"

        title = f"Daily Search Hits (Last {days} days)"
        chart = draw_line_chart(data)

    elif chart_type == "latency":
        # Latency distribution
        latencies = [e.get("timing_ms", 0) for e in events if e.get("timing_ms", 0) > 0]

        if not latencies:
            return "No latency data found"

        title = f"Latency Distribution (Last {days} days)"
        chart = draw_histogram(latencies, bins=10)

    else:
        return f"Unknown chart type: {chart_type}"

    lines = [title, "", chart] if chart else [title, "No data"]
    return "\n".join(lines)
