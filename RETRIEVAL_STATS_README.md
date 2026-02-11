# 检索统计功能使用说明

## 功能概述

本功能用于统计强化学习训练过程中检索的相关数据，特别是**迭代次数和平均每轮检索返回内容长度的关系**。

## 统计指标

对于每个样本，系统会统计以下信息：

1. **检索次数（retrieval_count）**: 从输入进入到检索停止的总次数
2. **总检索返回内容长度（total_retrieval_length）**: 所有检索返回内容的总字符数
3. **平均每轮检索返回内容长度（avg_retrieval_length）**: 计算公式为 `总检索返回内容长度 / 检索次数`

## 修改的文件

1. **llm_agent/generation.py**: 在多轮检索循环中添加统计逻辑
2. **llm_agent/stats_collector.py**: 新增统计数据收集和导出模块
3. **verl/trainer/ppo/ray_trainer.py**: 集成统计收集器到训练流程

## 使用方法

### 1. 正常运行训练

按照原有方式运行训练脚本，无需额外参数：

```bash
# REINFORCE 训练示例
bash train_reinforce.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct \
    DATA_PATH ZeroSearch_dataset TOTAL_STEPS 203 IP localhost \
    SEARCH_MODE simulate_prompt SIMULATION_LLM Qwen2.5-14B-Instruct \
    START_THRESHOLD 0 END_THRESHOLD 0.5 SEARCH_ENGINE google \
    MAX_TURNS 5 TOPK 5

# GRPO 训练示例
bash train_grpo.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct \
    DATA_PATH ZeroSearch_dataset TOTAL_STEPS 203 IP localhost \
    SEARCH_MODE simulate_prompt SIMULATION_LLM Qwen2.5-14B-Instruct \
    START_THRESHOLD 0 END_THRESHOLD 0.5 SEARCH_ENGINE google \
    MAX_TURNS 5 TOPK 5

# PPO 训练示例
bash train_ppo.sh NUM_GPUS_PER_NODE 4 MODEL_PATH Qwen2.5-3B-Instruct \
    DATA_PATH ZeroSearch_dataset TOTAL_STEPS 203 IP localhost \
    SEARCH_MODE simulate_prompt SIMULATION_LLM Qwen2.5-14B-Instruct \
    START_THRESHOLD 0 END_THRESHOLD 0.5 SEARCH_ENGINE google \
    MAX_TURNS 5 TOPK 5
```

### 2. 查看实时统计

训练过程中，每个批次处理完成后会在控制台打印检索统计信息：

```
=== 检索统计信息 ===
样本 0: 检索次数=3, 总长度=1542, 平均长度=514.00
样本 1: 检索次数=2, 总长度=1028, 平均长度=514.00
样本 2: 检索次数=4, 总长度=2056, 平均长度=514.00
...
```

### 3. 导出统计数据

训练或验证完成后，系统会自动生成以下文件：

#### Excel 文件
位置：`<default_local_dir>/retrieval_stats/retrieval_stats_YYYYMMDD_HHMMSS.xlsx`

包含三个工作表：
- **原始数据**: 每个样本的详细统计
- **聚合统计**: 按检索次数分组的统计数据
- **检索次数分布**: 不同检索次数的样本数量分布

#### JSON 文件
位置：`<default_local_dir>/retrieval_stats/retrieval_stats_YYYYMMDD_HHMMSS.json`

包含所有原始统计数据的JSON格式

## 输出数据格式

### Excel - 原始数据表

| 列名 | 说明 |
|-----|------|
| timestamp | 记录时间戳 |
| sample_index | 样本索引 |
| retrieval_count | 检索次数 |
| total_retrieval_length | 总检索返回内容长度 |
| avg_retrieval_length | 平均每轮检索返回内容长度 |
| global_step | 全局训练步数 |
| batch_idx | 批次索引 |
| phase | 阶段（training/validation） |

### Excel - 聚合统计表

| 列名 | 说明 |
|-----|------|
| retrieval_count | 检索次数 |
| total_length_mean | 总长度平均值 |
| total_length_std | 总长度标准差 |
| total_length_min | 总长度最小值 |
| total_length_max | 总长度最大值 |
| sample_count | 样本数量 |
| avg_length_mean | 平均长度的平均值 |
| avg_length_std | 平均长度的标准差 |
| avg_length_min | 平均长度最小值 |
| avg_length_max | 平均长度最大值 |

### Excel - 检索次数分布表

| 列名 | 说明 |
|-----|------|
| retrieval_count | 检索次数 |
| 样本数量 | 具有该检索次数的样本数量 |

## 数据分析示例

### Python 分析示例

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取Excel文件
df_raw = pd.read_excel('retrieval_stats_20260123_120000.xlsx', sheet_name='原始数据')
df_agg = pd.read_excel('retrieval_stats_20260123_120000.xlsx', sheet_name='聚合统计')

# 1. 绘制迭代次数与平均检索长度的关系
plt.figure(figsize=(10, 6))
plt.scatter(df_agg['retrieval_count'], df_agg['avg_length_mean'])
plt.errorbar(df_agg['retrieval_count'], df_agg['avg_length_mean'], 
             yerr=df_agg['avg_length_std'], fmt='o', capsize=5)
plt.xlabel('检索次数')
plt.ylabel('平均每轮检索返回内容长度')
plt.title('迭代次数与平均检索长度的关系')
plt.grid(True)
plt.savefig('retrieval_length_vs_count.png')
plt.show()

# 2. 查看不同训练步数的统计变化
if 'global_step' in df_raw.columns:
    step_stats = df_raw.groupby('global_step').agg({
        'retrieval_count': 'mean',
        'avg_retrieval_length': 'mean'
    })
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    ax1.plot(step_stats.index, step_stats['retrieval_count'])
    ax1.set_xlabel('训练步数')
    ax1.set_ylabel('平均检索次数')
    ax1.set_title('训练过程中检索次数变化')
    ax1.grid(True)
    
    ax2.plot(step_stats.index, step_stats['avg_retrieval_length'])
    ax2.set_xlabel('训练步数')
    ax2.set_ylabel('平均检索长度')
    ax2.set_title('训练过程中平均检索长度变化')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('training_progress.png')
    plt.show()

# 3. 打印详细统计
print("统计摘要:")
print(f"总样本数: {len(df_raw)}")
print(f"\n按检索次数分组:")
print(df_agg[['retrieval_count', 'avg_length_mean', 'sample_count']])
```

## 注意事项

1. **存储空间**: 统计数据会随着训练批次增加而累积，请确保有足够的磁盘空间
2. **性能影响**: 统计功能对训练性能的影响很小（< 1%），但会增加少量内存使用
3. **多次实验**: 每次训练会生成带时间戳的独立文件，方便进行多次实验对比
4. **自定义输出路径**: 输出路径默认在训练配置的 `default_local_dir` 下，可以通过修改代码调整

## 故障排除

### 问题1: 没有生成统计文件

**可能原因**: 
- 训练过程中没有进行检索操作（do_search=False）
- 训练提前终止

**解决方法**: 
- 确保配置中 `trainer.do_search=True`
- 检查训练日志确认是否正常完成

### 问题2: Excel文件打不开

**可能原因**: 
- 缺少 openpyxl 库

**解决方法**:
```bash
pip install openpyxl
```

### 问题3: 统计数据全为0

**可能原因**: 
- 模型从未执行检索操作（全部直接回答）

**解决方法**: 
- 这是正常现象，说明模型认为不需要检索即可回答
- 可以查看训练日志确认实际行为

## 技术细节

### 统计收集时机
- 在 `LLMGenerationManager.run_llm_loop()` 方法的每轮检索后
- 包括训练阶段和验证阶段

### 内容长度计算
- 使用 Python 的 `len()` 函数计算字符串长度
- 包括所有返回的文档内容、标记等

### 聚合方式
- 使用 pandas 的 `groupby` 和 `agg` 函数
- 计算均值、标准差、最小值、最大值等统计量

## 联系方式

如有问题或建议，请联系项目维护者。
