# n8n：本地→雲端(Docker+GCP) — Discord→Notion

前一個版本是只能在本地執行，因為不想要一直開著電腦，要上傳新的資訊還是有不少前置作業(ex：開n8n、執行python...)，所以就打算用Docker打包到雲端，前面再串個DC的bot作為輸入影片網址的媒介，這樣不管在哪裡都可以更新資訊啦!

## Step 1: 將DC納入流程中
加入DC之後的流程如下：
1. 用python監控bot是否獲得yt網址訊息 **(NEW!)**
2. 收到後把網址拿去跑之前整理數據的python code
3. 把資料回傳給n8n並更新到notion

### 設定DC
1. 進入[開發者後台](https://discord.com/developers/applications)(登入自己的帳號就可以囉)，建立新的Application
    ![image](https://hackmd.io/_uploads/rJhc7jTP-l.png)

    取個名字、勾個同意條款，之後接著按`Create`就建立好了
    ![image](https://hackmd.io/_uploads/SJDrViaDWg.png)
2. 設定Bot
    先選到Bot的標籤頁
    ![image](https://hackmd.io/_uploads/rJTbPipvbx.png)
    
    取得Token(記得把它先存下來)
    ![image](https://hackmd.io/_uploads/ryDhwo6PWl.png)
    
    把bot可讀取甚麼資訊打勾，記得`Save changes`
    ![image](https://hackmd.io/_uploads/SJhLOoTPbl.png)

3. 把Bot加入伺服器中
    點選OAuth2標籤頁，並打勾`bot`
    ![image](https://hackmd.io/_uploads/SyoXqjpwWx.png)
    
    設定Bot Permissions，勾選`Send Messages`、`Read Message History`
    ![image](https://hackmd.io/_uploads/rJETqipP-e.png)
    
    複製Generated URL，並開個分頁貼上去
    ![image](https://hackmd.io/_uploads/Sy282s6P-e.png)
    
    設定要跟哪個伺服器連結，完成授權
    ![image](https://hackmd.io/_uploads/HyBFpoavZx.png)
    
    接著，就可以看到有Bot上線啦~
    ![image](https://hackmd.io/_uploads/rJVwCj6DZg.png)

### 用Python監控bot
查了一下發現有個discord的library可以用來監控訊息，滿方便的。
DC的token跟url，我是用docker-compose的設定檔把它傳進去。
```
import os
import asyncio
import discord # 跟DC連動
import requests # 用來傳資料給 n8n
from single_video import summary # 引入原本處理yt的function

TOKEN = os.getenv("DISCORD_TOKEN")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f'機器人 {client.user} 已上線！')

@client.event
async def on_message(message):

    if "youtube.com" in message.content:
        await message.channel.send("🚀 偵測到 YouTube 網址，爬蟲啟動中...")

        # 取得json data
        data = await asyncio.to_thread(summary, message.content) 

        # 跑完後，把json傳給n8n
        if data:
            response = requests.post(N8N_WEBHOOK_URL, json=data)

            if response.status_code == 200:
                await message.channel.send(f"✅ 處理完成！已存入 Notion。總額：{data['sc_amount']}")
            else:
                await message.channel.send("❌ 資料存入 Notion 時出錯了")

client.run(TOKEN)
```

整個流程串好之後，可以直接在該聊天室傳入影片網址，相關的資訊就會更新到Notion了!
![image](https://hackmd.io/_uploads/Sym5C2pD-x.png)

## Step 2: Docker

確認流程一切就緒，就用Docker把環境包一包方便放到雲端吧!
1. 建立Python script的Dockerfile
2. 使用docker compose，以同時開啟n8n及python的Docker

### Docker版本的n8n
n8n本身有提供Docker的版本，只是說拉下來的image不會有登入的資訊，所以只要
1. 把本地n8n的流程.json下載下來
2. 在Docker版本的import進去(要重新辦帳號)
3. 重新設定Notion的Credential

就完成移植了。

### Dockerfile for Python script
這邊提供我的Dockerfile作為參考。
```
# 使用輕量版 Python 作為基底
FROM python:3.10-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 設定容器內的工作目錄
WORKDIR /app

# 安裝chat-downloader(修正非官方版)
RUN pip install chat-downloader@git+https://github.com/Indigo128/chat-downloader

# 複製library清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼到容器內
COPY . .

# 5. 執行 Python 程式
CMD ["python", "<你的檔案>.py"]
```

### 設定docker-compose.yml
使用docker-compose，這樣就可以一次開啟多個container，不用分開XD

```
services:
  # 服務一：n8n(官方有提供image)
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    restart: always

  # 服務二：Python
  discord-bot:
    build: .  # 讀取Dockerfile來build
    environment:
      - DISCORD_TOKEN=<你的token>
      # 在compose的狀況下，直接IP寫n8n就可以通了
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook/<Production url>
    volumes:
      # 掛載你存 JSON 的 Volume
      - sc_json_data:/app/json
    depends_on:
      - n8n     # 確保n8n啟動後，bot才開始監聽
    restart: always

volumes:
  n8n_data:
    name: n8n_data
  sc_json_data:
    name: sc_json_data
```

完成設定檔後，在cmd執行
```
docker-compose up -d --build
```

在Desktop的介面就會看到兩個container被建好囉
![image](https://hackmd.io/_uploads/HkDyVE0vWl.png)

## Step 3: GCP設定
選擇GCP是為了有前三個月$300美金的試用金XD
不過要記得先去設定付費帳戶，不然不給開VM喔~

1. 建立專案(我已經建好了，這邊只是示意一下XD)
點選紅框處，專案名稱自訂，位置選無組織即可
![image](https://hackmd.io/_uploads/BJKVD39d-x.png)
![image](https://hackmd.io/_uploads/HkFfOn9dbx.png)
2. 建立VM
![image](https://hackmd.io/_uploads/SyEKdh9ubg.png)
第一次開啟，會需要先初始化API
![image](https://hackmd.io/_uploads/r1uaOh9u-l.png)
點選：建立執行個體
![image](https://hackmd.io/_uploads/H1nKY35_Zx.png)
VM設定(僅供參考)
    * 位置：us-central1-c
    * 機器類型：e2-micro (2個vCPU, 1GB記憶體)
    * 開機磁碟：類型改為 「標準永久磁碟」，大小設為 30GB
    * 作業系統：Ubuntu
    * 版本：Ubuntu 22.04 LTS
    * 防火牆：勾選「允許 HTTP 流量」；勾選 「允許 HTTPS 流量」。

    點選建立(CREATE)，等VM清單出現剛剛設定好的VM，狀態顯示綠色勾勾表示建立完成。
    ![image](https://hackmd.io/_uploads/r19s2ncO-e.png)
3. 設定防火牆
![image](https://hackmd.io/_uploads/rJzHp39dZe.png)
點選：建立防火牆規則
![image](https://hackmd.io/_uploads/HJcMJ6cuZe.png)
    * 名稱：自訂
    * 目標標記：http-server
    * 來源 IP 範圍(IPv4)：0.0.0.0/0
    * 通訊協定與埠：勾選 tcp 並輸入 5678
4.  回到VM，開啟SSH安裝Docker
    ![image](https://hackmd.io/_uploads/rJ3wPT9uWx.png)

    ```
    # 更新系統並安裝必要工具
    sudo apt-get update && sudo apt-get install -y curl

    # 安裝Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

    # 設定權限
    sudo usermod -aG docker $USER

    # 檢查安裝是否成功
    docker --version && docker compose version
    ```
5. 用SSH把所有資料搬到VM(用nano複製貼上)
    **!注意!**
    docker-compose.yml要新增n8n的網址，紅框白底的部分要填入此VM的外部IP；也因為網址是http，所以要把SECURE_COOKIE設成false，不然n8n打不開。
    ![image](https://hackmd.io/_uploads/HJDqGa9OWx.png)
6. build Docker
    ```
    docker compose up -d --build
    ```
7. 重新設定n8n
    使用外部IP:5678打開n8n，因為又是一個新的建立檔，所以一樣要辦帳號、import workflow的json，設定Notion Credential。
    (因為我辦過帳號了，所以變成是登入頁面)
    ![image](https://hackmd.io/_uploads/r1yfB69OZe.png)

## 完成!
現在就完成了從Discord輸入YT網址，經過GCP的docker處理數據，最後把資料更新到Notion的服務啦!

下圖為n8n執行狀況
![image](https://hackmd.io/_uploads/BJ7fLp9uZg.png)

下圖為VM內的container運行狀況
![image](https://hackmd.io/_uploads/ByDZYaq_Zg.png)
