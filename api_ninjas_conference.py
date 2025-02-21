import os
import json
import requests
import time
from typing import List
import torch
from google.cloud import storage
from scoring import analyze_sentiment
from keywordcollector import collectKeywords

#setup
PROJECT_ID = "sentiment-analysis-379200"
BUCKET_NAME = 'news_40999'
storage_client = storage.Client(project=PROJECT_ID)

#api ninjas function
def get_authenticated(url):
    headers = {'X-Api-Key': os.getenv('APININJAS_API_KEY')}
    return requests.get(url, headers=headers)

#pull conference call from API ninjas
def earnings_calls(ticker: str, year: int, quarter: int) -> List[str]:
    source = get_authenticated(f"https://api.api-ninjas.com/v1/earningstranscript?ticker={ticker}&year={year}&quarter={quarter}")
    if source.status_code != 200:
        print("Error:", source.status_code, source.text)
        return []
    
    try:
        resObj = json.loads(source.text)
        paragraphs = resObj['transcript'].split('\n')
    except:
        print("Failed to decode JSON response.", ticker, f"{year}Q{quarter}")
        return []
    return paragraphs

#upload json file to bucket
def upload_to_bucket(content, blob_name):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(content), content_type='application/json')
    print(f"Uploaded: {blob_name}")

#finds keywords in paragraphs and scores them
def store_to_bucket(ticker, year, quarter, paragraphs):
    keywords = collectKeywords('keywords')  #fetches keywords from the keyword table in datastore
    
    processed_data = []
    for i, para in enumerate(paragraphs):
        sentiment_raw = analyze_sentiment(para) #uses the analyze_sentiment function from scoring.py

        #convert sentiment tensor to a dictionary of floats
        #fixed error being casued by 3 tensor elements not being allowed to store at the same time
        if isinstance(sentiment_raw, torch.Tensor):
            sentiment = { #analyze_sentiment returns 3 values
                "positive": float(sentiment_raw[0].item()),
                "negative": float(sentiment_raw[1].item()),
                "neutral": float(sentiment_raw[2].item())
            }
        else:
            sentiment = sentiment_raw

        matched_keywords = [kw["Keyword"] for kw in keywords if kw["Keyword"] in para]

        processed_data.append({ #after each paragraph will show this information
            "ticker": ticker,
            "year": year,
            "quarter": quarter,
            "paragraph": para,
            "sentiment": sentiment,
            "keywords": matched_keywords
        })
    
    #upload full JSON file to bucket
    file_name = f"Conference_Call{ticker}_{year}Q{quarter}.json"
    upload_to_bucket(processed_data, file_name)

def run():
    ticker = "C" #company ticker
    year = 2024
    quarter = 2
    paragraphs = earnings_calls(ticker, year, quarter)
    if paragraphs:
        store_to_bucket(ticker, year, quarter, paragraphs)
    else:
        print("No earnings call data available.")

if __name__ == "__main__":
    run()