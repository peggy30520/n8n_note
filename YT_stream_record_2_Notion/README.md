# n8n：YT串流數據→Notion

為了初步認識n8n，所以想了一個簡單的題目來實做一下。
最後決定利用n8n結合python，並搭配Notion，來搭造個人的簡易數據資料庫，以YT直播紀錄檔作為抓取資料的目標，針對指定的YTR來觀測一下相關的數據(EX:新增會員數、superchat金額...)

## Step 1：安裝/建立n8n帳戶，並開啟n8n
因為雲端版的要課金，所以我自己是先載了本地版的來玩看看，不過部分功能會受到限制；有興趣的人可以依照自己的需求尋找安裝或是使用n8n的方式。

我個人的安裝是參考：[How to Install and Self-Host n8n For Free](https://www.youtube.com/watch?v=fh5Mmi1fRBc)，是不需要docker的版本。

### 簡易流程
第2~4點，需在cmd裡面輸入指令執行。
1. 下載[Node.js](https://nodejs.org/en/download)
2. 確認是否安裝成功
    ```
    node --version
    ```
3. 安裝n8n
    ```
    npm install n8n -g
    ```
5. 開啟n8n
    ```
    n8n
    ```
    成功的話，會顯示下圖資訊
    ![image](https://hackmd.io/_uploads/rJ9PKhWPZe.png)
1. 打開連結(可以按著Ctrl點選連結，也會在瀏覽器打開)
    第一次進入的話，會請使用者建立帳密
    **Tips**：容易忘記的人最好要特別記下來，因為是本地端的服務，所以雖然有forget password的按鈕，但實際上不會幫助你找回密碼(By 差點失去帳戶的人
    ![image](https://hackmd.io/_uploads/HkYPsnZPZg.png)

3. 一切順利的話，就會進入workflow主控台
![image](https://hackmd.io/_uploads/SkNYh3Zv-l.png)

## Step 2：設定Notion API
在開始建立流程前，先把Notion的API設定一下，這樣n8n才知道要把資料更新到哪個Notion的頁面當中。


1. 進入Notion的Integrations頁面，並新增
![image](https://hackmd.io/_uploads/B1zM-TZv-l.png)
1. 完成命名，並選取要上傳資料到的workspace為何，最後按Create
![image](https://hackmd.io/_uploads/H1j4z6ZwWg.png)
2. 在Internal integration secret點選show，並複製API key
![image](https://hackmd.io/_uploads/HJbTQaWvZl.png)
1. 回到n8n的頁面，新增Credential，選擇Notion API
![image](https://hackmd.io/_uploads/r1ls4aWwbg.png)
![image](https://hackmd.io/_uploads/SJPZrpWDZe.png)

3. 填入API key，觀察是否連結成功
![image](https://hackmd.io/_uploads/ryC3BaWvZx.png)
![image](https://hackmd.io/_uploads/ryBeUT-D-e.png)
    
1. 回到Notion，開設一個database page，連結到剛剛建立的Integration
![image](https://hackmd.io/_uploads/BJ5puTbvZe.png)

## Step 3：建立Python跟n8n的連結

關於如何對YT直播的聊天紀錄檔處理，我是採用在本地跑Python script，再上傳到n8n。
也許有機會可以讓n8n去主動call Python來跑，但我目前還沒有找到相關的方式，也歡迎分享給我~

### 1. 開一個空的workflow，並建立webhook
![image](https://hackmd.io/_uploads/HkWela-vWg.png)

全新的頁面如下：
![image](https://hackmd.io/_uploads/Sk4fgaZwbl.png)
點選"+"，並選擇webhook
![image](https://hackmd.io/_uploads/Hk1oT6bv-g.png)

從這邊就可以獲得，python要上傳給n8n的網址路徑了
![image](https://hackmd.io/_uploads/S1UfRTbD-l.png)


### 2. 建立Python script處理直播聊天紀錄

有一個open source的library在協助抓直播聊天記錄檔的資料，也就是`chat_downloader`。
不過目前[官方release的版本](https://github.com/xenova/chat-downloader)有點問題，issue中有好心人士fork原始的版本並進行修正了，我後來也是使用[好心人士的版本](https://github.com/Indigo128/chat-downloader)才能順利下載資料，有需要的話，請自行參考安裝。
另外，如果該直播紀錄檔有被關閉聊天紀錄，就沒有辦法取得資訊囉。
#### 簡述重點 (以該workflow尚未published的成果為例)
1. 使用`chat_downloader`把只跟superchat相關的資訊取出，並憑個人需求整理成json格式，並上傳到n8n

    ```
    from chat_downloader import ChatDownloader

    # 影片網址
    video_url = "https://www.youtube.com/watch?v=<影片ID>"

    # 欲上傳到n8n的資料，json格式
    stats = {
        "video_url": video_url,
        "currency": "TWD",
        "sc_amoount": 0,
        "sc_count": 0,
        "new_member": 0,
        "old_member": 0
    }

    downloader = ChatDownloader()
    df = downloader.get_chat(video_url, message_groups=['superchat'])
    for message in df:
        # 憑個人需求設計，在此更新json內容
    
    # 下載.json，方便確認一下資料處理完的內容
    file_name = <欲儲存位置>
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
    
    # 卡一個input，讓使用者去執行n8n的workflow
    # 如果建立好的n8n是一直在監聽的階段，應該可以省略此步驟
    check = input("Listen to Webhook(y/n): ")
    
    # n8n webhook node裡面的網址
    n8n_webhook_url = "http://localhost:5678/webhook-test/<path>"
    
    # 執行並發送
    if(check == "y"):
        try:
            response = requests.post(n8n_webhook_url, json=stats)
            print(f"狀態碼: {response.status_code}")
            print(f"n8n 回傳內容: {response.text}")

            if response.status_code == 200:
                print("傳送成功！請檢查 n8n 畫面。")
            elif response.status_code == 404:
                print("錯誤：找不到 Webhook。請確認 n8n 是否正在 'Listen for Test Event'。")

        except Exception as e:
            print(f"發生錯誤: {e}")
    ```
1. 執行 .py，並確認workflow已取得資訊
![image](https://hackmd.io/_uploads/H116cgMPbe.png)
出現input()之後，記得先去執行workflow，表明n8n要開始監聽事件了。
**注意**：在testing的階段只能監聽兩分鐘
![image](https://hackmd.io/_uploads/S1OfOlfwbg.png)
確認已在監聽狀態後，輸入y
![image](https://hackmd.io/_uploads/rJ9ZjefP-e.png)
有打勾就代表執行完成
![image](https://hackmd.io/_uploads/rkhFslzD-g.png)
點選Webhook node，可以確認拿到的資訊是否正確
![image](https://hackmd.io/_uploads/SJyh2xGvbx.png)

## Step 4：設計workflow，將資料匯入Notion
Webhook後面的節點可以自由發揮，我自己還有另外抓的資料有：
* 透過影片網址，抓取影片標題及發佈時間
* 直接去找該YTR的相關Query，取得頻道瀏覽總次數及訂閱者數量
* 紀錄上傳該筆資料的時間

最後把所有的資訊整合起來，匯入Notion

![image](https://hackmd.io/_uploads/By7qe-zDWl.png)

### 匯入Notion說明
1. 回到notion的database page，把相關的欄位先設定好。
![image](https://hackmd.io/_uploads/B1Pb4WMPZg.png)
1. 在workflow裡面新增一個Notion node，選擇`Create a database page`
![image](https://hackmd.io/_uploads/B1sTSZGPbl.png)
3. 點選Notion node，設定Credential(API)，以及要連結到哪一個database page
    ![image](https://hackmd.io/_uploads/Bk-ISbMv-x.png)
1. 在Properties的部分，把INPUT與Notion欄位做對應
    * Key Name or ID 的下拉式選單會直接link到Notion的欄位
    * 記得INPUT與Notion欄位的type需一致，比如說都是number，都是string
    * 成功後執行後，也會顯示上傳到Notion的成果(如箭頭的指向變化)
![image](https://hackmd.io/_uploads/HJcIDbGwWe.png)

## Step 5：透過Notion Chart觀察數據
將以上流程看是用手動trigger，或是偵測有新直播紀錄檔就抓網址然後trigger，之類的就可以完成資料的蒐集。(我個人不會一直開著電腦跑流程，所以還是手動trigger的部分，但不得不說也是少很多工了)

最後，推薦可以在Notion額外開一個database page做統整(下稱Summary page)，這樣就可以保持原本的database的乾淨(?)，不用怕突然改到甚麼。
在Notion裡面可以設定database page的link(紅框)，所以就可以把Summary page，link到 database page，專門呈現數據變化。

想要呈現統整甚麼內容，都可以自行發揮滿有趣的XD
比如說大家對於什麼樣的直播內容會斗內最多之類的www

![image](https://hackmd.io/_uploads/Byou3bfDZg.png)

## 小提醒
* YT_superchat_record.json 可直接匯入workflow當中，其中我有把指定YTR相關的key、id之類的空掉，請自行填入

## 感謝觀看!
如果有任何建議或感想，歡迎分享!