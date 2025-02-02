# # run_plot.py
import time
import yaml
import argparse
import os
from xalpha import Xalpha
import pandas as pd
from configs.syspath import (BASE_PATH, DATA_PATH, UNIVERSE_PATH, FACTOR_VALUES_PATH,
                                BACKTEST_PATH, IMAGE_PATH, INTERMEDIATE_PATH, STATS_PATH)
from utils.db_connector import fetch_latest_stats_from_db
factor_config_path = os.path.join(BASE_PATH, 'configs', 'factor.yaml')

def run_plot(params):
    print("getting params in run_plot")

    simulator = Xalpha(params)
    print("running plot")
    factor_name = params['name']
    author = params['author']
    # 从数据库中获取最新记录
    latest_stats = fetch_latest_stats_from_db(factor_name)
    if not latest_stats:
        print(f"未找到因子 '{factor_name}' 的记录")
        return

    # 调用 report_plot 方法
    simulator.report_plot(
        stats=latest_stats,
        author = author,
        plot=True,
        savefig=True,
        path=IMAGE_PATH,
        full_title=f"{params['name']}_{params['frequency']}"
    )



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run plotting for a specific factor.')
    parser.add_argument('--name', type=str, required=True, help='Name of the factor to plot.')
    parser.add_argument('--config', type=str, default=factor_config_path, help='Path to the config YAML file.')
    args = parser.parse_args()

    start_time = time.time()
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    factor_params = next((f for f in config['factors'] if f['name'] == args.name), None)
    if factor_params is None:
        raise ValueError(f"Factor {args.name} not found in the config file.")
    factor_values_path_new = os.path.join(FACTOR_VALUES_PATH, f"{args.name}.parquet")
    if not os.path.exists(factor_values_path_new):
        raise FileNotFoundError(f"Parquet file not found: {factor_values_path_new}")
    indicator_df = pd.read_parquet(factor_values_path_new)
    if indicator_df.empty or not indicator_df.index.is_unique:
        raise ValueError(f"Indicator DataFrame is empty or has non-unique index for factor {args.name}.")
    try:
        start_date = indicator_df.index[0][0] if isinstance(indicator_df.index, pd.MultiIndex) else indicator_df.index[0]
        end_date = indicator_df.index[-1][0] if isinstance(indicator_df.index, pd.MultiIndex) else indicator_df.index[-1]
    except (IndexError, TypeError) as e:
        raise ValueError(f"Error extracting dates from index: {e}")
    
    # 更新 factor_params
    factor_params['start_date'] = str(start_date)  
    factor_params['end_date'] = str(end_date)
    factor_params['run_mode'] = 'all'
    
    # print(f"Updated factor_params: {factor_params}")
    run_plot(factor_params)
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"run_plot.py Total script runtime: {total_time:.2f} seconds")

