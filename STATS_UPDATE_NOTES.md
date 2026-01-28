# 统计功能更新说明

## 📋 更新日期
2026-01-27

## 🎯 更新内容

根据用户需求，对检索统计功能进行了两项重要更新：

### 1. JSON文件新增字段 ✅

**修改位置**: 
- `llm_agent/generation.py` - 在收集统计时添加query和ground_truth
- `llm_agent/stats_collector.py` - 在保存数据时包含这些字段

**新增字段**:
- `query`: 训练数据的问题/查询内容
- `ground_truth`: 标准答案（如果有）

**示例数据**:
```json
{
    "timestamp": "2026-01-27 12:00:00",
    "sample_index": 0,
    "retrieval_count": 3,
    "total_retrieval_length": 1500,
    "avg_retrieval_length": 500.0,
    "query": "什么是刑法第234条？",
    "ground_truth": "['故意伤害罪的相关规定']",
    "global_step": 1,
    "batch_idx": 0,
    "phase": "training"
}
```

**用途**: 
- 方便追溯每条统计数据对应的具体训练样本
- 便于分析不同问题类型的检索行为
- 支持问题级别的数据分析

---

### 2. Excel文件新增工作表 ✅

**修改位置**: 
- `llm_agent/stats_collector.py` - 添加 `get_step_aggregated_stats()` 方法
- `llm_agent/stats_collector.py` - 在 `save_to_excel()` 中添加新工作表

**新增工作表**: "按训练步数聚合"

**工作表字段**:

| 字段名 | 说明 |
|-------|------|
| global_step | 训练步数 |
| retrieval_count_mean | 该步的平均检索次数 |
| retrieval_count_std | 检索次数标准差 |
| retrieval_count_min | 最小检索次数 |
| retrieval_count_max | 最大检索次数 |
| total_length_mean | 总检索长度平均值 |
| total_length_std | 总检索长度标准差 |
| total_length_min | 总检索长度最小值 |
| total_length_max | 总检索长度最大值 |
| **avg_length_mean** ⭐ | **平均每轮检索长度的均值（核心指标）** |
| avg_length_std | 平均长度标准差 |
| avg_length_min | 平均长度最小值 |
| avg_length_max | 平均长度最大值 |
| sample_count | 该步的样本数量 |

**用途**:
- 观察训练过程中检索行为的变化趋势
- 分析每个训练步数的检索模式
- 快速定位异常步数
- 绘制训练曲线

---

## 📊 更新后的Excel文件结构

训练结束后生成的Excel文件包含**4个工作表**：

### 工作表1: 原始数据
- 所有样本的详细记录
- **新增**: query和ground_truth列
- 包含时间戳、步数、批次等信息

### 工作表2: 按检索次数聚合
- 按retrieval_count分组的统计
- 显示不同检索次数的平均检索长度
- 用于分析迭代次数与检索长度的关系

### 工作表3: 按训练步数聚合 🆕
- **新增工作表**
- 按global_step分组的统计
- 每行对应一个训练步数
- 显示该步的avg_length_mean等指标

### 工作表4: 检索次数分布
- 统计样本在不同检索次数的分布
- 快速了解数据概况

---

## 🔧 技术实现细节

### 1. 数据收集流程

```python
# generation.py - 初始化时收集query和ground_truth
retrieval_stats = [{
    'total_retrieval_length': 0,
    'retrieval_count': 0,
    'retrieval_details': [],
    'query': gen_batch.non_tensor_batch['question'][idx],  # 新增
    'ground_truth': gen_batch.non_tensor_batch['golden_answers'][idx]  # 新增
} for idx in range(batch_size)]
```

### 2. 数据保存流程

```python
# stats_collector.py - 保存时包含新字段
record = {
    'timestamp': timestamp,
    'sample_index': idx,
    'retrieval_count': stats['retrieval_count'],
    'total_retrieval_length': stats['total_retrieval_length'],
    'avg_retrieval_length': avg_length,
    'query': stats.get('query', ''),  # 新增
    'ground_truth': str(stats.get('ground_truth', '')),  # 新增
    'global_step': batch_info.get('global_step'),
    'batch_idx': batch_info.get('batch_idx'),
    'phase': batch_info.get('phase')
}
```

### 3. 按步数聚合实现

```python
# stats_collector.py - 新增方法
def get_step_aggregated_stats(self) -> pd.DataFrame:
    df = pd.DataFrame(self.all_stats)
    grouped = df.groupby('global_step').agg({
        'retrieval_count': ['mean', 'std', 'min', 'max'],
        'total_retrieval_length': ['mean', 'std', 'min', 'max'],
        'avg_retrieval_length': ['mean', 'std', 'min', 'max'],
        'sample_index': 'count'
    }).reset_index()
    return grouped
```

---

## 📈 使用示例

### 示例1: 查看JSON中的query

```python
import json

with open('retrieval_stats_20260127.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查看前3个样本的query
for item in data[:3]:
    print(f"Query: {item['query']}")
    print(f"Ground Truth: {item['ground_truth']}")
    print(f"检索次数: {item['retrieval_count']}")
    print(f"平均长度: {item['avg_retrieval_length']:.2f}")
    print("-" * 40)
```

### 示例2: 分析训练过程的检索长度变化

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取按步数聚合的数据
df = pd.read_excel('retrieval_stats_20260127.xlsx', 
                   sheet_name='按训练步数聚合')

# 绘制训练曲线
plt.figure(figsize=(12, 6))
plt.plot(df['global_step'], df['avg_length_mean'], marker='o')
plt.fill_between(df['global_step'], 
                 df['avg_length_mean'] - df['avg_length_std'],
                 df['avg_length_mean'] + df['avg_length_std'],
                 alpha=0.3)
plt.xlabel('训练步数')
plt.ylabel('平均每轮检索返回内容长度')
plt.title('训练过程中检索长度的变化')
plt.grid(True)
plt.savefig('training_progress.png')
plt.show()
```

### 示例3: 筛选特定query的数据

```python
import pandas as pd

# 读取原始数据
df = pd.read_excel('retrieval_stats_20260127.xlsx', 
                   sheet_name='原始数据')

# 筛选包含特定关键词的query
keyword = '刑法'
filtered = df[df['query'].str.contains(keyword, na=False)]

print(f"包含'{keyword}'的样本数: {len(filtered)}")
print(f"平均检索次数: {filtered['retrieval_count'].mean():.2f}")
print(f"平均检索长度: {filtered['avg_retrieval_length'].mean():.2f}")
```

---

## ✅ 验证测试

运行验证脚本确认更新：

```bash
python d:\Cursor_workspace\ZeroSearch\verify_updates.py
```

**测试结果**: ✓ 所有验证通过

---

## 🚀 如何使用

### 无需额外配置

所有更新已集成到代码中，**直接运行训练即可**：

```bash
bash train_reinforce.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct ...
bash train_grpo.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct ...
bash train_ppo.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct ...
```

### 输出位置

训练结束后，文件保存在：

```
<训练输出目录>/retrieval_stats/
├── retrieval_stats_YYYYMMDD_HHMMSS.xlsx  (包含4个工作表)
└── retrieval_stats_YYYYMMDD_HHMMSS.json  (包含query和ground_truth字段)
```

---

## 📝 注意事项

### 1. ground_truth字段格式

- 如果标准答案是列表，会被转换为字符串格式
- 例如: `['答案1', '答案2']` → `"['答案1', '答案2']"`
- 读取时需要使用 `eval()` 或 `ast.literal_eval()` 转换回列表

### 2. query字段编码

- JSON文件使用UTF-8编码，支持中文
- Excel中的中文正常显示

### 3. 空值处理

- 如果某些数据没有ground_truth，字段值为空字符串 `''`
- 如果某些数据没有query，字段值为空字符串 `''`

---

## 🔍 常见问题

### Q1: 如何找到特定query对应的统计数据？

**A**: 在Excel的"原始数据"工作表中，使用Excel的筛选功能或Ctrl+F查找。

### Q2: 按步数聚合的avg_length_mean是什么意思？

**A**: 表示某个训练步数中，所有样本的"平均每轮检索长度"的平均值。
- 例如：Step 5有10个样本
- 每个样本有自己的avg_retrieval_length
- avg_length_mean就是这10个值的平均

### Q3: 如何对比不同实验的训练曲线？

**A**: 
1. 运行多次实验，每次生成独立的Excel文件
2. 读取各文件的"按训练步数聚合"工作表
3. 绘制在同一张图上对比

---

## 📚 相关文档

- `使用指南_检索统计功能.md` - 详细使用指南
- `RETRIEVAL_STATS_README.md` - 技术文档
- `MODIFICATIONS_SUMMARY.md` - 完整修改总结

---

## 🎉 总结

本次更新完成了两个重要功能：

1. ✅ **JSON文件增强**: 每条记录包含query和ground_truth，便于追溯数据
2. ✅ **Excel新增工作表**: "按训练步数聚合"，便于分析训练过程

**立即可用**: 无需重新安装，直接运行训练即可体验新功能！

---

更新完成时间: 2026-01-27  
验证状态: ✅ 通过
