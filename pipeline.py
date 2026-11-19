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

#download_file(FILES_URL + 'teams.csv', os.path.join(RAW_DIR,'teams.csv'))


# 5. Написати функцију extract(raw_dir: str) -> dict која преузима сва четири извора у
# raw_dir и враћа речник са четири DataFrame-а: 'orders', 'products', 'teams','matches'
# 1. Поруџбине читамо помоћу API-ја (fetch_all) (orders.json)
# 2. Фајлови products.csv, teams.csv, matches.parquet се добијају помоћу функције
# download_file
# 3. Поруџбине у DataFrame: pd.json_normalize(orders, sep='_')
# Након тога преименовати колоне
# customer_name у customer
# customer_city у city
# 4. Остало читамо из raw_dir (где смо у кораку 2 скинули податке)
# По потреби, pd.read_csv(...) или pd.read_parquet(...)
# 5. Провера: orders (1852, 8), products (108, 7), teams (20, 5), matches (120, 9)

def extract(raw_dir: str) -> dict:
    fetch_all(BASE_URL + 'orders/page-1.json') #vraca listu recnika
    download_file(FILES_URL + 'products.csv', os.path.join(RAW_DIR,'products.csv')) 
    download_file(FILES_URL + 'teams.csv', os.path.join(RAW_DIR,'teams.csv'))
    download_file(FILES_URL + 'matches.parquet', os.path.join(RAW_DIR,'matches.parquet'))
    with open(os.path.join(raw_dir, 'orders.json'), 'r', encoding='utf-8') as f:
        orders = json.load(f)
        orders=pd.json_normalize(orders, sep='_')
        orders=orders.rename(columns={'customer_name': 'customer', 'customer_city': 'city'})
    products=pd.read_csv(os.path.join(raw_dir,'products.csv'))
    teams=pd.read_csv(os.path.join(raw_dir, 'teams.csv'))
    matches=pd.read_parquet(os.path.join(raw_dir, 'matches.parquet'))
    dict = {
        'orders': orders,
        'products': products,
        'teams': teams,
        'matches': matches
    }
    return dict


#pomocna funkcija
def remove_duplicate_products(df: pd.DataFrame) -> pd.DataFrame:
    is_dup = df.duplicated('product_id', keep='first')
    return df[~is_dup]


# 6. Производи. Написати функцију clean_products(df: pd.DataFrame) -> pd.DataFrame
# која чисти каталог производа
# Ако се понавља исти производ, садржати први ред за сваки product_id
# team_code треба да буде без размака, има велика слова (npm -> NPM), празан ред
# остаје празан (то су производи лиге, без тима)
# category треба да буде без размака, има мала слова
# price је текст у три облика '1490.00', '1490 RSD', '1490,00' а треба да постане
# само float (у сваком случају)
# Помоћ: .str.replace(' RSD', '', regex=False), pd.to_numeric(...)
# active трансформишемо у True/False ('yes', 'Yes', 'YES' постају True), све остало
# постаје False
# Output: 105 редова, price је типа float64, active је True за 101 производ
# Ред 1003 изгледа овако: {'team_code': 'NPM', 'category': 'scarves',
# 'price': 1490.0, 'active': True, ...}

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df=df.copy()
    data=remove_duplicates_products(df)
    if not data['team_code'].isna():
        data['team_code']=data['team_code'].str.strip().str.upper()
    data['category']=data['category'].str.strip().str.lower()
    data['price'] = pd.to_numeric(
        data['price'].str.replace(' RSD', '', regex=False),
         # Optional: turns unparseable values into NaN instead of crashing
        )
    data['active']=data['active'].str.strip().str.lower()=='yes'
    return data
     

# 7. Поруџбине. Написати функцију clean_orders(df: pd.DataFrame) -> pd.DataFrame
# order_id, customer, city, payment без размака;
# order_id велика слова
# customer и city -> title()
# Град који недостаје (isna) -> 'Unknown'

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    clean_df=df.copy()
    clean_df['order_id']=clean_df['order_id'].str.strip()
    clean_df['customer']=clean_df['customer'].str.strip().str.title()
    clean_df['city']=clean_df['city'].str.strip().str.title()
    clean_df['payment']=clean_df['payment'].str.strip()
    clean_df['city'] = clean_df['city'].fillna('Unknown')
   
    return clean_df