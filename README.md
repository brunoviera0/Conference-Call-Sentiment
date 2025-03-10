# Conference-Call-Sentiment

Contains an introductory attempt of pulling one conference call using API ninjas and scoring it using the scoring.py and keywordcolloctor.py found in the UConn sentiment backend.
Code stores call as text within a JSON file along with the sentiment score and found keywords after each paragraph, sample output can be found below.

Still need to: 
-Verify accuracy of sentiment scores and proper use of sentiment model.
-Organize in a way such that all infomration isnt contained within the same JSON file.

Sample Output: "with the progress that we're making towards our 2024 and medium-term targets and remain committed to these targets. With that, Jane and I will be happy to take your questions.", "sentiment": {"positive": 0.38949939608573914, "negative": 0.5219312906265259, "neutral": 0.08856929838657379}, "keywords": ["IPO", "Revenue"]}, {"ticker": "C", "year": 2024, "quarter": 2, "paragraph": "Operator: At this time, we will open the floor for questions."

export APININJAS_API_KEY="api_key" in terminal
3/10/2025
ssga_ai_paragraphs.py handles only AI related keywords in the technology category.
TODO: clean up and organize bucket, a lot of junk submissions while trying to debug code.

example output:

