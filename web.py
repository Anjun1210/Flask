import requests
import urllib3
from bs4 import BeautifulSoup

from flask import Flask, render_template,request,make_response,jsonify
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入蕭安均的網站</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=安均&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>Post傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/search>靜宜資管老師查詢</a><hr>"
    link += "<a href=/spider>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    link += "<br><a href=/spidermovie>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<br><a href=/searchmovie>輸入片名關鍵字,可以查詢資料庫符合的電影</a><hr>"
    link += "<br><a href=/road>台中市十大肇事路口</a><hr>"
    link += "<br><a href=/weather>天氣預報查詢</a><hr>"
    link += "<br><a href=/rate>本週新片進DB</a><hr>"
    link += "<br><a href=/webdemo>聊天機器人</a><hr>"

    return link

@app.route("/webdemo")
def webdemo():
    #R = "<a href='/'>返回首頁</a><hr>"
    return render_template("webdemo.html")
    #return R

@app.route("/webhook", methods=["POST"])
def webhook():
    # 建立 request 物件
    req = request.get_json(force=True)
    
    # 安全地取得 action，避免 json 格式不對時當機
    action = req.get("queryResult", {}).get("action")
    
    # 預設的回覆內容（如果 action 不是 rateChoice，就會回傳這個）
    info = "我是蕭安均設計的機器人，目前還不支援這個動作喔！"

    if action == "rateChoice":
        # 取出 Dialogflow 傳過來的分級參數，統一命名為 rate_param
        rate_param = req["queryResult"]["parameters"]["rate"]
        
        # 判斷如果是陣列，就取出第一個值
        if isinstance(rate_param, list) and len(rate_param) > 0:
            target_rate = rate_param[0]
        else:
            target_rate = str(rate_param)

        # 查詢 Firestore
        db = firestore.client()
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.where("rate", "==", target_rate).get()
        
        movie_list = []
        for doc in docs:
            movie_data = doc.to_dict()
            movie_list.append(movie_data["title"])
        
        if movie_list:
            info = f"我是蕭安均設計的機器人,為您找到本週上映的【{target_rate}】電影有：\n" + "、".join(movie_list)
        else:
            info = f"我是蕭安均設計的機器人,抱歉，本週資料庫中沒有找到【{target_rate}】的電影。"

        # 組合好字串後回傳給 Dialogflow
        #return make_response(jsonify({"fulfillmentText": info}))

    # 其他未知的 action 統一回傳預設 info
    return make_response(jsonify({"fulfillmentText": info}))

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=["GET", "POST"])
def weather():
    R = "<h1>天氣預報查詢</h1>"
    R += "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST'>"
    R += "請輸入欲查詢縣市 : <input name='city' placeholder='縣市名稱'> "
    R += "<button>查詢</button></form><hr>"

    if request.method == "POST":
        
        city = request.form.get("city").strip()
        city = city.replace("台", "臺")
        
        api_key = "rdec-key-123-45678-011121314" 
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={api_key}&locationName={city}"

        try:
            response = requests.get(url)
            data = response.json()

            if data["success"] == "true" and data["records"]["location"]:
                location_data = data["records"]["location"][0]
                weather_elements = location_data["weatherElement"]

                # 提取需要的資料 (通常 index 0 是最近的時段)
                # Wx: 天氣現象, PoP: 降雨機率, MinT: 最低溫, MaxT: 最高溫
                status = weather_elements[0]["time"][0]["parameter"]["parameterName"]
                pop = weather_elements[1]["time"][0]["parameter"]["parameterName"]
                min_t = weather_elements[2]["time"][0]["parameter"]["parameterName"]
                max_t = weather_elements[4]["time"][0]["parameter"]["parameterName"]

                R += f"<h2>{city} 最新天氣預報</h2>"
                R += f"天氣狀況：{status}<br>"
                R += f"降雨機率：{pop}%<br>"
                R += f"氣溫範圍：{min_t}°C - {max_t}°C<hr>"
            else:
                R += f"<p style='color:red;'>找不到「{city}」的資料，請確保輸入正確的縣市全名（包含『臺』或『台』）。</p>"
        except Exception as e:
            R += f"查詢出錯：{e}"

    return R

@app.route("/road")  # 修正 1：將 road 改為 route
def road():
    # 稍微調整 HTML 標籤讓標題正確顯示
    R = "<h1>台中市十大肇事路口(113年10月)作者:蕭安均</h1><br>"
    
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"

    # 準備偽裝成瀏覽器的 Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 發送請求時，把 headers 帶進去
        Data = requests.get(url, headers=headers)
        Data.raise_for_status() 
        JsonData = Data.json()

        # 印出資料
        for item in JsonData:
            R += item["路口名稱"] + " 原因:" + item["主要肇因"] + "<br>"

        return R

    # 修正 2：補上 except 區塊，捕捉並處理錯誤
    except Exception as e:
        return f"發生錯誤，無法抓取資料：{e}"

@app.route("/searchmovie", methods=["GET", "POST"])
def searchmovie():
    R = "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST'>輸入片名: <input name='keyword'> <button>查詢</button></form><hr>"

    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        docs = db.collection("電影2B").get()
        
        for doc in docs:
            movie = doc.to_dict()
            # 只要關鍵字有出現在片名中就印出來
            if keyword in movie["title"]:
                R += f"編號：{doc.id}<br>"
                R += f"片名：{movie['title']}<br>"
                R += f"日期：{movie['showDate']}<br>"
                R += f"<a href='{movie['hyperlink']}'>介紹網頁</a><br>"
                R += f"<img src='{movie['picture']}'><hr>"

    return R
    
@app.route("/spidermovie")
def spidermovie():
    R = ""

    db = firestore.client()


    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastupdate = sp.find(class_="smaller09").text.replace("更新時間：","")
    result=sp.select(".filmListAllX li")
    #info = ""
    total = 0
    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/","").replace ("/","")
      title = item.find(class_="filmtitle").text
      picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
      showdate = item.find(class_="runtime").text[5:15]
      #info += movie_id + "\n" + showdate + "\n" + title + "\n" + picture + "\n" + hyperlink + "\n\n"
        
      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showdate,
          "lastUpdate": lastupdate
      }

      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

    R += "網站最近更新日期：" + lastupdate + "<br>" + "總共爬取" + str(total) + "部電影到資料庫"

    return R

@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    # 1. 建立標題、返回首頁連結與搜尋表單
    R = "<h1>近期上映電影</h1>"
    R += "<a href='/'>返回首頁</a><hr>"
    R += "<form method='POST' action='/movie1'>"
    R += "請輸入電影名稱: <input type='text' name='keyword'>"
    R += "<button type='submit'>搜尋</button>"
    R += "</form><hr>"

    # 2. 接收使用者輸入的關鍵字 (預設為空字串)
    keyword = ""
    if request.method == "POST":
        keyword = request.form.get("keyword", "")

    # 3. 進行網頁爬蟲
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    found = False # 用來記錄是否有找到相符的電影

    # 4. 處理爬取到的資料並進行比對
    for item in result:
        a_tag = item.find("a")
        img_tag = item.find("img")
        
        if a_tag and img_tag:
            movie_title = img_tag.get("alt")
            
            # 如果沒有輸入關鍵字 (keyword是空的) 就顯示全部
            # 如果有輸入關鍵字，就檢查關鍵字是否包含在電影名稱中
            if not keyword or (keyword in movie_title):
                found = True
                L = "https://www.atmovies.com.tw/" + a_tag.get("href")
                R += "<a href=" + L + ">" + movie_title + "</a><br>"
                post = "https://www.atmovies.com.tw/" + img_tag.get("src")
                R += "<img src=" + post + "> </img><br><br>"
    
    # 5. 如果搜尋了但沒找到任何結果，給予友善提示
    if keyword and not found:
        R += f"<h3>找不到包含「{keyword}」的電影喔！</h3>"
            
    return R

@app.route("/spider")
def spider():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")
    for i in result:
        R += i.text + i.get("href")+"<br>"
    return R

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    if request.method == "POST":
        keyword = request.form.get("keyword")
        results = []
        collection_ref = db.collection("資管二B")
        docs = collection_ref.get()
        
        for doc in docs:
            teacher = doc.to_dict()
            
            if "name" in teacher and keyword in teacher["name"]:
                results.append(teacher)
        
        return render_template("search.html", keyword=keyword, results=results)
    
    return render_template("search.html")

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    return render_template("mis20260305.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name = user,dep = d,course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")
@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            y = float(request.form["y"])
            opt = request.form["opt"]
            
            if opt == "pow":
                # 次方計算：x 的 y 次方
                result = x ** y
                msg = f"{x} 的 {y} 次方 = {result}"
            elif opt == "root":
                # 根號計算：x 的 y 次根號 (即 x 的 1/y 次方)
                if x < 0 and y % 2 == 0:
                    msg = "錯誤：負數不能開偶數次方根"
                else:
                    result = x ** (1/y)
                    msg = f"{x} 的 {y} 次方根 = {result}"
            else:
                msg = "無效的運算"
        except Exception as e:
            msg = f"計算出錯：{str(e)}"
            
        return f"<h1>計算結果</h1><p>{msg}</p><a href='/math'>重新計算</a>"
    
    return render_template("math.html")

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("資管二B")    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()    
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result


if __name__ == "__main__":
    app.run(debug=True)
