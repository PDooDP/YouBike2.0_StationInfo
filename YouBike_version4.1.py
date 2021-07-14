# -*- coding: utf-8 -*-
"""
Created on Wed May  5 20:44:25 2021

@author: Dennis
"""
"""
========================================================================================
sna(sna 場站名稱(中文))、sarea(sarea 場站區域(中文))、ar(ar 地址(中文))、
snaen(snaen 場站名稱(英文))、sareaen(sareaen 場站區域(英文))、aren(aren 地址(英文))、
sno(sno 站點代號)、tot(tot 場站總停車格)、sbi(sbi 場站目前車輛數量)、mday(mday 資料更新時間)、
lat(lat 緯度)、lng(lng 經度)、bemp(bemp 可還車位數)、act(act 場站暫停狀態)
========================================================================================
"""
from tkinter import *
from tkinter import ttk
import re
import requests
import json
import time
import numpy as np
import pandas as pd
import schedule
from selenium import webdriver

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
           AppleWebKit/537.36 (KHTML, like Gecko) \
           Chrome/87.0.4280.141 \
           Safari/537.36"}

global park_columns, TP_url, TC_url, KS_url, count
TP_url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
TC_url = "https://datacenter.taichung.gov.tw/swagger/OpenData/9af00e84-473a-4f3d-99be-b875d8e86256"
KS_url = "http://od-oas.kcg.gov.tw/api/service/Get/b4dd9c40-9027-4125-8666-06bef1756092"
park_columns = ["sarea","sna","sno","tot","sbi","bemp","act","ar","mday","lat","lng"]
ot_columns = ["mday", "lat", "lng"]

# functions
# 針對不同的城市抓取、分析相對應的json檔
# 避免因使用者連續向網站要求資料導致被封鎖,
# 故加入time設定2秒鐘後才向網站要求資料
def loadJson(city):
    time.sleep(2)   
    url = ""
    if city == "台北":
        url = TP_url
    elif city == "台中":
        url = TC_url
    elif city == "高雄":
        url = KS_url
    else:
        print("something went wrong")

    data = requests.get(url, headers = headers)
    data.encoding = "utf-8"
    data = json.loads(data.text)
    
    # 三個城市的json格式皆不相同, 呼叫dataPrePorcess函式轉成相同格式方便資料整理
    if city == "台北":
        data_url = data
    elif city == "台中":
        data_url = data["retVal"]
    elif city == "高雄":
        data_url = data["data"]["retVal"]
    else:
        print("Invalid URL")
    # print(df_bike["mday"][0])
    return dataPreProcess(data_url)

# 資料載入dataframe前的前置作業
# 由於取得的data_bike是串列, 改成字典較好做資料處理
# 將串列加入key值轉成新的字典: new_data_bike
# 回傳newDataList函式前處理好的資料到loadJson函式
def dataPreProcess(data_bike):
    index_list = []
    for i in range(len(data_bike)):
        index_list.append(i)
    new_data_bike = dict(zip(index_list, data_bike))    #處理好的新字典
    return [newDataList(data) for data in new_data_bike.values()]

# json資料的前處理
# 將sna的YouBike2.0_字串移除, act改成1 => 開放 ; 0 => 暫不開放
# mday用replace()的函式和regular expression比較好閱讀的時間格式yyyy-mm-dd hh:mm:ss
def newDataList(old_data):
    global new_data
    new_data = []
    tmp = old_data["act"]
    new_data.append(old_data["sarea"])
    new_data.append(old_data["sna"].replace("YouBike2.0_",""))
    new_data.append(old_data["sno"])
    new_data.append(old_data["tot"])
    new_data.append(old_data["sbi"])
    new_data.append(old_data["bemp"])
    if tmp == "0":
        new_data.append(str(old_data["act"]).replace("0", "暫時關閉"))
    else:
        new_data.append(str(old_data["act"]).replace("1", "開放"))
    new_data.append(str(old_data["ar"]))
    # 設定mday格式為yyyy-mm-dd hh:mm:ss
    new_data.append(old_data["mday"].replace(old_data["mday"], re.sub(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', r'\1-\2-\3 \4:\5:\6', old_data["mday"])))
    new_data.append(old_data["lat"])
    new_data.append(old_data["lng"])
    return new_data
    
# 資料整理完後, 建立新的DataFrame
def initDF():
    global df_bike  # 建立全域變數df_bike
    df_bike = pd.DataFrame(loadJson(varCityCombo.get()))
    df_bike.columns = ["sarea", "sna", "sno", "tot", "sbi", "bemp", "act", "ar", "mday", "lat", "lng"]

# 找出哪幾區有提供YouBike2.0停車站服務, 將地區資料寫入下拉式選單供使用者選擇
def funcDistrict():
    arrArea = df_bike.sarea.drop_duplicates().values.tolist()   # 找出行政區的唯一值
    return arrArea

# 抓取該行政區Youbike停車站資訊
def funcStation():
    arrStationName = df_bike.loc[df_bike.sarea == varAreaCombo.get(), "sna"].values.tolist()
    return arrStationName

# 抓取該城市所有行政區的YouBike停車站資訊
def funcShowAll():
    funcDelView()
    arrInfo = df_bike.values.tolist()
    funcDisplayResult(arrInfo)
    area_name["value"] = funcDistrict()

# 當使用者選擇城市時, 載入相對應的url (json格式) (combobox1)
def comboCityChg(event):
    funcDelView()
    park_name["values"] = ""
    area_name.set("")
    park_name.set("")
    print(varCityCombo.get())
    initDF()    # 載入DataFrame
    funcShowAll()
    btnUpdate["state"] = NORMAL

# combobox2被選擇時與combobox3做連動
# 並列出該地區所有的停車站
def comboDistChg(event):
    funcDelView()
    park_name["values"] = ""
    park_name["value"] = funcStation()
    park_name.set("")
    arrInfo = df_bike.loc[df_bike.sarea == varAreaCombo.get(), park_columns].values.tolist()
    funcDisplayResult(arrInfo)
    print(varParkCombo.get(), varAreaCombo.get())

# 找出該停車站的資訊 (combobox3)
def comboStationChg(event):
    funcDelView()
    print(varAreaCombo.get(), varParkCombo.get())
    arrInfo = df_bike.loc[df_bike.sna == varParkCombo.get(), park_columns].values.tolist()
    funcDisplayResult(arrInfo)

# 當使用者雙擊treevie的itemw時，取得場站經緯度並呼叫maps進行導航
def funcDoubleClick(event):
    item = myTree.selection()
    lat = myTree.set(item, column = "lat")
    lng = myTree.set(item, column = "lng")
    funcMaps(lat, lng)

# 用selenium在google maps自動取得目前位置並導航至場站地點
def funcMaps(lat, lng):
    url = "https://www.google.com/maps"
    browser = webdriver.Chrome()
    browser.get(url)
    browser.implicitly_wait(60)     # 隱含等待60秒
    test = browser.find_element_by_id("mylocation").click() # 目前位置
    btnNavigate = browser.find_element_by_id("searchbox-directions").click()
    txtSearchBox1 = browser.find_element_by_css_selector("#sb_ifc52 > input").send_keys(lat + ", " + lng)
    btnSearch = browser.find_element_by_css_selector("#directions-searchbox-1 > button.searchbox-searchbutton").click()

# 將取得的資料顯示在treeview元件上
def funcDisplayResult(arrInfo):
    count = 0
    for item in arrInfo:
        myTree.insert(parent="", index = "end", iid = count, text = "", values = item)
        count += 1

# 當使用者按下update鍵, 針對區域或場站進行資料更新
def funcUpdate():
    # 重新呼叫一次json檔, 並刷新現有的Dataframe
    initDF()
    # loadJson(varCityCombo.get())
    if varAreaCombo.get() != "" and varParkCombo.get() != "":
        arrInfo = df_bike.loc[df_bike.sna == varParkCombo.get(), park_columns].values.tolist()
        print("park_:" + df_bike["mday"][0])
    elif varAreaCombo.get() != "" and varParkCombo.get() == "":
        arrInfo = df_bike.loc[df_bike.sarea == varAreaCombo.get(), park_columns].values.tolist()
        print("Area_:" + df_bike["mday"][0])
    else:
        arrInfo = df_bike[park_columns].values.tolist()
    funcDelView()
    funcDisplayResult(arrInfo)

# 清空treeview裡的資料
def funcDelView():
    myTree.delete(*myTree.get_children())

# ==================================使用者介面==================================
window = Tk()
window.title("YouBike2.0停車站資訊 version 4.1")
window.geometry("1270x330")  # width * height
# window.iconbitmap("youbike_icon.ico")

# combobox 1: search by city
varCityCombo = StringVar(window)
varAreaCombo = StringVar(window)
varParkCombo = StringVar(window)
city_name = ttk.Combobox(window, textvariable = varCityCombo, values = ["台北","台中","高雄"], state = "readonly")
city_name.grid(row = 1, column = 0)
city_name.bind("<<ComboboxSelected>>", comboCityChg)

# combobox 2: search by district
area_name = ttk.Combobox(window, textvariable = varAreaCombo, values = "", state = "readonly")
area_name.grid(row = 1, column = 1)
area_name.bind("<<ComboboxSelected>>", comboDistChg) # 當combobox發生異動時

# combobox 3, search by station
park_name = ttk.Combobox(window, textvariable = varParkCombo, values = "", state = "readonly")
park_name.grid(row = 1, column = 2)
park_name.bind("<<ComboboxSelected>>", comboStationChg)

# 設定TreeView
myTree = ttk.Treeview(window)
myTree["columns"] = park_columns

# Format columns
myTree.column("#0", width = 0, stretch = NO)
myTree.column("sarea", width=60, anchor = W)
myTree.column("sna", width=200, anchor = W)
myTree.column("sno", width=70, anchor = W)
myTree.column("tot", width=70, anchor = CENTER)
myTree.column("sbi", width=90, anchor = CENTER)
myTree.column("bemp", width=90, anchor = CENTER)
myTree.column("act", width=70, anchor = CENTER)
myTree.column("ar", width=295, anchor = W)
myTree.column("mday", width = 120, anchor = W)
myTree.column("lat", width = 80, anchor = W)
myTree.column("lng", width = 80, anchor = W)

# Create headings 
myTree.heading("#0", text="Label", anchor = W)
myTree.heading("sarea", text="場站區域", anchor = W)
myTree.heading("sna", text = "場站名稱", anchor = W)
myTree.heading("sno", text = "站點代號", anchor = W)
myTree.heading("tot", text = "總停車格", anchor = CENTER)
myTree.heading("sbi", text = "可借車輛數", anchor = CENTER)
myTree.heading("bemp", text = "可還車位數", anchor = CENTER)
myTree.heading("act", text = "場站狀態", anchor = CENTER)
myTree.heading("ar", text = "地址", anchor = W)
myTree.heading("mday", text = "更新時間", anchor = W)
myTree.heading("lat", text = "緯度", anchor = W)
myTree.heading("lng", text = "經度", anchor = W)
myTree.grid(row = 9, column = 0, columnspan = 3, pady = 10)

# 雙擊treeview上的item時觸發事件
myTree.bind("<Double-1>", funcDoubleClick)

# create a vertical scrollbar
vScroll = ttk.Scrollbar(window, orient="vertical", command = myTree.yview)
vScroll.grid(row = 9, column = 3, pady = 10, sticky = "ns")

myTree.configure(yscrollcommand = vScroll.set)

lbCity = Label(window, text = "城市: ").grid(row = 0, column = 0)
lbDistrict = Label(window, text = "選擇區域: ").grid(row = 0, column = 1)
lbName = Label(window, text = "停車場名稱: ").grid(row = 0, column = 2)

btnUpdate = Button(window, text = "Update", command = funcUpdate)
btnUpdate.grid(row = 15, column = 2)
btnUpdate["state"] = DISABLED

# btnMaps = Button(window, text = "Get", command = funcMaps)
# btnMaps.grid(row = 15, column = 1)

window.mainloop()
# ==================================使用者介面==================================
