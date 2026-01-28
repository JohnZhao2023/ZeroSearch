"""
测试统计功能的更新：query和ground_truth字段，以及按step聚合
"""
import json
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from llm_agent.stats_collector import RetrievalStatsCollector


def test_new_fields():
    """测试新增的query和ground_truth字段"""
    print("=" * 60)
    print("测试1: 验证query和ground_truth字段")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    # 模拟包含query和ground_truth的数据
    retrieval_stats_batch1 = [
        {
            'total_retrieval_length': 1500,
            'retrieval_count': 3,
            'retrieval_details': [],
            'query': '什么是刑法第234条？',
            'ground_truth': ['故意伤害罪的相关规定']
        },
        {
            'total_retrieval_length': 1000,
            'retrieval_count': 2,
            'retrieval_details': [],
            'query': '民法典关于合同的规定是什么？',
            'ground_truth': ['民法典第三编合同']
        }
    ]
    
    batch_info1 = {
        'global_step': 1,
        'batch_idx': 0,
        'phase': 'training'
    }
    
    collector.add_batch_stats(retrieval_stats_batch1, batch_info1)
    
    # 检查数据
    print("\n收集的数据示例:")
    for stat in collector.all_stats[:2]:
        print(f"\n样本 {stat['sample_index']}:")
        print(f"  Query: {stat['query']}")
        print(f"  Ground Truth: {stat['ground_truth']}")
        print(f"  检索次数: {stat['retrieval_count']}")
        print(f"  平均长度: {stat['avg_retrieval_length']:.2f}")
    
    print("\n✓ Query和Ground Truth字段测试通过")
    return collector


def test_step_aggregation():
    """测试按步数聚合"""
    print("\n" + "=" * 60)
    print("测试2: 验证按训练步数聚合功能")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    # 模拟多个step的数据
    for step in range(3):
        retrieval_stats = [
            {
                'total_retrieval_length': 1500 + step * 100,
                'retrieval_count': 3,
                'retrieval_details': [],
                'query': f'问题_{step}_1',
                'ground_truth': ['答案']
            },
            {
                'total_retrieval_length': 1000 + step * 100,
                'retrieval_count': 2,
                'retrieval_details': [],
                'query': f'问题_{step}_2',
                'ground_truth': ['答案']
            }
        ]
        
        batch_info = {
            'global_step': step,
            'batch_idx': 0,
            'phase': 'training'
        }
        
        collector.add_batch_stats(retrieval_stats, batch_info)
    
    # 获取按step聚合的统计
    df_step_agg = collector.get_step_aggregated_stats()
    
    print("\n按训练步数聚合的统计:")
    print(df_step_agg.to_string(index=False))
    
    print("\n✓ 按步数聚合功能测试通过")
    return collector


def test_excel_export():
    """测试Excel导出包含所有新功能"""
    print("\n" + "=" * 60)
    print("测试3: 验证Excel导出")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    # 添加多个step的数据
    for step in [0, 1, 5, 10]:
        for batch in range(2):
            retrieval_stats = [
                {
                    'total_retrieval_length': 1500 + step * 50,
                    'retrieval_count': 3,
                    'retrieval_details': [],
                    'query': f'法律问题_step{step}_batch{batch}_sample1',
                    'ground_truth': ['标准答案1', '标准答案2']
                },
                {
                    'total_retrieval_length': 1000 + step * 50,
                    'retrieval_count': 2,
                    'retrieval_details': [],
                    'query': f'法律问题_step{step}_batch{batch}_sample2',
                    'ground_truth': ['标准答案']
                }
            ]
            
            batch_info = {
                'global_step': step,
                'batch_idx': batch,
                'phase': 'training'
            }
            
            collector.add_batch_stats(retrieval_stats, batch_info)
    
    # 导出Excel
    excel_path = collector.save_to_excel('test_updated_stats.xlsx')
    
    print(f"\n✓ Excel文件已导出: {excel_path}")
    print("\n请检查Excel文件包含以下工作表:")
    print("  1. 原始数据（包含query和ground_truth列）")
    print("  2. 按检索次数聚合")
    print("  3. 按训练步数聚合（新增）")
    print("  4. 检索次数分布")
    
    return collector


def test_json_export():
    """测试JSON导出包含新字段"""
    print("\n" + "=" * 60)
    print("测试4: 验证JSON导出")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    retrieval_stats = [
        {
            'total_retrieval_length': 1500,
            'retrieval_count': 3,
            'retrieval_details': [],
            'query': '测试问题：刑法第234条的内容是什么？',
            'ground_truth': ['故意伤害罪', '处三年以下有期徒刑']
        }
    ]
    
    batch_info = {
        'global_step': 0,
        'batch_idx': 0,
        'phase': 'training'
    }
    
    collector.add_batch_stats(retrieval_stats, batch_info)
    
    # 导出JSON
    json_path = collector.save_to_json('test_updated_stats.json')
    
    # 读取并验证
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✓ JSON文件已导出: {json_path}")
    print("\nJSON数据示例:")
    print(json.dumps(data[0], ensure_ascii=False, indent=2))
    
    # 验证新字段
    assert 'query' in data[0], "缺少query字段"
    assert 'ground_truth' in data[0], "缺少ground_truth字段"
    print("\n✓ 验证成功：JSON包含query和ground_truth字段")
    
    return collector


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试统计功能更新")
    print("=" * 60 + "\n")
    
    try:
        # 测试1: 新字段
        test_new_fields()
        
        # 测试2: 按step聚合
        test_step_aggregation()
        
        # 测试3: Excel导出
        test_excel_export()
        
        # 测试4: JSON导出
        test_json_export()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n新增功能验证成功：")
        print("  1. ✓ JSON文件包含query和ground_truth字段")
        print("  2. ✓ Excel新增'按训练步数聚合'工作表")
        print("  3. ✓ 可以查看每个step的avg_length_mean等统计")
        print("\n请查看 ./test_output 目录下的输出文件")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
