import pandas as pd
from googleapiclient.discovery import build
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Konfigurasi API
API_KEY = 'AIzaSyCkQBfbW0Xd-TtPtK5UOLu_Cr0TldeuyF8'
VIDEO_ID = 'Z0vsD8J-0_4'

# Fungsi untuk mengambil semua komentar dengan paginasi
def get_all_comments(video_id, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=100,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return comments

# Fungsi untuk analisis sentimen
def analyze_sentiment(comments):
    sentiments = []
    for comment in comments:
        blob = TextBlob(comment)
        polarity = blob.sentiment.polarity
        sentiments.append({'comment': comment, 'sentiment': polarity})
    return pd.DataFrame(sentiments)

# Fungsi untuk mengkategorikan komentar
def categorize_comments(df):
    barca_supporters = df[df['comment'].str.contains('Barca|Barcelona', case=False, na=False)]
    atletico_supporters = df[df['comment'].str.contains('Atletico|Atleti', case=False, na=False)]

    top_positive_barca = barca_supporters.sort_values(by='sentiment', ascending=False).head(5)
    top_positive_atletico = atletico_supporters.sort_values(by='sentiment', ascending=False).head(5)

    return top_positive_barca, top_positive_atletico

# Fungsi untuk menyimpan data ke MongoDB dengan debugging
def load_to_mongodb(df, collection_name):
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['youtubeAPI']
        collection = db[collection_name]

        if df.empty:
            print("DataFrame kosong, tidak ada data yang disimpan ke MongoDB")
        else:
            result = collection.insert_many(df.to_dict('records'))
            print(f"{len(result.inserted_ids)} data berhasil disimpan ke MongoDB")

        collections = db.list_collection_names()
        print(f"Collection yang ada di database: {collections}")

    except Exception as e:
        print(f"Terjadi error saat menyimpan ke MongoDB: {e}")

# Eksekusi
comments = get_all_comments(VIDEO_ID, API_KEY)
sentiment_df = analyze_sentiment(comments)
barca, atletico = categorize_comments(sentiment_df)

# Load ke MongoDB
load_to_mongodb(sentiment_df, 'all_comments')

print(barca.to_string(index=False))
print(atletico.to_string(index=False))

# Visualisasi
plt.figure(figsize=(8, 6))
sns.histplot(sentiment_df['sentiment'], bins=20, kde=True)
plt.title('Distribusi Sentimen Komentar')
plt.xlabel('Sentimen')
plt.ylabel('Frekuensi')
plt.show()

print('Top 5 Positive Comments for Barcelona Supporters:')
print(barca)
print('\nTop 5 Positive Comments for Atletico Supporters:')
print(atletico)
