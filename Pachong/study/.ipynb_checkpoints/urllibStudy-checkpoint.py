# 爬虫学习
import requests


try:
    response = requests.get("https://jsonplaceholder.typicode.com/posts", timeout=0.1)
    print(response.json())
except requests.Timeout:
    print("请求超时")



