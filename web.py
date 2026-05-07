import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template,request
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

    return link

@app.route("/road")  # 修正 1：將 road 改為 route
def road():
    # 稍微調整 HTML 標籤讓標題正確顯示
    R = "<h1>台中市十大肇事路口(113年10月)</h1><br>"
    
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
