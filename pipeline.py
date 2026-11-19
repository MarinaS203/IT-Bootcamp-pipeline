import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
BASE_URL = 'https://cvijan.github.io/nss-api/v2/'
FILES_URL = 'https://cvijan.github.io/nss-api/files/'
RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'


os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# 1. Позив API-ја. Написати функцију get_json(url: str) -> dict која шаље GET захтев.
# Подиже грешку ако статус није успешан и враћа одговор као речник ако јесте.
# get_json(BASE_URL + 'status.json')['service'] враћа 'Northern Star Shop
# API'
# get_json(BASE_URL + 'orders/page-99.json') подиже requests.HTTPError

def get_json(url: str) -> dict:
    response=requests.get(url)
    response.raise_for_status()
    return response.json()
# get_json(BASE_URL + 'status.json')['service']
# get_json(BASE_URL + 'orders/page-99.json')


# 2. Странице. Написати функцију fetch_all(first_url: str) -> list која прати next
# линкове и враћа записе са свих страна у једној листи
# Помоћ: urljoin(url, page['next'])
# Input: BASE_URL + 'orders/page-1.json'' даје 1852 записа


def fetch_all(first_url: str) -> list:
    list_of_orders=[]
    while first_url:
        data=get_json(first_url)
        next_page = data.get('next')
        list_of_orders.extend(data.get('data', []))
        if next_page:
            first_url = urljoin(first_url, next_page)
        else:
            first_url = None

    return list_of_orders

# fetch_all(BASE_URL + 'orders/page-1.json')


# 3. Чување сирових података. Написати функцију save_json(records: list, path: str) ->
# None која листу речника уписује у JSON фајл без икаквих измена.
# json.dump(records, f, ensure_ascii=False, indent=2)
# save_json(orders, os.path.join(RAW_DIR, 'orders.json')) -> прави се фајл
# data/raw/orders.json

def save_json(records: list, path: str) -> None:
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# orders=fetch_all(BASE_URL + 'orders/page-1.json')
# save_json(orders, os.path.join(RAW_DIR, 'orders.json'))


# 4. Преузимање фајла. Функција је дата: копирати је без измена у своју ћелију и користити у
# задатку 5

def download_file(url: str, path: str) -> int:
    #Download a file and save it unchanged. Returns its size in bytes.
    response = requests.get(url, timeout=30)
    response.raise_for_status() # 404 and other errors stop here
    with open(path, 'wb') as f: # 'wb' = write bytes, needed for Parquet
        f.write(response.content) # .content = the file's bytes, unchanged
    return len(response.content)
