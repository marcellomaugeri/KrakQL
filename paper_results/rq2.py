#!/usr/bin/env python
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# --- Configuration ---
RESULTS_DIR = Path("./results")
DEFAULT_BATCH_SIZE = 64

def parse_log_file(log_path: Path) -> Dict[str, Any]:
    """Parses a tool's log file to extract probe statistics."""
    stats = {
        "fields_found": 0,
        "field_batches": 0,
        "args_found": 0,
        "arg_batches": 0,
    }

    if not log_path.is_file():
        return "Log Not Found"

    try:
        log_content = log_path.read_text(encoding="utf-8")
        
        field_matches = re.findall(r"\(# New Fields\): (\d+)", log_content)
        arg_matches = re.findall(r"\(# New Args\): (\d+)", log_content)

        stats["field_batches"] = len(field_matches)
        stats["fields_found"] = sum(int(m) for m in field_matches)
        
        stats["arg_batches"] = len(arg_matches)
        stats["args_found"] = sum(int(m) for m in arg_matches)

        return stats

    except Exception as e:
        return f"Parse Error: {e}"

def aggregate_stats(stats_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates a list of stats dicts into a simple mean."""
    if not stats_list or not all(isinstance(s, dict) for s in stats_list):
        return "No Valid Data"

    aggregated = {}
    keys_to_agg = ["fields_found", "field_batches", "args_found", "arg_batches"]
    
    for key in keys_to_agg:
        values = [s.get(key, 0) for s in stats_list]
        aggregated[key] = np.mean(values)
        
    return aggregated

def analyze_experiment_runs(exp_dir: Path) -> Dict[str, Any]:
    """Analyzes experiment runs, grouping by base tool name."""
    raw_results: Dict[str, Dict[str, List]] = {}
    tool_dirs = [d for d in exp_dir.iterdir() if d.is_dir()]
    tool_groups: Dict[str, List[Path]] = {}

    for tool_dir in tool_dirs:
        base_name = re.match(r"([a-zA-Z]+)", tool_dir.name).group(1)
        if base_name not in tool_groups:
            tool_groups[base_name] = []
        tool_groups[base_name].append(tool_dir)
        
    allowed_groups = ["KrakQL", "clairvoyance"]
    tool_groups = {k: v for k, v in tool_groups.items() if k in allowed_groups}

    first_tool_name = next(iter(tool_groups))
    first_tool_path = tool_groups[first_tool_name][0]
    case_studies = sorted([d.name for d in first_tool_path.iterdir() if d.is_dir()])

    for cs_name in case_studies:
        raw_results[cs_name] = {}
        for group_name, dirs in tool_groups.items():
            raw_results[cs_name][group_name] = []
            for tool_run_dir in dirs:
                log_file_name = "krakql.log" if "krakql" in group_name.lower() else "clairvoyance.log"
                log_path = tool_run_dir / cs_name / log_file_name
                stats = parse_log_file(log_path)
                raw_results[cs_name][group_name].append(stats)

    aggregated_results = {}
    for cs_name, tool_data in raw_results.items():
        aggregated_results[cs_name] = {}
        for group_name, stats_list in tool_data.items():
            aggregated_results[cs_name][group_name] = aggregate_stats(stats_list)
            
    return aggregated_results, ['clairvoyance', 'KrakQL']

def format_batches(value: float) -> str:
    """Formats batch numbers, using 'k' for thousands."""
    if value >= 1000:
        return f"{value/1000:.0f}k"
    return f"{value:.0f}"

def format_rate(found: float, batches: float, batch_size: int) -> str:
    """Formats the discovery rate percentage."""
    if batches == 0 or batch_size == 0:
        return "--"
    
    total_candidates = batches * batch_size
    rate = (found / total_candidates * 100) if total_candidates > 0 else 0.0
    
    if 0 < rate < 0.01:
        return "<0.01\\%"
    return f"{rate:.2f}\\%"

def print_latex_table(results: Dict[str, Any], tools: List[str], batch_size: int):
    """Prints the final results as a LaTeX table."""
    
    # --- LaTeX Preamble ---
    print("\\begin{table*}[t]")
    print("\\centering")
    print(f"\\caption{{Discovery efficiency: Elements found per batch (batch size = {batch_size} names)}}")
    print("\\label{tab:efficiency}")
    print("\\resizebox{\\textwidth}{!}{%")
    print("\\begin{tabular}{l|ccc|ccc|ccc|ccc}")
    print("\\toprule")

    # --- Headers ---
    print(" & \\multicolumn{6}{c|}{\\textbf{Clairvoyance}} & \\multicolumn{6}{c}{\\textbf{KrakQL}} \\\\")
    print("\\cmidrule{2-13}")
    print(" & \\multicolumn{3}{c|}{\\textbf{Fields}} & \\multicolumn{3}{c|}{\\textbf{Arguments}} & \\multicolumn{3}{c|}{\\textbf{Fields}} & \\multicolumn{3}{c}{\\textbf{Arguments}} \\\\")
    print("\\cmidrule{2-4} \\cmidrule{5-7} \\cmidrule{8-10} \\cmidrule{11-13}")
    print("\\textbf{Target} & \\textbf{Found} & \\textbf{Batches} & \\textbf{Rate} & \\textbf{Found} & \\textbf{Batches} & \\textbf{Rate} & \\textbf{Found} & \\textbf{Batches} & \\textbf{Rate} & \\textbf{Found} & \\textbf{Batches} & \\textbf{Rate} \\\\")
    print("\\midrule")

    # --- Totals Initialization ---
    totals = {tool: {"fields_found": 0, "field_batches": 0, "args_found": 0, "arg_batches": 0} for tool in tools}

    # --- Data Rows ---
    for cs_name, tool_results in sorted(results.items()):
        row_cells = [cs_name.replace('_', '-')]
        # Enforce the correct order to match the hardcoded headers
        for tool_name in ['clairvoyance', 'KrakQL']:
            result = tool_results.get(tool_name)
            
            if isinstance(result, dict):
                # Fields
                ff, fb = result.get('fields_found', 0), result.get('field_batches', 0)
                row_cells.append(f"{ff:.0f}")
                row_cells.append(format_batches(fb))
                row_cells.append(format_rate(ff, fb, batch_size))
                totals[tool_name]['fields_found'] += ff
                totals[tool_name]['field_batches'] += fb

                # Args
                af, ab = result.get('args_found', 0), result.get('arg_batches', 0)
                row_cells.append(f"{af:.0f}")
                row_cells.append(format_batches(ab))
                row_cells.append(format_rate(af, ab, batch_size))
                totals[tool_name]['args_found'] += af
                totals[tool_name]['arg_batches'] += ab
            else:
                row_cells.extend(["--"] * 6)
        
        print(" & ".join(row_cells) + " \\\\")

    # --- Total Row ---
    print("\\midrule")
    total_row_cells = ["\\textbf{Total}"]
    # Enforce the correct order for the total row as well
    for tool_name in ['clairvoyance', 'KrakQL']:
        # Fields Total
        ff_total, fb_total = totals[tool_name]['fields_found'], totals[tool_name]['field_batches']
        total_row_cells.append(f"{ff_total:,.0f}")
        total_row_cells.append(format_batches(fb_total))
        total_row_cells.append(format_rate(ff_total, fb_total, batch_size))
        
        # Args Total
        af_total, ab_total = totals[tool_name]['args_found'], totals[tool_name]['arg_batches']
        total_row_cells.append(f"{af_total:,.0f}")
        total_row_cells.append(format_batches(ab_total))
        total_row_cells.append(format_rate(af_total, ab_total, batch_size))
        
    print(" & ".join(total_row_cells) + " \\\\")

    # --- LaTeX Postamble ---
    print("\\bottomrule")
    print("\\end{tabular}}")
    print("\\end{table*}")


def main():
    parser = argparse.ArgumentParser(description="Run probe success rate analysis for paper results (RQ2).")
    parser.add_argument(
        "results_folder", type=str, nargs='?', default=str(RESULTS_DIR),
        help=f"Path to the experiment results folder. Default: {RESULTS_DIR}",
    )
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
        help=f"Number of candidates per probe batch. Default: {DEFAULT_BATCH_SIZE}",
    )
    args = parser.parse_args()

    experiment_dir = Path(args.results_folder)
    if not experiment_dir.is_dir():
        print(f"Error: Results directory not found at '{experiment_dir}'", file=sys.stderr)
        return

    analysis_results, tools = analyze_experiment_runs(experiment_dir)
    print_latex_table(analysis_results, tools, args.batch_size)

if __name__ == "__main__":
    main()