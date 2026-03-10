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
        self.current_step_stats = {}  # 当前step的统计数据（用于实时更新）
        self.realtime_file = None  # 实时更新的Excel文件路径
        
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
            # 获取最后一轮的response长度（不再计算平均）
            final_length = stats.get('final_response_length', 0)
            
            record = {
                'timestamp': timestamp,
                'sample_index': idx,
                'retrieval_count': stats['retrieval_count'],  # 迭代次数
                'final_response_length': final_length,  # 最后一轮response长度
                'query': stats.get('query', ''),
                'ground_truth': str(stats.get('ground_truth', '')),
                'full_trajectory': stats.get('full_trajectory', ''),  # 完整多轮交互记录
            }
            
            # 添加批次信息
            if batch_info:
                record.update(batch_info)
            
            self.all_stats.append(record)
    
    def get_aggregated_stats(self) -> pd.DataFrame:
        """
        获取聚合统计数据（按迭代次数分组）
        
        Returns:
            包含聚合统计的DataFrame
        """
        if not self.all_stats:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.all_stats)
        
        # 按迭代次数分组统计
        if 'retrieval_count' in df.columns:
            grouped = df.groupby('retrieval_count').agg({
                'final_response_length': ['mean', 'std', 'min', 'max', 'count']
            }).reset_index()
            
            # 重命名列
            grouped.columns = [
                'retrieval_count',
                'final_response_length_mean', 'final_response_length_std', 
                'final_response_length_min', 'final_response_length_max', 'sample_count'
            ]
            
            return grouped
        
        return df
    
    def get_step_aggregated_stats(self) -> pd.DataFrame:
        """
        获取按步数聚合的统计数据
        
        Returns:
            包含按global_step聚合统计的DataFrame
        """
        if not self.all_stats:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.all_stats)
        
        # 按global_step分组统计
        if 'global_step' in df.columns:
            grouped = df.groupby('global_step').agg({
                'retrieval_count': ['mean', 'std', 'min', 'max'],
                'final_response_length': ['mean', 'std', 'min', 'max'],
                'sample_index': 'count'  # 样本数量
            }).reset_index()
            
            # 重命名列
            grouped.columns = [
                'global_step',
                'retrieval_count_mean', 'retrieval_count_std', 'retrieval_count_min', 'retrieval_count_max',
                'final_response_length_mean', 'final_response_length_std', 
                'final_response_length_min', 'final_response_length_max',
                'sample_count'
            ]
            
            return grouped
        
        return df
    
    def save_step_realtime(self, global_step: int, phase='training'):
        """
        实时保存当前step的统计数据到Excel
        每个step完成后调用此方法，追加一行统计结果
        
        Args:
            global_step: 当前训练步数
            phase: 训练阶段（training/validation）
        """
        # 筛选当前step的数据
        current_step_data = [s for s in self.all_stats 
                           if s.get('global_step') == global_step 
                           and s.get('phase') == phase]
        
        if not current_step_data:
            return
        
        # 计算当前step的聚合统计
        retrieval_counts = [s['retrieval_count'] for s in current_step_data]
        final_lengths = [s['final_response_length'] for s in current_step_data]
        
        # 挑选一个有完整交互记录的样本作为输出示例
        sample_output = ''
        for s in current_step_data:
            trajectory = s.get('full_trajectory', '')
            if trajectory:
                sample_output = f"【问题】{s.get('query', '')}\n\n{trajectory}"
                gt = s.get('ground_truth', '')
                if gt:
                    sample_output += f"【标准答案】{gt}\n"
                break
        
        # 计算统计量
        import numpy as np
        step_record = {
            'global_step': global_step,
            'phase': phase,
            'retrieval_count_mean': float(np.mean(retrieval_counts)) if retrieval_counts else 0,
            'retrieval_count_std': float(np.std(retrieval_counts)) if len(retrieval_counts) > 1 else 0,
            'retrieval_count_min': int(np.min(retrieval_counts)) if retrieval_counts else 0,
            'retrieval_count_max': int(np.max(retrieval_counts)) if retrieval_counts else 0,
            'final_response_length_mean': float(np.mean(final_lengths)) if final_lengths else 0,
            'final_response_length_std': float(np.std(final_lengths)) if len(final_lengths) > 1 else 0,
            'final_response_length_min': float(np.min(final_lengths)) if final_lengths else 0,
            'final_response_length_max': float(np.max(final_lengths)) if final_lengths else 0,
            'sample_count': len(current_step_data),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sample_output': sample_output,
        }
        
        # 初始化实时文件路径（每次运行创建新文件）
        if self.realtime_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.realtime_file = os.path.join(self.output_dir, f'realtime_step_stats_{timestamp}.xlsx')
        
        # 读取现有数据并追加（如果文件存在）
        if os.path.exists(self.realtime_file):
            try:
                existing_df = pd.read_excel(self.realtime_file, engine='openpyxl')
                # 检查是否已存在当前step的记录（避免重复）
                if not ((existing_df['global_step'] == global_step) & (existing_df['phase'] == phase)).any():
                    new_df = pd.DataFrame([step_record])
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    print(f"⚠ Step {global_step} ({phase}) 已存在，跳过")
                    return
            except Exception as e:
                print(f"⚠ 读取现有文件失败: {e}，创建新文件")
                combined_df = pd.DataFrame([step_record])
        else:
            combined_df = pd.DataFrame([step_record])
        
        # 保存到Excel
        try:
            combined_df.to_excel(self.realtime_file, index=False, engine='openpyxl')
            print(f"✓ Step {global_step} ({phase}) 统计已实时保存 | 最后一轮response平均长度: {step_record['final_response_length_mean']:.2f}")
        except Exception as e:
            print(f"✗ 实时保存失败: {e}")
    
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
            
            # 按迭代次数聚合统计
            df_agg = self.get_aggregated_stats()
            if not df_agg.empty:
                df_agg.to_excel(writer, sheet_name='按迭代次数聚合', index=False)
            
            # 按训练步数聚合统计（新增）
            df_step_agg = self.get_step_aggregated_stats()
            if not df_step_agg.empty:
                df_step_agg.to_excel(writer, sheet_name='按训练步数聚合', index=False)
            
            # 按迭代次数统计（如果有数据）
            if not df_raw.empty and 'retrieval_count' in df_raw.columns:
                turns_stats = df_raw.groupby('retrieval_count').size().reset_index(name='样本数量')
                turns_stats.to_excel(writer, sheet_name='迭代次数分布', index=False)
        
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
            print(f"\n平均迭代次数: {df['retrieval_count'].mean():.2f}")
            print(f"迭代次数范围: {df['retrieval_count'].min()} - {df['retrieval_count'].max()}")
            
            print("\n按迭代次数分布:")
            for count in sorted(df['retrieval_count'].unique()):
                num_samples = (df['retrieval_count'] == count).sum()
                percentage = num_samples / len(df) * 100
                print(f"  迭代 {count} 次: {num_samples} 个样本 ({percentage:.1f}%)")
        
        if 'final_response_length' in df.columns:
            valid_df = df[df['retrieval_count'] > 0]
            if not valid_df.empty:
                print(f"\n平均最后一轮response长度: {valid_df['final_response_length'].mean():.2f}")
                print(f"长度范围: {valid_df['final_response_length'].min():.2f} - {valid_df['final_response_length'].max():.2f}")
        
        # 新增：按训练步数统计
        if 'global_step' in df.columns and df['global_step'].nunique() > 1:
            print(f"\n训练步数统计:")
            print(f"  训练步数范围: {df['global_step'].min()} - {df['global_step'].max()}")
            print(f"  不同步数: {df['global_step'].nunique()} 个")
        
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
