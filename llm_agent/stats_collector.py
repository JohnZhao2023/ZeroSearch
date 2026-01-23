"""
统计收集器模块：用于收集和输出检索统计数据
"""
import os
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd


class RetrievalStatsCollector:
    """检索统计数据收集器"""
    
    def __init__(self, output_dir='./retrieval_stats'):
        """
        初始化统计收集器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.all_stats = []  # 存储所有批次的统计数据
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
    def add_batch_stats(self, retrieval_stats: List[Dict], batch_info: Dict = None):
        """
        添加一个批次的统计数据
        
        Args:
            retrieval_stats: 检索统计列表，每个元素对应一个样本
            batch_info: 批次信息（如批次号、步骤号等）
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for idx, stats in enumerate(retrieval_stats):
            # 计算平均长度
            if stats['retrieval_count'] > 0:
                avg_length = stats['total_retrieval_length'] / stats['retrieval_count']
            else:
                avg_length = 0
            
            record = {
                'timestamp': timestamp,
                'sample_index': idx,
                'retrieval_count': stats['retrieval_count'],
                'total_retrieval_length': stats['total_retrieval_length'],
                'avg_retrieval_length': avg_length,
            }
            
            # 添加批次信息
            if batch_info:
                record.update(batch_info)
            
            self.all_stats.append(record)
    
    def get_aggregated_stats(self) -> pd.DataFrame:
        """
        获取聚合统计数据
        
        Returns:
            包含聚合统计的DataFrame
        """
        if not self.all_stats:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.all_stats)
        
        # 按检索次数分组统计
        if 'retrieval_count' in df.columns:
            grouped = df.groupby('retrieval_count').agg({
                'total_retrieval_length': ['mean', 'std', 'min', 'max', 'count'],
                'avg_retrieval_length': ['mean', 'std', 'min', 'max']
            }).reset_index()
            
            # 重命名列
            grouped.columns = [
                'retrieval_count',
                'total_length_mean', 'total_length_std', 'total_length_min', 'total_length_max', 'sample_count',
                'avg_length_mean', 'avg_length_std', 'avg_length_min', 'avg_length_max'
            ]
            
            return grouped
        
        return df
    
    def save_to_excel(self, filename=None):
        """
        将统计数据保存到Excel文件
        
        Args:
            filename: 输出文件名，如果为None则自动生成
        """
        if not self.all_stats:
            print("警告：没有统计数据可保存")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'retrieval_stats_{timestamp}.xlsx'
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 创建Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 原始数据
            df_raw = pd.DataFrame(self.all_stats)
            df_raw.to_excel(writer, sheet_name='原始数据', index=False)
            
            # 聚合统计
            df_agg = self.get_aggregated_stats()
            if not df_agg.empty:
                df_agg.to_excel(writer, sheet_name='聚合统计', index=False)
            
            # 按检索次数统计（如果有数据）
            if not df_raw.empty and 'retrieval_count' in df_raw.columns:
                turns_stats = df_raw.groupby('retrieval_count').size().reset_index(name='样本数量')
                turns_stats.to_excel(writer, sheet_name='检索次数分布', index=False)
        
        print(f"统计数据已保存到: {output_path}")
        return output_path
    
    def save_to_json(self, filename=None):
        """
        将统计数据保存到JSON文件
        
        Args:
            filename: 输出文件名，如果为None则自动生成
        """
        if not self.all_stats:
            print("警告：没有统计数据可保存")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'retrieval_stats_{timestamp}.json'
        
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_stats, f, ensure_ascii=False, indent=2)
        
        print(f"统计数据已保存到: {output_path}")
        return output_path
    
    def print_summary(self):
        """打印统计摘要"""
        if not self.all_stats:
            print("没有统计数据")
            return
        
        df = pd.DataFrame(self.all_stats)
        
        print("\n" + "=" * 60)
        print("检索统计摘要")
        print("=" * 60)
        print(f"总样本数: {len(df)}")
        
        if 'retrieval_count' in df.columns:
            print(f"\n平均检索次数: {df['retrieval_count'].mean():.2f}")
            print(f"检索次数范围: {df['retrieval_count'].min()} - {df['retrieval_count'].max()}")
            
            print("\n按检索次数分布:")
            for count in sorted(df['retrieval_count'].unique()):
                num_samples = (df['retrieval_count'] == count).sum()
                percentage = num_samples / len(df) * 100
                print(f"  检索 {count} 次: {num_samples} 个样本 ({percentage:.1f}%)")
        
        if 'avg_retrieval_length' in df.columns:
            valid_df = df[df['retrieval_count'] > 0]
            if not valid_df.empty:
                print(f"\n平均每轮检索返回内容长度: {valid_df['avg_retrieval_length'].mean():.2f}")
                print(f"长度范围: {valid_df['avg_retrieval_length'].min():.2f} - {valid_df['avg_retrieval_length'].max():.2f}")
        
        print("=" * 60 + "\n")
    
    def clear(self):
        """清空统计数据"""
        self.all_stats = []


# 全局统计收集器实例
_global_collector = None


def get_global_collector(output_dir='./retrieval_stats'):
    """
    获取全局统计收集器实例
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        RetrievalStatsCollector实例
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = RetrievalStatsCollector(output_dir)
    return _global_collector


def reset_global_collector():
    """重置全局统计收集器"""
    global _global_collector
    _global_collector = None
