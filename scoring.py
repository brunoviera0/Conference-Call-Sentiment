import sys
import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from sklearn.preprocessing import MinMaxScaler

# Required nltk files, only downloaded on first use
nltk.download('vader_lexicon')
nltk.download('punkt')

model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finBERT')
tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finBERT')
sia = SentimentIntensityAnalyzer()

def score_csv(scoring_location, keywords_location, output_location):
    keywords_df = pd.read_csv(keywords_location)

    if not os.path.exists(output_location):
        os.makedirs(output_location)

    for input_file_name in os.listdir(scoring_location):
        with open(scoring_location + '/' + input_file_name, encoding="utf-8") as f:
            input_df = pd.DataFrame([l.strip('\n') for l in f.readlines()])

        datelist = input_file_name.split('.')[0].split('_')

        year, month = datelist[0], datelist[1]

        quarter = str(get_quarter(int(month)))

        processed_df = process_transcript(input_df[input_df.columns[0]], keywords_df)

        try:
            output_df = calculate_weighted_sentiment(processed_df, keywords_df)
        except ValueError:
            output_df = processed_df

        output_name = "Q" + quarter + year + ".csv"

        output_df.to_csv(output_location + '/' + output_name, index=False)

def calculate_weighted_sentiment(sentiment_df, keywords_df):
    '''
    Args:
        sentiment_filename: Name of Excel file with sentiment results for a transcript.
                            Columns such as: 'Sentiment Score', 'Keyword', 'Paragraph' 

        keywords_filename:  Name of Excel file with keywords and their weights (under 'Proposed').
                            Must contain 'Weights'

    Result:
        Adds (at least) columns 'Proposed' and 'Weighted Sentiment Score' to 'sentiment_filename'.
        'Weighted Sentiment Score' equals the original 'Sentiment Score' multiplied by 'Proposed' 
        weight for relevant 'Keyword', scaled to between 0 and 1.

    Returns:
        None
    '''

    weightMap = {}

    for unused_index, row in keywords_df.iterrows():
        weightMap[row['Keyword']] = row['Weight']

    keywords_df['Weight'] = keywords_df['Keyword'].map(weightMap)

    # Merge the sentiment DataFrame with the keyword weights DataFrame and drop duplicate columns
    sentiment_df = pd.merge(sentiment_df,
                            keywords_df,
                            left_on='Keyword',
                            right_on='Keyword',
                            how='left',
                            suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')
    


    # Calculate the proposed sentiment score using keyword weights
    sentiment_df['Weighted Sentiment Score'] = sentiment_df['Sentiment Score'] * sentiment_df['Weight']

    # Normalize the weighted sentiment score to be between 0 and 1
    scaler = MinMaxScaler()
    sentiment_df['Weighted Sentiment Score'] = scaler.fit_transform(sentiment_df[['Weighted Sentiment Score']])

    # Save the DataFrame with the new column to the same Excel file
    return sentiment_df

def get_quarter(month):
    '''
    Args:
        month: month of the year

    Returns:
        Financial quarter of 'month'
    '''
    if month <= 3:
        return 1
    elif month <= 6:
        return 2
    elif month <= 9:
        return 3
    else:
        return 4

def process_transcript(transcript_df, keywords_df):
    '''
    Args:
        transcript_df:  dataframe of transcript, essentially a list of paragraphs
        keywords_df:    dataframe with headers 'Keyword' and 'Category'

    Returns:
        output_df:  Dataframe with headers: 'Category', 'Keyword', 'Paragraph', 
                                            'Sentiment Score', 'Sentiment Magnitude'
    '''
    output_df = pd.DataFrame(columns=['Category', 'Keyword', 'Paragraph', 'Sentiment Score', 'Sentiment Magnitude'])

    for unused_index, row in keywords_df.iterrows():
        keyword = row['Keyword']
        category = row['Category']

        paragraphs = transcript_df.apply(lambda x: str(x) if keyword.lower() in str(x).lower() else None).dropna()

        # some paragraphs contain multiple keywords and are therefore processed multiple times
        # TODO: avoid redundant processing
        for paragraph in paragraphs:
            chunks = split_text(paragraph, 1024)
            for chunk in chunks:
                sentiment_score, total_magnitude = process_chunk(chunk)
                new_row = { 'Category': category,
                            'Keyword': keyword,
                            'Paragraph': chunk,
                            'Sentiment Score': sentiment_score.item(),
                            'Sentiment Magnitude': total_magnitude}
                output_df = pd.concat([output_df, pd.DataFrame([new_row])], ignore_index=True)

    return output_df

def process_chunk(chunk):
    '''
    Args:
        chunk: string of text, presumably a paragraph

    Returns:
        Tuple of (sentiment_score, total_magnitude)
        sentiment_score: sentiment of 'chunk'
        total_magnitude: magnitude of 'chunk' sentiment
    '''
    probabilities = analyze_sentiment(chunk)
    sentiment_score = (probabilities[1] + (probabilities[2] * 2) + (probabilities[0] * 3)) - 2

    sentences = sent_tokenize(chunk)
    magnitudes = []
    for sentence in sentences:
        sentence_magnitude = abs(sia.polarity_scores(sentence)['compound'])
        magnitudes.append(sentence_magnitude)
    total_magnitude = sum(magnitudes)

    return sentiment_score, total_magnitude

def analyze_sentiment(text):
    '''
    Args:
        text: string of text

    Returns:
        Sentiment of 'text'
        Appears to be a list of [positive, negative, neutral] sentiment values between 0 and 1
    '''
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    outputs = model(**inputs)
    probabilities = softmax(outputs.logits, dim=1)
    return probabilities[0]

def split_text(text, chunk_size):
    '''
    Args:
        text:       string of text
        chunk_size: size of chunks to split 'text' into

    Returns:
        list of 'text' split into strings of length 'chunk_size'
    '''
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

if __name__ == "__main__":
    scoring_input = sys.argv[1]
    keywords_input = sys.argv[2]
    output_input = sys.argv[3]

    score_csv(scoring_input, keywords_input, output_input)
