import asyncio
import discord # 跟DC連動
import requests # 用來傳資料給 n8n
from single_video import summary # 引入原本處理yt的function
import os

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