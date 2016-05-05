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
    def save_results_to_json(filename, results):
        with open(filename, "w") as file:
            file.write('{"articles":[')
            for article in results:
                file.write(results[article].to_json())
                file.write(",")
            file.write("{}]}")

    @staticmethod
    def load_results_from_json(filename):
        results = {}
        if not os.path.exists(filename):
            return results

        with open(filename) as file:
            json_file = json.loads(file.read())
        for result in json_file['articles']:
            if not 'article' in result:
                continue
            the_result = Citation(result['article'], result['citations'])
            results[the_result.article.encode('ascii','ignore')] = the_result
        return results

class Citation:

    def __init__(self, article, citations):
        self.article = article
        self.citations = citations

    def to_json(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4)

#
# start script content
#

# if not len(sys.argv) == 3:
#     print "Usage: ./SCOPUSCitationExtractor.py <SOURCE_JSON> <TARGET_JSON>"
#     sys.exit(1)
#
# source_file = sys.argv[1]
# target_file = sys.argv[2]
source_file = '/Users/philipp/Dropbox/paperService/icws.json'
target_file = 'test.json'

# load the article titles from the ICWS JSON in the Dropbox folder
articles = Helper.load_article_names_from_json(source_file)
total_articles = len(articles)

# load what we already scraped in a previous session
previous_results = Helper.load_results_from_json(target_file)

# copy over all results from our previous result set
citations = previous_results

SCOPUS_SEARCH_URL = "http://api.elsevier.com/content/search/scopus?apiKey=6492f9c867ddf3e84baa10b5971e3e3d&query="

cur_article = 0
for article in articles:

    cur_article += 1

    # skip if we already scraped this article in a previous run
    if article in citations:
        print "Skipping %s" % article
        continue

    url = SCOPUS_SEARCH_URL + urllib.quote("title(\"%s\")" % article)
    r = requests.get(url)
    result = r.json()
    for entry in result['search-results']['entry']:
        if entry['dc:title'] == article:
            print "Article %s has %s citations" % (article, entry['citedby-count'])
        else:
            print "Not the same article - looking for %s, but found %s" % (article, entry['dc:title'])

    # scopus.
    #
    # query.set_phrase(article)
    # querier.send_query(query)
    # if len(querier.articles) == 0:
    #     print "Could not find article %s" % article
    #     continue
    # elif len(querier.articles) > 1:
    #     print "Found multiple articles for %s, using %s" % (article, querier.articles[0]['title'])
    # print "(%d/%d) %s: %s" % (cur_article, total_articles, article, querier.articles[0]["num_citations"])
    # citation = Citation(article, querier.articles[0]["num_citations"])
    # citations[article] = citation
    # Helper.save_results_to_json(target_file, citations)