import glob
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
            if 'title' in hit["info"] and type(hit["info"]["title"]) is dict:
                article = hit["info"]["title"]["text"]
            else:
                article = hit["info"]["title"]
            article = article.replace(". ", "")
            article = article .encode('ascii','ignore')
            articles.append(article)
        return articles

    @staticmethod
    def load_article_names_from_result(filename):
        results = {}
        if not os.path.exists(filename):
            return results

        with open(filename) as file:
            json_file = json.loads(file.read())
            article_names = []
            for art in json_file['articles']:
                if 'article' in art:
                    article_names.append(art['article'])
            return article_names

# if not len(sys.argv) == 2:
#     print "Usage: ./Find_Missing_Articles.py <DIR>"
#     sys.exit(1)
#
# dir = sys.argv[1]
dir = '/Users/philipp/Dropbox/paperService'

for filename in glob.iglob(dir+'/*.json'):
    if 'scopuscits' in filename or 'keywords' in filename or 'results' in filename:
        continue
    result_file = filename.replace(".json", "") + "_scopuscits.json"
    all_articles = Helper.load_article_names_from_json(filename)
    found_articles = Helper.load_article_names_from_result(result_file)

    print "###### Missing articles for %s:" % filename

    for article in all_articles:
        if not article in found_articles:
            print article