#!/usr/bin/env python
# paper_results/rq1.py
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
import numpy as np
from scipy.stats import wilcoxon
from graphql.language import (
    parse,
    DocumentNode,
    ObjectTypeDefinitionNode,
    InputObjectTypeDefinitionNode,
    FieldDefinitionNode,
    InputValueDefinitionNode,
    NamedTypeNode,
    ListTypeNode,
    NonNullTypeNode,
)

# --- Configuration ---
RESULTS_DIR = Path("./results")
GROUND_TRUTH_BASE_DIR = RESULTS_DIR / "ground_truth"
RETRIEVED_SCHEMA_FILE = "schema.gql" # In older versions it was schema.graphql
GROUND_TRUTH_SCHEMA_FILE = "schema.graphql"

# --- Exact copy of schema coverage functions ---
SchemaElements = Dict[str, Any]

def type_node_to_str(node) -> str:
    """Recursively converts a type node from the AST to a string."""
    if isinstance(node, NamedTypeNode):
        return node.name.value
    if isinstance(node, ListTypeNode):
        return f"[{type_node_to_str(node.type)}]"
    if isinstance(node, NonNullTypeNode):
        return f"{type_node_to_str(node.type)}!"
    return ""

def extract_schema_elements(sdl: str) -> SchemaElements:
    """
    Parses a GraphQL SDL and extracts its components into a clean, structured dictionary.
    """
    elements: SchemaElements = {
        "types": set(),
        "input_types": set(),
        "fields": {},      # Unified: { "TypeName": { "fieldName": "FieldType" } }
        "arguments": {},   # Only for field arguments: { "TypeName": { "fieldName": { "argName": "ArgType" } } }
    }

    if not sdl or not sdl.strip():
        return elements

    doc: DocumentNode = parse(sdl)
    for definition in doc.definitions:
        if isinstance(definition, ObjectTypeDefinitionNode):
            type_name = definition.name.value
            if type_name.startswith("__"): continue
            
            elements["types"].add(type_name)
            elements["fields"].setdefault(type_name, {})
            elements["arguments"].setdefault(type_name, {})
            
            if definition.fields:
                for field in definition.fields:
                    assert isinstance(field, FieldDefinitionNode)
                    field_name = field.name.value
                    elements["fields"][type_name][field_name] = type_node_to_str(field.type)
                    
                    if field.arguments:
                        elements["arguments"][type_name].setdefault(field_name, {})
                        for arg in field.arguments:
                            assert isinstance(arg, InputValueDefinitionNode)
                            arg_name = arg.name.value
                            elements["arguments"][type_name][field_name][arg_name] = type_node_to_str(arg.type)

        elif isinstance(definition, InputObjectTypeDefinitionNode):
            type_name = definition.name.value
            if type_name.startswith("__"): continue

            elements["input_types"].add(type_name)
            elements["fields"].setdefault(type_name, {})

            if definition.fields:
                for in_field in definition.fields:
                    assert isinstance(in_field, InputValueDefinitionNode)
                    field_name = in_field.name.value
                    elements["fields"][type_name][field_name] = type_node_to_str(in_field.type)
    
    return elements

def calculate_coverage(target: SchemaElements, retrieved: SchemaElements) -> Dict[str, Any]:
    """
    (Corrected Version)
    Calculates coverage using the clean data structure from the new extract_schema_elements.
    """
    total_types = len(target["types"])
    total_input_types = len(target["input_types"])
    total_fields = sum(len(fields) for fields in target["fields"].values())
    total_args = sum(len(args) for field_args in target["arguments"].values() for args in field_args.values())

    found_types = len(target["types"].intersection(retrieved["types"]))
    found_input_types = len(target["input_types"].intersection(retrieved["input_types"]))

    found_fields = 0
    for type_name, fields in target["fields"].items():
        if type_name in retrieved["fields"]:
            for field_name, field_type in fields.items():
                if field_name in retrieved["fields"][type_name] and retrieved["fields"][type_name][field_name] == field_type:
                    found_fields += 1

    found_args = 0
    for type_name, field_args in target["arguments"].items():
        if type_name in retrieved["arguments"]:
            for field_name, args in field_args.items():
                if field_name in retrieved["arguments"][type_name]:
                    for arg_name, arg_type in args.items():
                        if arg_name in retrieved["arguments"][type_name][field_name]:
                            found_args += 1

    overall_found = found_types + found_fields + found_args
    overall_total = total_types + total_fields + total_args

    return {
        "counts": {
            "types": (found_types, total_types),
            "input_types": (found_input_types, total_input_types),
            "fields": (found_fields, total_fields),
            "arguments": (found_args, total_args),
            "overall": (overall_found, overall_total),
        },
        "percentages": {
            "types": (found_types / total_types * 100) if total_types > 0 else 100.0,
            "input_types": (found_input_types / total_input_types * 100) if total_input_types > 0 else 100.0,
            "fields": (found_fields / total_fields * 100) if total_fields > 0 else 100.0,
            "arguments": (found_args / total_args * 100) if total_args > 0 else 100.0,
            "overall": (overall_found / overall_total * 100) if overall_total > 0 else 100.0,
        }
    }

# --- Statistical Functions ---

def vargha_delaney_a12(sample1: List[float], sample2: List[float]) -> float:
    """
    Computes the Vargha-Delaney A12 effect size.
    A12 > 0.5 means sample1 is stochastically larger than sample2.
    """
    if not sample1 or not sample2:
        return 0.5
    
    m, n = len(sample1), len(sample2)
    rank_sum = 0
    
    all_samples = sorted([(x, 1) for x in sample1] + [(y, 2) for y in sample2])
    
    ranks = {}
    for i, (value, sample_id) in enumerate(all_samples):
        ranks.setdefault(value, []).append(i + 1)

    avg_ranks = {val: sum(r_list) / len(r_list) for val, r_list in ranks.items()}

    for x in sample1:
        rank_sum += avg_ranks[x]
        
    return (rank_sum / m - (m + 1) / 2) / n

def p_value_to_stars(p_value: float) -> str:
    """Converts a p-value to a star rating."""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""

# --- Main Analysis Logic ---

def analyze_and_aggregate(results_dir: Path, ground_truth_dir: Path) -> Dict:
    """Main function to drive the analysis."""
    
    # {cs_name: {tool_group: [coverage_data_run1, ...], ...}}
    raw_results = {}
    
    all_tool_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name != 'ground_truth']
    
    # Correctly group tools
    tool_groups = {
        'clairvoyance': [d for d in all_tool_dirs if d.name == 'clairvoyance'],
        'KrakQL': sorted([d for d in all_tool_dirs if d.name.startswith('KrakQL')])
    }

    print(f"Found tool groups: {list(tool_groups.keys())}")
    print(f"KrakQL runs found: {len(tool_groups['KrakQL'])}")


    # Use clairvoyance to find case studies
    case_studies = sorted([d.name for d in (results_dir / "clairvoyance").iterdir() if d.is_dir()])
    print(f"Found {len(case_studies)} case studies: {', '.join(case_studies)}\n")

    for cs_name in case_studies:
        raw_results[cs_name] = {}
        
        # Load ground truth
        gt_path = ground_truth_dir / cs_name / GROUND_TRUTH_SCHEMA_FILE
        if not gt_path.is_file():
            print(f"  - WARNING: Ground truth for '{cs_name}' not found. Skipping.")
            continue
        try:
            target_sdl = gt_path.read_text(encoding="utf-8")
            target_elements = extract_schema_elements(target_sdl)
        except Exception as e:
            print(f"  - ERROR: Could not parse ground truth for '{cs_name}': {e}")
            continue

        for group_name, dirs in tool_groups.items():
            raw_results[cs_name][group_name] = []
            for tool_run_dir in dirs:
                retrieved_path = tool_run_dir / cs_name / RETRIEVED_SCHEMA_FILE
                if not retrieved_path.is_file():
                    # Fallback for older experiments
                    retrieved_path = tool_run_dir / cs_name / "schema.graphql"

                if not retrieved_path.is_file():
                    raw_results[cs_name][group_name].append("Not Found")
                    continue
                
                try:
                    retrieved_sdl = retrieved_path.read_text(encoding="utf-8")
                    retrieved_elements = extract_schema_elements(retrieved_sdl)
                    coverage_data = calculate_coverage(target_elements, retrieved_elements)
                    raw_results[cs_name][group_name].append(coverage_data)
                except Exception as e:
                    raw_results[cs_name][group_name].append(f"Parse Error: {e}")

    # --- Aggregation Step ---
    aggregated_results = {}
    for cs_name, cs_data in raw_results.items():
        aggregated_results[cs_name] = {}
        for group_name, runs in cs_data.items():
            valid_runs = [r for r in runs if isinstance(r, dict)]
            if not valid_runs:
                aggregated_results[cs_name][group_name] = "Error"
                continue

            if group_name == 'clairvoyance':
                # Clairvoyance has only one run
                aggregated_results[cs_name][group_name] = valid_runs[0]
            else: # Aggregate KrakQL runs
                agg_data = {"counts": {}, "percentages": {}, "raw_counts": {}}
                for metric in ["types", "fields", "arguments", "overall"]:
                    # Raw counts for total calculation
                    raw_found = [r["counts"][metric][0] for r in valid_runs]
                    raw_total = [r["counts"][metric][1] for r in valid_runs]
                    agg_data["raw_counts"][metric] = (raw_found, raw_total)

                    # Mean counts for display
                    agg_data["counts"][metric] = (np.mean(raw_found), raw_total[0] if raw_total else 0)

                    # Percentages
                    perc_values = [r["percentages"][metric] for r in valid_runs]
                    agg_data["percentages"][metric] = {
                        "mean": np.mean(perc_values),
                        "std": np.std(perc_values),
                        "cv": (np.std(perc_values) / np.mean(perc_values) * 100) if np.mean(perc_values) > 0 else 0,
                        "range": (np.min(perc_values), np.max(perc_values)),
                        "raw": perc_values
                    }
                aggregated_results[cs_name][group_name] = agg_data

    num_krakql_runs = len(tool_groups.get('KrakQL', []))
    return aggregated_results, ['clairvoyance', 'KrakQL'], num_krakql_runs


def print_detailed_coverage_table(results: Dict, tools: List[str], num_krakql_runs: int):
    """Prints the main detailed coverage table."""
    print("\n" + "="*120)
    print("Table 1: Detailed Schema Coverage Comparison (KrakQL: mean of n runs per target)".center(120))
    print("="*120 + "\n")

    metrics = ["types", "fields", "arguments", "overall"]
    cs_col_width = 15
    metric_col_width = 22

    # Headers
    header1 = f"{'Target':<{cs_col_width}}"
    header2 = f"{'':<{cs_col_width}}"
    separator = ["-" * cs_col_width]
    
    # Correct tool order
    tool_order = ['clairvoyance', 'KrakQL']

    for tool in tool_order:
        tool_name = f"KrakQL (n={num_krakql_runs})" if "KrakQL" in tool else "Clairvoyance"
        header1 += f" | {tool_name.center(len(metrics) * (metric_col_width + 3) - 3)}"
        for metric in metrics:
            header2 += f" | {metric.capitalize():^{metric_col_width}}"
            separator.append("-" * metric_col_width)
    
    print(header1)
    print(header2)
    print("-+-".join(separator))

    # --- Initialize Totals ---
    totals = {
        tool: {m: [0, 0] for m in metrics} for tool in tool_order
    }

    # Data Rows
    for cs_name, cs_data in sorted(results.items()):
        row = f"{cs_name:<{cs_col_width}}"
        for tool in tool_order:
            data = cs_data.get(tool)
            if not isinstance(data, dict):
                row += f" | {'Data Error'.center(metric_col_width)}" * len(metrics)
                continue

            for metric in metrics:
                if tool == 'clairvoyance':
                    found, total = data["counts"][metric]
                    perc = data["percentages"][metric]
                    cell = f"{found}/{total} ({perc:.0f}%)"
                    totals[tool][metric][0] += found
                    totals[tool][metric][1] += total
                else: # KrakQL
                    found_mean, total = data["counts"][metric]
                    perc_mean = data["percentages"][metric]["mean"]
                    cell = f"{found_mean:.1f}/{int(total)} ({perc_mean:.0f}%)"
                    
                    # Accumulate the mean 'found' and unique 'total' for the final row
                    totals[tool][metric][0] += found_mean
                    totals[tool][metric][1] += total

                row += f" | {cell:^{metric_col_width}}"
        print(row)
    
    print("-+-".join(separator))
    # Total row
    total_row = f"{'Total':<{cs_col_width}}"
    for tool in tool_order:
        for metric in metrics:
            found, total = totals[tool][metric]
            perc = (found / total * 100) if total > 0 else 0
            
            if tool == 'clairvoyance':
                cell = f"{int(found)}/{int(total)} ({perc:.1f}%)"
            else: # KrakQL
                cell = f"{found:.1f}/{int(total)} ({perc:.1f}%)"

            total_row += f" | {cell:^{metric_col_width}}"
    print(total_row)


def print_statistical_analysis_table(results: Dict, num_krakql_runs: int):
    """Prints the second table with statistical analysis."""
    print("\n" + "="*90)
    print("Table 2: Statistical Analysis and Relative Improvement".center(90))
    print("="*90 + "\n")

    headers = ["Target", "Clairvoyance", "Mean±SD", "CV%", "Relative Improvement %"]
    col_widths = [18, 14, 20, 10, 22]
    
    # Header construction
    header_line = f"{headers[0]:<{col_widths[0]}} | {headers[1]:^{col_widths[1]}} | "
    header_line += f"{f'KrakQL (n={num_krakql_runs})':^{col_widths[2] + col_widths[3] + 3}} | "
    header_line += f"{headers[4]:^{col_widths[4]}}"
    
    sub_header_line = f"{'':<{col_widths[0]}} | {'Overall':^{col_widths[1]}} | "
    sub_header_line += f"{headers[2]:^{col_widths[2]}} | {headers[3]:^{col_widths[3]}} | "
    sub_header_line += f"{'vs. Clairvoyance':^{col_widths[4]}}"

    print(header_line)
    print(sub_header_line)
    print(" | ".join(["-" * w for w in col_widths]))

    # For overall stats
    clair_overall_means = []
    krakql_overall_means = []

    for cs_name, cs_data in sorted(results.items()):
        clair_data = cs_data.get('clairvoyance')
        krakql_data = cs_data.get('KrakQL')

        if not isinstance(clair_data, dict) or not isinstance(krakql_data, dict):
            continue

        clair_overall = clair_data["percentages"]["overall"]
        krakql_overall_stats = krakql_data["percentages"]["overall"]
        
        clair_overall_means.append(clair_overall)
        krakql_overall_means.append(krakql_overall_stats["mean"])

        # Calculate relative improvement
        if clair_overall > 0:
            rel_improvement = ((krakql_overall_stats['mean'] - clair_overall) / clair_overall) * 100
            rel_uncertainty = (krakql_overall_stats['std'] / clair_overall) * 100
            rel_imp_str = f"{rel_improvement:+.1f} ± {rel_uncertainty:.1f}%"
        else:
            rel_imp_str = "N/A (div by zero)"


        row = [
            f"{cs_name:<{col_widths[0]}}",
            f"{clair_overall:.1f}%".center(col_widths[1]),
            f"{krakql_overall_stats['mean']:.1f}±{krakql_overall_stats['std']:.1f}%".center(col_widths[2]),
            f"{krakql_overall_stats['cv']:.1f}%".center(col_widths[3]),
            rel_imp_str.center(col_widths[4]),
        ]
        print(" | ".join(row))

    # --- Overall Statistics ---
    print(" | ".join(["-" * w for w in col_widths]))
    
    # Paired Wilcoxon test on the means of overall coverage per case study
    try:
        # Filter out pairs where Clairvoyance is 0 to avoid meaningless stats
        filtered_clair = []
        filtered_krakql = []
        for c, k in zip(clair_overall_means, krakql_overall_means):
            if c > 0:
                filtered_clair.append(c)
                filtered_krakql.append(k)

        if len(filtered_clair) > 1:
            p_value = wilcoxon(filtered_clair, filtered_krakql).pvalue
            p_str = f"{p_value:.3f}{p_value_to_stars(p_value)}"
        else:
            p_str = "N/A (insufficient data)"
    except Exception:
        p_str = "N/A"
    
    # A12 effect size on the same samples
    a12 = vargha_delaney_a12(krakql_overall_means, clair_overall_means)
    a12_str = f"{a12:.2f}"

    print(f"\nOverall Paired Statistics (Clairvoyance vs. KrakQL):")
    print(f"  - Wilcoxon p-value: {p_str}")
    print(f"  - Vargha-Delaney Â₁₂: {a12_str}")


def main():
    parser = argparse.ArgumentParser(description="Run schema coverage analysis for paper results (RQ1).")
    parser.add_argument(
        "results_folder",
        type=str,
        nargs='?',
        default=str(RESULTS_DIR),
        help=f"Path to the experiment results folder. Default: {RESULTS_DIR}",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_folder)
    if not results_dir.is_dir():
        print(f"Error: Results directory not found at '{results_dir}'")
        return
    
    ground_truth_dir = results_dir / "ground_truth"
    if not ground_truth_dir.is_dir():
        print(f"Error: Ground truth directory not found at '{ground_truth_dir}'")
        return

    aggregated_results, tools, num_krakql_runs = analyze_and_aggregate(results_dir, ground_truth_dir)
    
    print_detailed_coverage_table(aggregated_results, tools, num_krakql_runs)
    print_statistical_analysis_table(aggregated_results, num_krakql_runs)


if __name__ == "__main__":
    main()
