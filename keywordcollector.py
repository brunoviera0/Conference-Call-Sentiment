from google.cloud import datastore
import csv
import sys

def collectKeywords(keywordlocation: str) -> list:
    client = datastore.Client()
    
    output = []

    query = client.query(namespace='Sentiment_Keywords', kind=keywordlocation)
    for entity in query.fetch():
        output.append({"Keyword": entity["Keyword"], "Category": entity["Category"], "Weight": entity["Weight"]})

    return output

def ouputCSV(keywordDicts: list, outputFile: str):
    with open(outputFile, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keywordDicts[0].keys())

        writer.writeheader()

        writer.writerows(keywordDicts)

if __name__ == "__main__":
    keywordlocations = sys.argv[1]
    outputlocation = sys.argv[2]

    for keywordloc in keywordlocations.split(','):
        kwords = collectKeywords(keywordloc)
        ouputCSV(kwords, outputlocation + keywordloc + ".csv")