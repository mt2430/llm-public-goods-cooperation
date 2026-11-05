# Figure-to-data index

All paths below are relative to the repository root. Each script runs independently and is also called by `code/reproduce.py`.

| Figure | Plotting script | Primary figure source data |
|---|---|---|
| 1 | `code/plot_main_01_02.py` | `data/main_01_02/round_statistics_N6.csv` |
| 2 | `code/plot_main_01_02.py` | `data/main_01_02/condition_statistics_N6.csv` |
| 3 | `code/plot_main_03.py` | `data/main_03_communication/round_source_data.csv`, `effects_by_R.csv`, `social_dilemma_effects.csv` |
| 4 | `code/plot_main_04.py` | `data/main_04_actions/state_composition.csv`, `state_support.csv` |
| 5 | `code/plot_main_05.py` | `data/main_05_termination/random_round_source.csv`, `termination_trajectory_means.csv`, `termination_summary.csv` |
| 6 | `code/plot_main_06_07.py` | `data/main_06_07/Figure_6_summary.csv` |
| 7 | `code/plot_main_06_07.py` | `data/main_06_07/Figure_7_conditions.csv` |
| S1 | `code/plot_supplementary.py` | `data/supplementary/S1_communication_contrasts.csv` |
| S2 | `code/plot_supplementary.py` | `data/supplementary/S2_group_outcomes_R090.csv`, `S2_group_summary.csv` |
| S3 | `code/plot_supplementary.py` | `data/supplementary/S3_horizon_information.csv`, `S3_task_contrasts.csv` |

The group-level, round-level and individual-action tables retain the underlying observations used by `code/analyze.py`. Group identifiers link overlapping subsets consistently. Only distinct complete groups are independent repetitions.
