import os
import json
import requests
import time
from typing import List
import torch
from google.cloud import storage
from scoring import process_transcript
from google.cloud import datastore 
import pandas as pd

#Google Project Configuration
PROJECT_ID = "sentiment-analysis-379200"
BUCKET_NAME = 'news_40999'
storage_client = storage.Client(project=PROJECT_ID)
datastore_client = datastore.Client(project=PROJECT_ID)

#API Ninjas Authentication
def get_authenticated(url):
    headers = {'X-Api-Key': os.getenv('APININJAS_API_KEY')}
    return requests.get(url, headers=headers)

#fetch Earnings Call Transcripts
def earnings_calls(tickers: List[str], year: int, quarter: int):
    transcripts = {}
    
    for ticker in tickers:
        source = get_authenticated(f"https://api.api-ninjas.com/v1/earningstranscript?ticker={ticker}&year={year}&quarter={quarter}")
        if source.status_code != 200:
            print(f"Error for {ticker}: {source.status_code} - {source.text}")
            continue
        
        try:
            resObj = json.loads(source.text)
            paragraphs = resObj['transcript'].split('\n')
            transcripts[ticker] = paragraphs
        except:
            print(f"Failed to decode JSON response for {ticker}, {year}Q{quarter}")
    
    return transcripts

#upload JSON File to Google Cloud Bucket
def upload_to_bucket(content, blob_name):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(content), content_type='application/json')
    print(f"Uploaded: {blob_name}")


def collect_technology_keywords():
    client = datastore.Client()
    
    output = []
    query = client.query(kind='AI_Keywords')
    for entity in query.fetch():
        output.append({"Keyword": entity["Keyword"], "Category": entity["Category"]})

    return output


#store both keyword paragraphs & full transcript
def store_to_bucket(ticker, year, quarter, paragraphs):
    call_date = f"{year} Q{quarter}"
    
    #extract only keyword values as a list of strings
    keywords_data = collect_technology_keywords()
    keywords = [entry["Keyword"] for entry in keywords_data]

    #remove duplicates
    keywords = list(set(keywords))

    #Debugging: Print cleaned keywords
    print("\n=== Debugging Unique Technology Keywords ===")
    print(keywords)

    #convert paragraphs list to a Pandas DataFrame
    transcript_df = pd.DataFrame(paragraphs, columns=["Transcript"])  

    #process_transcript()
    processed_df = process_transcript(
        transcript_df,  
        pd.DataFrame({"Keyword": keywords, "Category": ["Technology"] * len(keywords)})
    )

    #store each keyword-matching paragraph separately
    if processed_df.empty:
        print(f"No keyword-matching paragraphs found for {ticker}. Skipping paragraph storage.")
    else:
        for index, row in processed_df.iterrows():
            paragraph_data = {
                "call_date": call_date,
                "category": row["Category"],
                "keyword": row['Keyword'],
                "paragraph": row['Paragraph'],
                "document_type": "Conference Call",
                "ticker": ticker,
                "year": year,
                "quarter": quarter,
                "sentiment_score": row['Sentiment Score'],
                "sentiment_magnitude": row['Sentiment Magnitude']
            }

            #store each paragraph in its own file
            paragraph_file_name = f"Paragraph_{ticker}_{year}Q{quarter}_{index}.json"
            upload_to_bucket(paragraph_data, paragraph_file_name)

    #average sentiment
    avg_score = processed_df["Sentiment Score"].mean() if not processed_df.empty else None
    avg_magnitude = processed_df["Sentiment Magnitude"].mean() if not processed_df.empty else None

    summary = {
        "call_date": call_date,
        "document_type": "Conference Call",
        "ticker": ticker,
        "year": year,
        "quarter": quarter,
        "average_sentiment_score": avg_score,
        "average_sentiment_magnitude": avg_magnitude,
    }

    #upload full summary for transcript
    summary_file_name = f"Summary_{ticker}_{year}Q{quarter}.json"
    upload_to_bucket(summary, summary_file_name)

    #full transcript separately
    full_transcript_data = {
        "ticker": ticker,
        "year": year,
        "quarter": quarter,
        "call_date": call_date,
        "full_transcript": paragraphs
    }
    full_file_name = f"Transcript_{ticker}_{year}Q{quarter}.json"
    upload_to_bucket(full_transcript_data, full_file_name)
    
    print(f"Processed and uploaded {ticker}")


#run for multiple tickers
def run():
    tickers = ["ORCL","GOOGL", "META", "MSFT", "AMZN", "NOW", "CRM", "ADBE", "APP", "PLTR", "INTU", "ACN", "TRI"]
    year = 2024
    quarter = 2

    transcripts = earnings_calls(tickers, year, quarter)
    
    if not transcripts:
        print("No earnings call data available")
        return

    for ticker, paragraphs in transcripts.items():
        if paragraphs:
            store_to_bucket(ticker, year, quarter, paragraphs)
        else:
            print(f"No transcript available for {ticker}")

if __name__ == "__main__":
    run()
