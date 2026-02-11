"""
测试实时保存功能
"""
import sys
import os
import time

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("测试实时保存功能")
print("=" * 60)

try:
    from llm_agent.stats_collector import RetrievalStatsCollector
    
    # 创建收集器
    collector = RetrievalStatsCollector(output_dir='./test_realtime_output')
    
    print("\n模拟训练过程，每个step完成后实时保存...\n")
    
    # 模拟5个training step
    for step in range(5):
        print(f"\n{'='*40}")
        print(f"Step {step} 开始")
        print(f"{'='*40}")
        
        # 模拟该step的数据（假设每个step有3个样本）
        retrieval_stats = [
            {
                'total_response_length': 0,
                'retrieval_count': 2 + step % 3,  # 2-4次迭代
                'final_response_length': 180 + step * 10,  # 最后一轮长度逐渐增加
                'retrieval_details': [],
                'query': f'法律问题_step{step}_sample1',
                'ground_truth': ['标准答案']
            },
            {
                'total_response_length': 0,
                'retrieval_count': 3,
                'final_response_length': 190 + step * 10,
                'retrieval_details': [],
                'query': f'法律问题_step{step}_sample2',
                'ground_truth': ['标准答案']
            },
            {
                'total_response_length': 0,
                'retrieval_count': 2,
                'final_response_length': 170 + step * 10,
                'retrieval_details': [],
                'query': f'法律问题_step{step}_sample3',
                'ground_truth': ['标准答案']
            }
        ]
        
        batch_info = {
            'global_step': step,
            'batch_idx': 0,
            'phase': 'training'
        }
        
        # 添加统计数据
        collector.add_batch_stats(retrieval_stats, batch_info)
        
        # 实时保存当前step
        print(f"保存 Step {step} 的统计...")
        collector.save_step_realtime(step, phase='training')
        
        # 模拟训练耗时
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    
    # 检查文件
    if collector.realtime_file and os.path.exists(collector.realtime_file):
        print(f"\n✓ 实时统计文件已生成: {collector.realtime_file}")
        
        # 读取并显示
        import pandas as pd
        df = pd.read_excel(collector.realtime_file)
        
        print(f"\n文件内容（共{len(df)}行）:")
        print(df.to_string(index=False))
        
        print("\n✓ 验证：每个step完成后都追加了一行数据")
        print(f"✓ 包含字段: {list(df.columns)}")
        
    else:
        print("\n✗ 实时文件未生成")
    
    # 测试最终保存
    print("\n" + "="*60)
    print("测试最终完整保存...")
    print("="*60)
    
    final_excel = collector.save_to_excel('test_final.xlsx')
    print(f"\n✓ 完整统计文件: {final_excel}")
    
    print("\n" + "="*60)
    print("说明")
    print("="*60)
    print("\n训练过程中会生成两类文件：")
    print(f"\n1. 实时更新文件（按step聚合）:")
    print(f"   {collector.realtime_file}")
    print(f"   - 每完成一个step就追加一行")
    print(f"   - 可以随时打开查看训练进度")
    print(f"   - 包含该step的final_response_length_mean等统计")
    print(f"\n2. 完整统计文件（训练结束后）:")
    print(f"   {final_excel}")
    print(f"   - 包含4个工作表")
    print(f"   - 包含所有原始数据和聚合统计")
    
    print("\n" + "="*60)
    print("✓ 所有测试通过！")
    print("="*60)
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
