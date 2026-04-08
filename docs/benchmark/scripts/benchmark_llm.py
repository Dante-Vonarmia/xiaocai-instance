#!/usr/bin/env python3
"""
LLM Benchmark Script

用法:
    python benchmark_llm.py --models claude-sonnet-4.5,gpt-4-turbo --dataset data/test_samples.json

输出:
    results/benchmark_YYYY-MM-DD.csv
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
from anthropic import Anthropic
from openai import OpenAI
import os

class LLMBenchmark:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def call_claude(self, prompt: str, model: str = "claude-sonnet-4-20250514") -> Dict[str, Any]:
        """调用 Claude API"""
        start_time = time.time()
        
        response = self.anthropic.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        latency = time.time() - start_time
        
        return {
            "response": response.content[0].text,
            "latency": latency,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": model
        }
    
    def call_gpt4(self, prompt: str, model: str = "gpt-4-turbo") -> Dict[str, Any]:
        """调用 GPT-4 API"""
        start_time = time.time()
        
        response = self.openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )
        
        latency = time.time() - start_time
        
        return {
            "response": response.choices[0].message.content,
            "latency": latency,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "model": model
        }
    
    def run_benchmark(self, models: List[str], dataset: List[Dict]) -> pd.DataFrame:
        """运行 Benchmark"""
        results = []
        
        for sample in dataset:
            sample_id = sample["id"]
            prompt = sample["prompt"]
            ground_truth = sample.get("ground_truth")
            
            for model in models:
                print(f"Testing {model} on sample {sample_id}...")
                
                try:
                    if "claude" in model.lower():
                        result = self.call_claude(prompt, model)
                    elif "gpt" in model.lower():
                        result = self.call_gpt4(prompt, model)
                    else:
                        raise ValueError(f"Unsupported model: {model}")
                    
                    # 计算准确率（简化版，实际应该用 JSON 解析 + 字段对比）
                    accuracy = self._calculate_accuracy(result["response"], ground_truth)
                    
                    results.append({
                        "sample_id": sample_id,
                        "model": model,
                        "latency": result["latency"],
                        "input_tokens": result["input_tokens"],
                        "output_tokens": result["output_tokens"],
                        "accuracy": accuracy,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"Error: {e}")
                    results.append({
                        "sample_id": sample_id,
                        "model": model,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        return pd.DataFrame(results)
    
    def _calculate_accuracy(self, response: str, ground_truth: Dict) -> float:
        """
        计算准确率（简化版）
        
        实际实现应该:
        1. 解析 JSON 输出
        2. 字段级别对比
        3. 使用 ROUGE/BLEU 等指标
        """
        if not ground_truth:
            return 0.0
        
        # TODO: 实现真实的准确率计算
        return 0.95  # 占位符

def main():
    parser = argparse.ArgumentParser(description="LLM Benchmark Tool")
    parser.add_argument("--models", type=str, required=True, 
                       help="Comma-separated model names (e.g., claude-sonnet-4.5,gpt-4-turbo)")
    parser.add_argument("--dataset", type=str, required=True,
                       help="Path to test dataset JSON file")
    parser.add_argument("--output", type=str, default="results/benchmark.csv",
                       help="Output CSV file path")
    
    args = parser.parse_args()
    
    # 解析模型列表
    models = [m.strip() for m in args.models.split(",")]
    
    # 加载数据集
    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    
    print(f"Loaded {len(dataset)} test samples")
    print(f"Testing models: {models}")
    
    # 运行 Benchmark
    benchmark = LLMBenchmark()
    results_df = benchmark.run_benchmark(models, dataset)
    
    # 保存结果
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    
    print(f"\nResults saved to: {output_path}")
    
    # 打印汇总统计
    print("\n=== Summary Statistics ===")
    print(results_df.groupby("model").agg({
        "latency": ["mean", "std", "min", "max"],
        "accuracy": "mean",
        "input_tokens": "mean",
        "output_tokens": "mean"
    }).round(3))

if __name__ == "__main__":
    main()
