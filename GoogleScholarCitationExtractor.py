import json
import time

from scholar import *

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

if not len(sys.argv) == 3:
    print "Usage: ./GoogleScholarCitationExtractor.py <SOURCE_JSON> <TARGET_JSON>"
    sys.exit(1)

source_file = sys.argv[1]
target_file = sys.argv[2]

# load the article titles from the ICWS JSON in the Dropbox folder
articles = Helper.load_article_names_from_json(source_file)
total_articles = len(articles)

# load what we already scraped in a previous session
previous_results = Helper.load_results_from_json(target_file)

# copy over all results from our previous result set
citations = previous_results

querier = ScholarQuerier()
settings = ScholarSettings()
settings.set_citation_format(settings.CITFORM_BIBTEX)
querier.apply_settings(settings)
query = SearchScholarQuery()

cur_article = 0
for article in articles:

    cur_article += 1

    # skip if we already scraped this article in a previous run
    if article in citations:
        print "Skipping %s" % article
        continue

    # sleep a few secs to not unduly annoy GS
    time.sleep(3)

    query.set_phrase(article)
    querier.send_query(query)
    if len(querier.articles) == 0:
        print "Could not find article %s" % article
        continue
    elif len(querier.articles) > 1:
        print "Found multiple articles for %s, using %s" % (article, querier.articles[0]['title'])
    print "(%d/%d) %s: %s" % (cur_article, total_articles, article, querier.articles[0]["num_citations"])
    citation = Citation(article, querier.articles[0]["num_citations"])
    citations[article] = citation
    Helper.save_results_to_json(target_file, citations)