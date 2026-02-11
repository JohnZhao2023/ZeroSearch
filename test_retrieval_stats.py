"""
测试检索统计功能的脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from llm_agent.stats_collector import RetrievalStatsCollector


def test_basic_stats():
    """测试基本的统计功能"""
    print("=" * 60)
    print("测试1: 基本统计功能")
    print("=" * 60)
    
    # 创建统计收集器
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    # 模拟第一个批次的数据
    retrieval_stats_batch1 = [
        {
            'total_retrieval_length': 1500,
            'retrieval_count': 3,
            'retrieval_details': [
                {'turn': 1, 'length': 500, 'content_preview': 'Doc 1: ...'},
                {'turn': 2, 'length': 500, 'content_preview': 'Doc 2: ...'},
                {'turn': 3, 'length': 500, 'content_preview': 'Doc 3: ...'},
            ]
        },
        {
            'total_retrieval_length': 1000,
            'retrieval_count': 2,
            'retrieval_details': [
                {'turn': 1, 'length': 500, 'content_preview': 'Doc 1: ...'},
                {'turn': 2, 'length': 500, 'content_preview': 'Doc 2: ...'},
            ]
        },
        {
            'total_retrieval_length': 2000,
            'retrieval_count': 4,
            'retrieval_details': [
                {'turn': 1, 'length': 500, 'content_preview': 'Doc 1: ...'},
                {'turn': 2, 'length': 500, 'content_preview': 'Doc 2: ...'},
                {'turn': 3, 'length': 500, 'content_preview': 'Doc 3: ...'},
                {'turn': 4, 'length': 500, 'content_preview': 'Doc 4: ...'},
            ]
        }
    ]
    
    batch_info1 = {
        'global_step': 1,
        'batch_idx': 0,
        'phase': 'training'
    }
    
    collector.add_batch_stats(retrieval_stats_batch1, batch_info1)
    
    # 模拟第二个批次的数据
    retrieval_stats_batch2 = [
        {
            'total_retrieval_length': 1500,
            'retrieval_count': 3,
            'retrieval_details': []
        },
        {
            'total_retrieval_length': 1500,
            'retrieval_count': 3,
            'retrieval_details': []
        },
        {
            'total_retrieval_length': 500,
            'retrieval_count': 1,
            'retrieval_details': []
        }
    ]
    
    batch_info2 = {
        'global_step': 2,
        'batch_idx': 1,
        'phase': 'training'
    }
    
    collector.add_batch_stats(retrieval_stats_batch2, batch_info2)
    
    # 打印统计摘要
    collector.print_summary()
    
    # 导出数据
    excel_path = collector.save_to_excel('test_stats.xlsx')
    json_path = collector.save_to_json('test_stats.json')
    
    print(f"\n✓ Excel文件已保存: {excel_path}")
    print(f"✓ JSON文件已保存: {json_path}")
    print("\n测试1完成！\n")
    
    return collector


def test_aggregated_stats(collector):
    """测试聚合统计功能"""
    print("=" * 60)
    print("测试2: 聚合统计功能")
    print("=" * 60)
    
    df_agg = collector.get_aggregated_stats()
    
    print("\n聚合统计数据:")
    print(df_agg.to_string(index=False))
    print("\n测试2完成！\n")


def test_edge_cases():
    """测试边界情况"""
    print("=" * 60)
    print("测试3: 边界情况")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    # 情况1: 没有检索的样本
    stats_no_retrieval = [
        {
            'total_retrieval_length': 0,
            'retrieval_count': 0,
            'retrieval_details': []
        }
    ]
    
    collector.add_batch_stats(stats_no_retrieval, {'test': 'no_retrieval'})
    print("✓ 已添加无检索样本")
    
    # 情况2: 单次检索
    stats_single_retrieval = [
        {
            'total_retrieval_length': 800,
            'retrieval_count': 1,
            'retrieval_details': [
                {'turn': 1, 'length': 800, 'content_preview': 'Single retrieval'}
            ]
        }
    ]
    
    collector.add_batch_stats(stats_single_retrieval, {'test': 'single_retrieval'})
    print("✓ 已添加单次检索样本")
    
    # 情况3: 大量检索
    stats_many_retrievals = [
        {
            'total_retrieval_length': 5000,
            'retrieval_count': 10,
            'retrieval_details': []
        }
    ]
    
    collector.add_batch_stats(stats_many_retrievals, {'test': 'many_retrievals'})
    print("✓ 已添加大量检索样本")
    
    collector.print_summary()
    print("\n测试3完成！\n")


def test_export_empty():
    """测试空数据导出"""
    print("=" * 60)
    print("测试4: 空数据导出")
    print("=" * 60)
    
    collector = RetrievalStatsCollector(output_dir='./test_output')
    
    print("尝试导出空数据...")
    collector.save_to_excel('empty_test.xlsx')
    collector.save_to_json('empty_test.json')
    
    print("\n测试4完成！\n")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行检索统计功能测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试1: 基本功能
        collector = test_basic_stats()
        
        # 测试2: 聚合统计
        test_aggregated_stats(collector)
        
        # 测试3: 边界情况
        test_edge_cases()
        
        # 测试4: 空数据
        test_export_empty()
        
        print("=" * 60)
        print("所有测试完成！✓")
        print("=" * 60)
        print("\n请查看 ./test_output 目录下的输出文件")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
