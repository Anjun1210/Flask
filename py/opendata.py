import requests

url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"

# 1. 準備偽裝成瀏覽器的 Headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    # 2. 發送請求時，把 headers 帶進去
    Data = requests.get(url, headers=headers)
    
    # 檢查伺服器有沒有回傳錯誤代碼 (例如 404 找不到網頁)
    Data.raise_for_status() 

    # 3. requests 有內建解析 JSON 的功能，可以直接轉成字典或串列
    JsonData = Data.json()

    # 4. 印出資料
    for item in JsonData:
        print(item["路口名稱"], "原因:", item["主要肇因"])
        print()

except requests.exceptions.RequestException as e:
    print(f"連線發生錯誤：{e}")
except ValueError:
    print("抓取成功，但回傳的資料不是有效的 JSON 格式")