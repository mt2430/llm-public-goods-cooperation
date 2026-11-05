# 数据字典与统计口径

## 数据层级

一条完整轨迹是一组模型智能体从首轮到结束的实验记录，是独立重复和bootstrap的单位。逐轮记录描述群体在一轮中的平均行为。个体行动记录描述一个参与者在一轮中的投入。条件统计和图源数据在这些记录上计算。

缺失的数值保留为空单元格或NaN。随机终止后没有观察到的轮次不记为零。各图复用同一批群体时，trajectory_id保持一致。

## 实验参数

| 字段 | 含义 |
|---|---|
| configuration_id | 公开版模型配置标识，推理设置见data/model_configurations.csv |
| model / model_family | 模型简称或模型家族。kimi3对应Kimi，glm52对应GLM |
| trajectory_id / slot_id | 独立群体轨迹标识；随机终止逐轮表使用slot_id |
| atlas_cell_id | 统一条件标识 |
| R | 归一化回报，R=r/N，也是每单位贡献给每名参与者带来的回报 |
| N | 群体人数，4、6、8或12 |
| E | 每轮重新分配的禀赋，核心实验为20 |
| T | 固定轮数条件的总轮数，核心实验为10 |
| communication | none、once_public、each_public，依次为无沟通、首轮公开沟通、每轮公开沟通 |
| feedback | none、aggregate、individual，反馈信息类型 |
| memory | 可用历史窗口，0、1、3或all，具体条件保留原记录 |
| membership | fixed或random_each_round，固定成员或逐轮重组 |
| contribution_step_ratio | 可选投入金额步长除以E |
| continuation_probability | 继续概率，随机终止实验为0.90 |
| realized_rounds / rounds / completed_rounds | 完整群体实际经历的轮数 |
| registered_rounds | 预先抽取的随机持续轮数 |
| replicate | 条件内的独立重复编号 |
| round | 从1开始的轮次 |
| participant | 参与者标识，和trajectory_id、round共同定位行动 |

R<1时，贡献一单位会使贡献者当轮收益减少1-R。群体总收益则增加NR-1。每人每轮收益为E-c_i+R乘以全组投入之和。累计收益是各轮收益之和，不改变下一轮可投入的E。

## 贡献、行动和差值

| 字段 | 含义及单位 |
|---|---|
| contribution_rate | 贡献率c/E，个体表为个体贡献率，逐轮群体表为本轮参与者平均贡献率，范围0–1 |
| mean / atlas_mean | 完整轨迹的全过程平均贡献率，或同条件轨迹均值，依表层级确定 |
| early / atlas_early | 前min(3,T)轮平均贡献率 |
| late / atlas_late | 后min(3,T)轮平均贡献率 |
| final / atlas_final | 最后一轮贡献率 |
| zero / atlas_zero | 完全不贡献的行动比例 |
| full / atlas_full | 全额贡献的行动比例 |
| state | 0为零贡献，1为部分贡献，2为全额贡献 |
| share | 给定模型、沟通安排和轮次的行动状态比例，三个R先分别计算再等权汇总 |
| estimate_pp / lo_pp / hi_pp | 贡献率差及其95%区间，以百分点为单位 |
| arm_a / arm_b | 差值的被减项和减项，差值为arm_a减arm_b |
| first_minus_none | 首轮沟通减无沟通 |
| every_minus_none | 每轮沟通减无沟通 |
| every_minus_first | 每轮沟通减首轮沟通 |
| mean_percent等以_percent结尾的字段 | 已乘100的贡献率或分布统计 |
| metric | whole_run/mean、late_stage/late、final_round/final等统计窗口 |

同名字段的单位取决于表。以下规则用于避免重复乘100。

| 文件 | 贡献率与区间的单位 |
|---|---|
| main_01_02条件与轮次统计 | 0–1的比例，画图时乘100 |
| group_records、main_03_communication轨迹与轮次 | 0–1的比例 |
| main_03_communication中的effects及plotted_direct_effect_map | estimate_pp、lo_pp、hi_pp已是百分点 |
| main_04_actions | contribution_rate与share为0–1比例 |
| main_05_termination | mean、late、lo、hi为比例，termination_contrasts的mean、lo、hi为比例差，画图时乘100 |
| main_06_07/Figure_6_trajectories.csv | mean、late、final为0–1比例 |
| main_06_07/Figure_6_summary.csv、Figure_6_condition_summary.csv | estimate、lo、hi已是0–100百分比 |
| main_06_07/Figure_6_contrasts.csv | estimate_pp、lo_pp、hi_pp已是百分点 |
| main_06_07/Figure_7_conditions.csv | mean、mean_lo、mean_hi为0–1比例 |
| supplementary/S1_communication_contrasts.csv | 已是百分点 |
| supplementary/S2_group_outcomes_R090.csv | atlas_*贡献率为0–1比例 |
| supplementary/S2_group_summary.csv | 各_percent字段为0–100百分比 |
| supplementary/S3_horizon_information.csv | mean、lo、hi为0–1比例 |
| supplementary/S3_task_contrasts.csv | mean、lo、hi为比例差，画图时乘100得到百分点 |

## delta等历史字段的含义

原轨迹表中的delta是继续概率。分析表condition_statistics_N6和condition_source_data中的delta是末期减前期的贡献率变化，继续概率另存为continuation_probability。atlas_delta是末期减前期。分析表terminal是终轮减前一轮的贡献率变化，原轨迹表terminal或terminal_rule是终止规则。不能仅凭列名把这些字段跨表合并。

dispersion为群体内部个体贡献率的总体标准差，再按轮次及轨迹平均。sd为同条件完整轨迹全过程贡献率的样本标准差。volatility是相邻轮群体平均贡献率变化的绝对值均值。payoff或atlas_payoff是每人每轮收益除以E，mean_payoff保留原收益金额。group_count是原聚合记录携带的计数字段，不是群体人数N。

## 区间和汇总

误差带和误差棒为点估计的95%百分位bootstrap区间。原分析在各条件内独立重采样完整群体10,000次。所有参与者及轮次随群体一起保留。跨R汇总先计算每个条件，再对R等权平均。独立沟通安排分别重采样，同一基准用于多个对比时复用该基准抽样。

n为条件内完整群体数。n_alive为相应轮次有观测的群体数。n_a和n_b记录对比两侧样本数。_lo和_hi是相应统计量区间端点。p10和p90为原逐轮分布的分位数，不是95%均值区间。bootstrap_replicates记录重采样次数。


## 公开版标识与图形字段

trajectory_id与slot_id使用一致的群体编号，atlas_cell_id使用条件编号。编号跨表保持一致，并保留原排序。configuration_id连接模型配置表。panel、figure_model_index和heatmap_row等字段用于对应图内位置。R_values与weighting记录汇总所用的条件及权重。各表字段与行数见table_inventory.json。
