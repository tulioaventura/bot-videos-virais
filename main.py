import os
import requests
from datetime import datetime, timedelta, timezone


YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def search_shorts(query, max_results=10):
    published_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }
    
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    
    video_ids = []
    for item in data.get("items", []):
        if "videoId" in item.get("id", {}):
            video_ids.append(item["id"]["videoId"])
    
    if not video_ids:
        return []
    
    # Buscar estatísticas (views)
    url_stats = "https://www.googleapis.com/youtube/v3/videos"
    params_stats = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }
    
    r2 = requests.get(url_stats, params=params_stats, timeout=30)
    r2.raise_for_status()
    stats_data = r2.json()
    
    videos = []
    for item in stats_data.get("items", []):
        views = int(item["statistics"].get("viewCount", 0))
        title = item["snippet"]["title"]
        video_id = item["id"]
        channel = item["snippet"]["channelTitle"]
        
        videos.append({
            "title": title,
            "views": views,
            "link": f"https://youtube.com/shorts/{video_id}",
            "channel": channel
        })
    
    return videos


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def main():
    print("Buscando shorts...")
    
    # Buscas focadas em esportes e tecnologia
    queries = [
        "sports highlights shorts",
        "football soccer nba highlights",
        "technology gadgets AI shorts",
        "tech news smartphone AI"
    ]
    
    all_videos = []
    for q in queries:
        try:
            found = search_shorts(q, max_results=8)
            all_videos.extend(found)
            print(f"Query '{q}': {len(found)} vídeos")
        except Exception as e:
            print(f"Erro na query {q}: {e}")
    
    # Remover duplicados
    unique = {}
    for v in all_videos:
        unique[v["link"]] = v
    
    # Ordenar por views e pegar top 3
    top3 = sorted(unique.values(), key=lambda x: x["views"], reverse=True)[:3]
    
    if not top3:
        send_telegram("Não encontrei shorts virais hoje. Tente novamente amanhã.")
        return
    
    hoje = datetime.now().strftime("%d/%m/%Y")
    mensagem = f"🔥 Top 3 Shorts Virais — Esportes & Tecnologia\n📅 {hoje}\n\n"
    
    for i, v in enumerate(top3, 1):
        views_formatado = f"{v['views']:,}".replace(",", ".")
        mensagem += f"{i}. {v['title']}\n"
        mensagem += f"   👀 {views_formatado} views | {v['channel']}\n"
        mensagem += f"   🔗 {v['link']}\n\n"
    
    mensagem += "Boa postagem no perfil! 🚀"
    
    send_telegram(mensagem)
    print("Mensagem enviada com sucesso!")


if __name__ == "__main__":
    main()
