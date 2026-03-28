"""
日志分析工具
用于分析任务执行日志，提取性能指标和错误信息
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class LogAnalyzer:
    """
    日志分析器
    分析任务执行日志，生成报告
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
    
    def analyze_task(self, task_id: str) -> Dict[str, Any]:
        """分析单个任务的日志"""
        task_dir = self.log_dir / task_id
        if not task_dir.exists():
            return {"error": f"Task directory not found: {task_id}"}
        
        result = {
            "task_id": task_id,
            "summary": {},
            "errors": [],
            "screenshots": [],
            "browser_actions": [],
            "performance": {},
            "results": []
        }
        
        jsonl_files = list(task_dir.glob("*.jsonl"))
        for jsonl_file in jsonl_files:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        self._process_entry(entry, result)
                    except json.JSONDecodeError:
                        continue
        
        screenshot_dir = task_dir / "screenshots" / "browser_actions"
        if screenshot_dir.exists():
            result["screenshots"] = [str(p) for p in screenshot_dir.glob("*.png")]
        
        metrics_dir = task_dir / "metrics"
        if metrics_dir.exists():
            summary_file = metrics_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    result["performance"] = json.load(f)
        
        return result
    
    def _process_entry(self, entry: Dict, result: Dict):
        """处理日志条目"""
        action = entry.get("action", "")
        
        if action == "error" or entry.get("level") == "ERROR":
            result["errors"].append(entry)
        elif action.startswith("browser_"):
            result["browser_actions"].append(entry)
        elif action in ["navigate", "click", "fill", "submit", "wait", "select", "hover", "evaluate"]:
            result["browser_actions"].append(entry)
        elif entry.get("status"):
            result["results"].append(entry)
    
    def generate_report(self, task_id: str) -> str:
        """生成任务分析报告"""
        analysis = self.analyze_task(task_id)
        
        if "error" in analysis:
            return f"Error: {analysis['error']}"
        
        report_lines = [
            f"=" * 60,
            f"Task Analysis Report: {task_id}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"=" * 60,
            "",
            "SUMMARY",
            "-" * 40,
        ]
        
        if analysis["results"]:
            result = analysis["results"][-1]
            report_lines.append(f"Final Status: {result.get('status', 'unknown')}")
            report_lines.append(f"Message: {result.get('message', '')}")
        
        report_lines.extend([
            "",
            "ERRORS",
            "-" * 40,
        ])
        
        if analysis["errors"]:
            for error in analysis["errors"]:
                report_lines.append(f"- [{error.get('timestamp', '')}] {error.get('error', error.get('message', ''))}")
                if error.get('screenshot'):
                    report_lines.append(f"  Screenshot: {error.get('screenshot')}")
        else:
            report_lines.append("No errors found.")
        
        report_lines.extend([
            "",
            "BROWSER ACTIONS",
            "-" * 40,
            f"Total actions: {len(analysis['browser_actions'])}",
            "",
        ])
        
        action_counts = defaultdict(int)
        for action in analysis["browser_actions"]:
            action_type = action.get("action", "unknown")
            action_counts[action_type] += 1
        
        for action_type, count in sorted(action_counts.items()):
            report_lines.append(f"  {action_type}: {count}")
        
        report_lines.extend([
            "",
            "SCREENSHOTS",
            "-" * 40,
            f"Total screenshots: {len(analysis['screenshots'])}",
        ])
        
        report_lines.extend([
            "",
            "PERFORMANCE",
            "-" * 40,
        ])
        
        perf = analysis.get("performance", {})
        if perf:
            report_lines.append(f"Total Duration: {perf.get('total_duration_ms', 0):.2f}ms")
            operations = perf.get("operations", {})
            for op, stats in operations.items():
                report_lines.append(f"  {op}:")
                report_lines.append(f"    Count: {stats.get('count', 0)}")
                report_lines.append(f"    Avg: {stats.get('avg_ms', 0):.2f}ms")
                report_lines.append(f"    Min: {stats.get('min_ms', 0):.2f}ms")
                report_lines.append(f"    Max: {stats.get('max_ms', 0):.2f}ms")
        else:
            report_lines.append("No performance data available.")
        
        report_lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
    
    def list_tasks(self) -> List[str]:
        """列出所有任务的日志目录"""
        if not self.log_dir.exists():
            return []
        return [d.name for d in self.log_dir.iterdir() if d.is_dir()]
    
    def compare_tasks(self, task_ids: List[str]) -> Dict[str, Any]:
        """比较多个任务的执行情况"""
        comparisons = {}
        
        for task_id in task_ids:
            analysis = self.analyze_task(task_id)
            if "error" not in analysis:
                comparisons[task_id] = {
                    "status": analysis["results"][-1].get("status") if analysis["results"] else "unknown",
                    "error_count": len(analysis["errors"]),
                    "action_count": len(analysis["browser_actions"]),
                    "performance": analysis.get("performance", {})
                }
        
        return comparisons
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取所有任务的错误摘要"""
        all_errors = []
        
        for task_dir in self.log_dir.iterdir():
            if not task_dir.is_dir():
                continue
            
            for jsonl_file in task_dir.glob("*.jsonl"):
                try:
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                if entry.get("action") == "error" or entry.get("level") == "ERROR":
                                    all_errors.append({
                                        "task_id": task_dir.name,
                                        "timestamp": entry.get("timestamp"),
                                        "error": entry.get("error") or entry.get("message", ""),
                                        "screenshot": entry.get("screenshot")
                                    })
                            except json.JSONDecodeError:
                                continue
                except Exception:
                    continue
        
        return {
            "total_errors": len(all_errors),
            "errors": all_errors,
            "error_count_by_task": self._count_by_task(all_errors)
        }
    
    def _count_by_task(self, errors: List[Dict]) -> Dict[str, int]:
        counts = defaultdict(int)
        for error in errors:
            counts[error.get("task_id", "unknown")] += 1
        return dict(counts)


class PerformanceAnalyzer:
    """
    性能分析器
    分析性能指标，识别瓶颈
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
    
    def analyze_bottlenecks(self, task_id: str) -> Dict[str, Any]:
        """分析任务性能瓶颈"""
        task_dir = self.log_dir / task_id / "metrics" / "summary.json"
        
        if not task_dir.exists():
            return {"error": "No performance data available"}
        
        with open(task_dir, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        operations = data.get("operations", {})
        
        bottlenecks = []
        for op, stats in operations.items():
            avg_ms = stats.get("avg_ms", 0)
            count = stats.get("count", 0)
            
            if avg_ms > 5000:
                bottlenecks.append({
                    "operation": op,
                    "avg_ms": avg_ms,
                    "count": count,
                    "severity": "high",
                    "suggestion": f"Operation '{op}' is very slow ({avg_ms:.0f}ms avg). Consider optimization or caching."
                })
            elif avg_ms > 2000:
                bottlenecks.append({
                    "operation": op,
                    "avg_ms": avg_ms,
                    "count": count,
                    "severity": "medium",
                    "suggestion": f"Operation '{op}' could be optimized ({avg_ms:.0f}ms avg)."
                })
        
        return {
            "task_id": task_id,
            "total_duration_ms": data.get("total_duration_ms", 0),
            "bottlenecks": bottlenecks,
            "slowest_operations": sorted(
                [(op, stats["avg_ms"]) for op, stats in operations.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def generate_optimization_report(self, task_id: str) -> str:
        """生成优化建议报告"""
        analysis = self.analyze_bottlenecks(task_id)
        
        if "error" in analysis:
            return f"Error: {analysis['error']}"
        
        report_lines = [
            f"=" * 60,
            f"Performance Optimization Report: {task_id}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"=" * 60,
            "",
            f"Total Duration: {analysis['total_duration_ms']:.2f}ms",
            "",
            "SLOWEST OPERATIONS",
            "-" * 40,
        ]
        
        for op, avg_ms in analysis["slowest_operations"]:
            report_lines.append(f"  {op}: {avg_ms:.2f}ms")
        
        report_lines.extend([
            "",
            "BOTTLENECKS & SUGGESTIONS",
            "-" * 40,
        ])
        
        if analysis["bottlenecks"]:
            for bottleneck in analysis["bottlenecks"]:
                report_lines.append(f"[{bottleneck['severity'].upper()}] {bottleneck['operation']}")
                report_lines.append(f"  Avg: {bottleneck['avg_ms']:.2f}ms, Count: {bottleneck['count']}")
                report_lines.append(f"  Suggestion: {bottleneck['suggestion']}")
                report_lines.append("")
        else:
            report_lines.append("No significant bottlenecks found.")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Log Analysis Tool")
    parser.add_argument("command", choices=["analyze", "report", "compare", "errors", "optimize"],
                        help="Command to execute")
    parser.add_argument("--task-id", "-t", help="Task ID")
    parser.add_argument("--task-ids", nargs="+", help="Multiple Task IDs")
    parser.add_argument("--log-dir", "-l", default="logs", help="Log directory")
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_dir)
    
    if args.command == "analyze":
        if not args.task_id:
            print("Error: --task-id is required")
            return
        result = analyzer.analyze_task(args.task_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "report":
        if not args.task_id:
            print("Error: --task-id is required")
            return
        print(analyzer.generate_report(args.task_id))
    
    elif args.command == "compare":
        if not args.task_ids:
            print("Error: --task-ids is required")
            return
        result = analyzer.compare_tasks(args.task_ids)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "errors":
        result = analyzer.get_error_summary()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "optimize":
        if not args.task_id:
            print("Error: --task-id is required")
            return
        perf_analyzer = PerformanceAnalyzer(args.log_dir)
        print(perf_analyzer.generate_optimization_report(args.task_id))


if __name__ == "__main__":
    main()
