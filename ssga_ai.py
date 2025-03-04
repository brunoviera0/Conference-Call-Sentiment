import os
import json
import requests
import time
from typing import List
import torch
from google.cloud import storage
from scoring import process_chunk  #using correct sentiment processing
from keywordcollector import collectKeywords
from google.cloud import datastore 

#google project
PROJECT_ID = "sentiment-analysis-379200"
BUCKET_NAME = 'news_40999'
storage_client = storage.Client(project=PROJECT_ID)
datastore_client = datastore.Client(project=PROJECT_ID)

#API Ninjas key function
def get_authenticated(url):
    headers = {'X-Api-Key': os.getenv('APININJAS_API_KEY')}
    return requests.get(url, headers=headers)

#API Ninjas for multiple tickers
def earnings_calls(tickers: List[str], year: int, quarter: int):
    transcripts = {}  #dictionary to store transcripts per ticker
    
    for ticker in tickers: #added for loop to cycle through multiple tickers
        source = get_authenticated(f"https://api.api-ninjas.com/v1/earningstranscript?ticker={ticker}&year={year}&quarter={quarter}")
        if source.status_code != 200:
            print(f"Error for {ticker}: {source.status_code} - {source.text}")
            continue  # Skip this ticker if no data available
        
        try:
            resObj = json.loads(source.text)
            paragraphs = resObj['transcript'].split('\n')
            transcripts[ticker] = paragraphs  #store each transcript under the coresponding ticker symbol
        except:
            print(f"Failed to decode JSON response for {ticker}, {year}Q{quarter}")
    
    return transcripts  #returns the dictionary: { "TICKER": [Paragraphs] }

#upload JSON file to bucket
def upload_to_bucket(content, blob_name):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(content), content_type='application/json')
    print(f"Uploaded: {blob_name}")

#add new AI keywords to a new datastore table
def store_ai_keywords():
    ai_keywords = ["AI Agent", "LLM", "Model Training", "AI Inference", "AI Monetization", "AI software functionality"]

    for keyword in ai_keywords:
        key = datastore_client.key("AI_Keywords")  #create a new entity in AI_Keywords
        entity = datastore.Entity(key)
        entity.update({"Keyword": keyword, "Category": "AI"})
        datastore_client.put(entity)  #save to Datastore

    print("AI Keywords stored.")

#collect keywords from two sources (original datastore table and new AI category)
def collect_all_keywords():
    existing_keywords = collectKeywords('keywords')  #Existing keywords
    query = datastore_client.query(kind="AI_Keywords")  #AI-specific keywords
    ai_keywords = list(query.fetch())

    #convert AI keywords to the same format as existing keywords
    ai_keywords_formatted = [{"Keyword": k["Keyword"], "Category": "AI"} for k in ai_keywords]
    
    return existing_keywords + ai_keywords_formatted  #combine both sets of keywords

#finds keywords in paragraphs and scores them
def store_to_bucket(ticker, year, quarter, paragraphs):
    keywords = collect_all_keywords()
    
    processed_data = []
    for i, para in enumerate(paragraphs):
        sentiment_score, sentiment_magnitude = process_chunk(para) #use process_chunk instead of analyze_sentiment

        matched_keywords = [kw["Keyword"] for kw in keywords if kw["Keyword"] in para]

        processed_data.append({  #store results per paragraph
            "ticker": ticker,
            "year": year,
            "quarter": quarter,
            "paragraph": para,
            "sentiment_score": sentiment_score.item(),  #convert tensor to number
            "sentiment_magnitude": sentiment_magnitude,  
            "keywords": matched_keywords
        })
    
    #upload full JSON file to bucket
    file_name = f"Conference_Call_{ticker}_{year}Q{quarter}.json"
    upload_to_bucket(processed_data, file_name)

#run for multiple tickers
def run():
    tickers = ["ORCL","GOOGL", "META", "MSFT", "AMZN", "NOW", "CRM", "ADBE", "APP", "PLTR", "INTU", "ACN", "TRI"]  #stock tickers from email
    year = 2024 #need to automate for given year and quarter
    quarter = 2

    transcripts = earnings_calls(tickers, year, quarter)
    
    if not transcripts:
        print("No earnings call data available")
        return

    #process each ticker's transcript separately
    for ticker, paragraphs in transcripts.items():
        if paragraphs:
            store_to_bucket(ticker, year, quarter, paragraphs)
        else:
            print(f"No transcript available for {ticker}")

if __name__ == "__main__":
    store_ai_keywords()
    run()
