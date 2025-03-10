# Conference-Call-Sentiment

Contains an introductory attempt of pulling one conference call using API ninjas and scoring it using the scoring.py and keywordcolloctor.py found in the UConn sentiment backend.
Code stores call as text within a JSON file along with the sentiment score and found keywords after each paragraph, sample output can be found below.

Still need to: 
-Verify accuracy of sentiment scores and proper use of sentiment model.
-Organize in a way such that all infomration isnt contained within the same JSON file.

Sample Output: "with the progress that we're making towards our 2024 and medium-term targets and remain committed to these targets. With that, Jane and I will be happy to take your questions.", "sentiment": {"positive": 0.38949939608573914, "negative": 0.5219312906265259, "neutral": 0.08856929838657379}, "keywords": ["IPO", "Revenue"]}, {"ticker": "C", "year": 2024, "quarter": 2, "paragraph": "Operator: At this time, we will open the floor for questions."

export APININJAS_API_KEY="api_key" in terminal



3/10/2025
ssga_ai_paragraphs.py handles only AI related keywords in the technology category while using process_transcript() from scoring.py
TODO: clean up and organize bucket, a lot of junk submissions while trying to debug code.

example output:

Summary_META_2024Q2.json:

{"call_date": "2024 Q2", "document_type": "Conference Call", "ticker": "META", "year": 2024, "quarter": 2, "average_sentiment_score": 0.4844968058168888, "average_sentiment_magnitude": 2.977875}

Paragraph_META_2024Q2.json: 

{"call_date": "2024 Q2", "category": "Technology", "keyword": "ai agent", "paragraph": "mark zuckerberg : all right, thanks ken. and hey everyone, thanks for joining today. this was a strong quarter for our community and business. we estimate that there are now more than 3.2 billion people using at least one of our apps each day. the growth we're seeing here in the us has especially been a bright spot. whatsapp now serves more than 100 million monthly actives in the us, and we're seeing good year-over-year growth across facebook, instagram, and threads as well, both in the us, and globally. i'm particularly pleased with the progress that we're making with young adults on facebook. the numbers we are seeing, especially in the us, really go against the public narrative around who's using the app. a couple of years ago, we started focusing our apps more on 18 to 29 year olds and it's good to see that those efforts are driving good results. another bright spot is threads which is about to hit 200 million monthly actives. we're making steady progress towards building what looks like it's going to be ", "document_type": "Conference Call", "ticker": "META", "year": 2024, "quarter": 2, "sentiment_score": 0.874605655670166, "sentiment_magnitude": 5.5959}

