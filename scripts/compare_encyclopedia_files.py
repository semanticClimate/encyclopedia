#!/usr/bin/env python3
"""
Compare encyclopedia files between amilib and encyclopedia projects.

This script analyzes structural differences (classes, methods, functions)
between source files in amilib and target files in encyclopedia.

Usage:
    python scripts/compare_encyclopedia_files.py
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def get_file_info(filepath: Path) -> Dict:
    """Extract structural information from a Python file."""
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}
    except Exception as e:
        return {"error": f"Error reading file: {e}"}
    
    info = {
        "filepath": str(filepath),
        "line_count": len(content.splitlines()),
        "classes": {},
        "functions": [],
        "imports": [],
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            class_methods = []
            static_methods = []
            properties = []
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
                elif isinstance(item, ast.AsyncFunctionDef):
                    methods.append(f"async {item.name}")
            
            # Get decorators
            decorators = [ast.unparse(d) if hasattr(ast, 'unparse') else d.id if isinstance(d, ast.Name) else str(d) 
                         for d in node.decorator_list]
            
            info["classes"][node.name] = {
                "methods": sorted(methods),
                "line_start": node.lineno,
                "line_end": getattr(node, 'end_lineno', node.lineno),
                "decorators": decorators,
            }
        
        elif isinstance(node, ast.FunctionDef) and not any(
            isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
            if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
        ):
            # Top-level function
            info["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "args": [arg.arg for arg in node.args.args],
            })
        
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    info["imports"].append(f"import {alias.name}")
            else:
                module = node.module or ""
                names = ", ".join([alias.name for alias in node.names])
                info["imports"].append(f"from {module} import {names}")
    
    return info


def compare_classes(class1: Dict, class2: Dict, name: str) -> Dict:
    """Compare two class definitions."""
    methods1 = set(class1.get("methods", []))
    methods2 = set(class2.get("methods", []))
    
    return {
        "class_name": name,
        "in_both": sorted(methods1 & methods2),
        "only_in_source": sorted(methods1 - methods2),
        "only_in_target": sorted(methods2 - methods1),
        "source_line_count": class1.get("line_end", 0) - class1.get("line_start", 0) + 1,
        "target_line_count": class2.get("line_end", 0) - class2.get("line_start", 0) + 1,
    }


def compare_files(source_path: Path, target_path: Path) -> Dict:
    """Compare two Python files."""
    source_info = get_file_info(source_path)
    target_info = get_file_info(target_path)
    
    if "error" in source_info:
        return {"error": f"Source: {source_info['error']}"}
    if "error" in target_info:
        return {"error": f"Target: {target_info['error']}"}
    
    comparison = {
        "source_file": str(source_path),
        "target_file": str(target_path),
        "source_line_count": source_info["line_count"],
        "target_line_count": target_info["line_count"],
        "line_count_diff": target_info["line_count"] - source_info["line_count"],
        "classes": {},
        "top_level_functions": {},
        "imports": {
            "source": source_info["imports"],
            "target": target_info["imports"],
        },
    }
    
    # Compare classes
    source_classes = set(source_info["classes"].keys())
    target_classes = set(target_info["classes"].keys())
    
    for class_name in source_classes | target_classes:
        if class_name in source_info["classes"] and class_name in target_info["classes"]:
            comparison["classes"][class_name] = compare_classes(
                source_info["classes"][class_name],
                target_info["classes"][class_name],
                class_name
            )
        elif class_name in source_info["classes"]:
            comparison["classes"][class_name] = {
                "class_name": class_name,
                "status": "only_in_source",
                "methods": source_info["classes"][class_name]["methods"],
            }
        else:
            comparison["classes"][class_name] = {
                "class_name": class_name,
                "status": "only_in_target",
                "methods": target_info["classes"][class_name]["methods"],
            }
    
    # Compare top-level functions
    source_funcs = {f["name"]: f for f in source_info["functions"]}
    target_funcs = {f["name"]: f for f in target_info["functions"]}
    
    all_funcs = set(source_funcs.keys()) | set(target_funcs.keys())
    for func_name in all_funcs:
        if func_name in source_funcs and func_name in target_funcs:
            comparison["top_level_functions"][func_name] = {
                "status": "in_both",
                "source_line": source_funcs[func_name]["line"],
                "target_line": target_funcs[func_name]["line"],
            }
        elif func_name in source_funcs:
            comparison["top_level_functions"][func_name] = {
                "status": "only_in_source",
                "line": source_funcs[func_name]["line"],
            }
        else:
            comparison["top_level_functions"][func_name] = {
                "status": "only_in_target",
                "line": target_funcs[func_name]["line"],
            }
    
    return comparison


def print_comparison_report(comparison: Dict):
    """Print a formatted comparison report."""
    if "error" in comparison:
        print(f"ERROR: {comparison['error']}")
        return
    
    print("=" * 80)
    print("ENCYCLOPEDIA FILE COMPARISON REPORT")
    print("=" * 80)
    print()
    print(f"Source: {comparison['source_file']}")
    print(f"Target: {comparison['target_file']}")
    print()
    print(f"Line Count:")
    print(f"  Source: {comparison['source_line_count']:,} lines")
    print(f"  Target: {comparison['target_line_count']:,} lines")
    diff = comparison['line_count_diff']
    if diff > 0:
        print(f"  Difference: +{diff:,} lines in target (target is larger)")
    elif diff < 0:
        print(f"  Difference: {diff:,} lines (target is smaller)")
    else:
        print(f"  Difference: Same line count")
    print()
    
    # Classes comparison
    print("CLASSES:")
    print("-" * 80)
    for class_name, class_info in sorted(comparison["classes"].items()):
        if "status" in class_info:
            status = class_info["status"]
            if status == "only_in_source":
                print(f"  {class_name}: ONLY IN SOURCE ({len(class_info['methods'])} methods)")
            elif status == "only_in_target":
                print(f"  {class_name}: ONLY IN TARGET ({len(class_info['methods'])} methods)")
        else:
            only_source = class_info.get("only_in_source", [])
            only_target = class_info.get("only_in_target", [])
            in_both = class_info.get("in_both", [])
            
            print(f"  {class_name}:")
            print(f"    Methods in both: {len(in_both)}")
            if only_source:
                print(f"    Methods only in SOURCE ({len(only_source)}):")
                for method in only_source[:10]:  # Show first 10
                    print(f"      - {method}")
                if len(only_source) > 10:
                    print(f"      ... and {len(only_source) - 10} more")
            if only_target:
                print(f"    Methods only in TARGET ({len(only_target)}):")
                for method in only_target[:10]:  # Show first 10
                    print(f"      - {method}")
                if len(only_target) > 10:
                    print(f"      ... and {len(only_target) - 10} more")
            
            line_diff = class_info.get("target_line_count", 0) - class_info.get("source_line_count", 0)
            if line_diff != 0:
                print(f"    Line count difference: {line_diff:+d} lines")
    print()
    
    # Top-level functions
    if comparison["top_level_functions"]:
        print("TOP-LEVEL FUNCTIONS:")
        print("-" * 80)
        for func_name, func_info in sorted(comparison["top_level_functions"].items()):
            status = func_info["status"]
            if status == "only_in_source":
                print(f"  {func_name}: ONLY IN SOURCE (line {func_info['line']})")
            elif status == "only_in_target":
                print(f"  {func_name}: ONLY IN TARGET (line {func_info['line']})")
            else:
                print(f"  {func_name}: IN BOTH (source: line {func_info['source_line']}, target: line {func_info['target_line']})")
        print()
    
    # Import differences
    source_imports = set(comparison["imports"]["source"])
    target_imports = set(comparison["imports"]["target"])
    only_source_imports = source_imports - target_imports
    only_target_imports = target_imports - source_imports
    
    if only_source_imports or only_target_imports:
        print("IMPORT DIFFERENCES:")
        print("-" * 80)
        if only_source_imports:
            print(f"  Imports only in SOURCE ({len(only_source_imports)}):")
            for imp in sorted(only_source_imports)[:10]:
                print(f"    - {imp}")
            if len(only_source_imports) > 10:
                print(f"    ... and {len(only_source_imports) - 10} more")
        if only_target_imports:
            print(f"  Imports only in TARGET ({len(only_target_imports)}):")
            for imp in sorted(only_target_imports)[:10]:
                print(f"    - {imp}")
            if len(only_target_imports) > 10:
                print(f"    ... and {len(only_target_imports) - 10} more")
        print()
    
    print("=" * 80)


def main():
    """Main comparison function."""
    # Define file pairs to compare
    comparisons = [
        {
            "name": "Core Encyclopedia",
            "source": Path("..", "amilib", "amilib", "ami_encyclopedia.py"),
            "target": Path("encyclopedia", "core", "encyclopedia.py"),
        },
        {
            "name": "Clustering",
            "source": Path("..", "amilib", "amilib", "ami_encyclopedia_cluster.py"),
            "target": Path("encyclopedia", "clustering", "clusterer.py"),
        },
        {
            "name": "Utilities (Link Extractor)",
            "source": Path("..", "amilib", "amilib", "ami_encyclopedia_util.py"),
            "target": Path("encyclopedia", "utils", "link_extractor.py"),
        },
        {
            "name": "CLI Arguments",
            "source": Path("..", "amilib", "amilib", "ami_encyclopedia_args.py"),
            "target": Path("encyclopedia", "cli", "args.py"),
        },
    ]
    
    # Get script directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    all_results = []
    
    for comp in comparisons:
        source_path = Path(project_root, *Path(comp["source"]).parts)
        target_path = Path(project_root, *Path(comp["target"]).parts)
        
        print(f"\n{'='*80}")
        print(f"COMPARING: {comp['name']}")
        print(f"{'='*80}\n")
        
        comparison = compare_files(source_path, target_path)
        print_comparison_report(comparison)
        
        all_results.append({
            "name": comp["name"],
            "comparison": comparison,
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    for result in all_results:
        comp = result["comparison"]
        if "error" in comp:
            print(f"{result['name']}: ERROR - {comp['error']}")
        else:
            diff = comp["line_count_diff"]
            status = "LARGER" if diff > 0 else "SMALLER" if diff < 0 else "SAME SIZE"
            print(f"{result['name']}:")
            print(f"  Source: {comp['source_line_count']:,} lines")
            print(f"  Target: {comp['target_line_count']:,} lines")
            print(f"  Difference: {diff:+,d} lines (target is {status})")
            
            # Count method differences
            total_only_source = 0
            total_only_target = 0
            for class_info in comp["classes"].values():
                if "only_in_source" in class_info:
                    total_only_source += len(class_info["only_in_source"])
                if "only_in_target" in class_info:
                    total_only_target += len(class_info["only_in_target"])
            
            if total_only_source > 0 or total_only_target > 0:
                print(f"  Methods only in source: {total_only_source}")
                print(f"  Methods only in target: {total_only_target}")
            print()


if __name__ == "__main__":
    main()
