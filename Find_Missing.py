import json
import os
import sys
import requests
import urllib

class Helper:
    @staticmethod
    def load_article_names_from_json(filename):
        with open(filename) as file:
            json_file = json.loads(file.read())
        articles = []
        for hit in json_file["result"]["hits"]["hit"]:
            if hit["info"]["type"] == "proceedings":
                continue
            article = hit["info"]["title"]["text"]
            article = article.replace(". ", "")
            article = article .encode('ascii','ignore')
            articles.append(article)
        return articles

    @staticmethod
    def load_results_from_json(filename):
        results = []
        if not os.path.exists(filename):
            return results

        with open(filename) as file:
            json_file = json.loads(file.read())
        for result in json_file['articles']:
            if not 'article' in result:
                continue
            results.append(result['article'])
        return results

icws_articles = Helper.load_article_names_from_json('/Users/philipp/Dropbox/paperService/icws.json')
parsed_articles = Helper.load_results_from_json('/Users/philipp/Dropbox/paperService/icws_scopuscits.json')

for article in icws_articles:
    if not article in parsed_articles:
        print article