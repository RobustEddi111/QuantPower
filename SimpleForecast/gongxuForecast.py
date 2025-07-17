# ARIMA移动平均预测时间序列

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt

# 示例发电量数据
gen_str = '245.14	246.77	243.45	237.24	230.66	261.86	234.01	260.81	228.85'
generation_data = [float(i) for i in gen_str.split('\t')]
print(generation_data)


# 转换数据为 DataFrame 并设置索引为人工时间索引
data = pd.DataFrame(generation_data, columns=["generation"])
data.index = pd.RangeIndex(start=1, stop=len(data) + 1, step=1)  # 创建人工索引作为时间轴

# 创建并拟合 ARIMA 模型，(p, d, q) 为 (1, 1, 1) 的初始设置
model = ARIMA(data["generation"], order=(1, 1,1))
fitted_model = model.fit()

# 预测未来 30 天的发电量
forecast_steps = 4
forecast = fitted_model.forecast(steps=forecast_steps)

# 可视化结果
plt.figure(figsize=(10, 6))
plt.plot(data.index, data["generation"], label="Historical Generation")
plt.plot(range(len(data) + 1, len(data) + forecast_steps + 1), forecast, label="Forecasted Generation", color="orange")
plt.title("Power Generation Forecast using ARIMA")
plt.xlabel("Time Index")
plt.ylabel("Generation")
plt.legend()
plt.show()

# 打印预测结果
print(f"Forecasted Generation for next {forecast_steps} days:\n", forecast)
