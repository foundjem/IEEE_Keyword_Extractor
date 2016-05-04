from lxml import html
import requests
import urllib
import re
import json
import os
import sys


class Helper:
    @staticmethod
    def load_article_names_from_json(filename):
        with open(filename) as file:
            json_file = json.loads(file.read())
        articles = []
        for hit in json_file["result"]["hits"]["hit"]:
            if hit["info"]["type"] == "proceedings":
                continue
            article = hit["info"]["title"] #["text"]
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
            the_result = Keywords(result['article'], result['kw_inspec'], result['kw_inspec_unc'], result['kw_authors'], result['kw_ieee'])
            results[the_result.article.encode('ascii','ignore')] = the_result
        return results


    @staticmethod
    def get_keywords(list):
        keywords = []
        for keyword_el in list.xpath("li/a"):
            keywords.append(keyword_el.get("data-keyword"))
        return keywords

class Keywords:

    def __init__(self, article, inspec, inspec_unc, authors, ieee):
        self.article = article
        self.kw_inspec = inspec
        self.kw_inspec_unc = inspec_unc
        self.kw_authors = authors
        self.kw_ieee = ieee

    def to_json(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4)

    def __str__(self):
        str = "Article: %s\n" % self.article
        str += "-----------------------\n"
        str += "# INSPEC Controlled Terms\n"
        for keyword in self.kw_inspec:
            str += keyword+"\n"
        str += "# INSPEC Uncontrolled Terms\n"
        for keyword in self.kw_inspec_unc:
            str += keyword+"\n"
        str += "# Author Terms\n"
        for keyword in self.kw_authors:
            str += keyword+"\n"
        str += "# IEEE Terms\n"
        for keyword in self.kw_ieee:
            str += keyword+"\n"
        str = str.encode('ascii','ignore')
        return str

#
# start script content
#

if not len(sys.argv) == 3:
    print "Usage: ./IEEEKeywordExtractor.py <SOURCE_JSON> <TARGET_JSON>"
    sys.exit(1)

source_file = sys.argv[1]
target_file = sys.argv[2]

# load the article titles from the ICWS JSON in the Dropbox folder
articles = Helper.load_article_names_from_json(source_file)

# load what we already scraped in a previous session
previous_results = Helper.load_results_from_json(target_file)

# copy over all results from our previous result set
keywords = previous_results

for article in articles:

    # skip if we already scraped this article in a previous run
    if article in keywords:
        print "Skipping %s" % article
        continue

    # first we need to look up the "arnumber"
    # we can do this with a call to the REST backend that IEEEXplorer is using internally
    headers = {
        'Content-Type': 'application/json',
    }
    post_json = {'queryText' : article}
    with requests.session() as session:
        response_json = session.post("http://ieeexplore.ieee.org:80/rest/search?reload=true", json=post_json, headers=headers).content

    # let's not even bother parsing - just grep through this with a simple regex looking for "articleNumber":"XXX"
    m = re.search('\\"articleNumber\\":\\"(\d*)\\"', response_json)
    # some articles have weird characters in their name and we don't find them - just ignore for now
    if not m:
        continue
    arnumber = m.group(1)

    # now that we know the arnumber we can get the page that has the actual keywords
    url_pattern = "http://ieeexplore.ieee.org/xpl/abstractKeywords.jsp?arnumber=%s&newsearch=true&queryText=%s"
    url = url_pattern % (arnumber, urllib.quote(article))
    with requests.session() as session:
        page = session.get(url)
    content = page.content
    tree = html.fromstring(content)

    # with open("tmp.html", "w") as file:
    #     file.write(content)

    # IEEEXplorer uses Coldfusion, whose HTML not even a mother could love :( let's see if we can make some sense of it

    # there seem to be about 4 types of keywords, and not all papers have all of them
    # what kind of keywords they are can only be seen in the <h2> title directly before them

    # (1) INSPEC: CONTROLLED INDEXING
    inspec_controlled_header =\
        tree.xpath('//div[@class = "article-blk"]/div[@class = "art-keywords col-2-305 cf"]/div/div/h2[text() = "INSPEC: CONTROLLED INDEXING"]')
    if(inspec_controlled_header.__len__() > 0):
        inspec_controlled = Helper.get_keywords(inspec_controlled_header[0].xpath("./following-sibling::ul")[0])
    else:
        inspec_controlled = []

    # (2) INSPEC: NON CONTROLLED INDEXING
    inspec_noncontrolled_header =\
        tree.xpath('//div[@class = "article-blk"]/div[@class = "art-keywords col-2-305 cf"]/div/div/h2[text() = "INSPEC: NON CONTROLLED INDEXING"]')
    if(inspec_noncontrolled_header.__len__() > 0):
        inspec_noncontrolled = Helper.get_keywords(inspec_noncontrolled_header[0].xpath("./following-sibling::ul")[0])
    else:
        inspec_noncontrolled = []

    # (3) AUTHOR KEYWORDS
    author_header =\
        tree.xpath('//div[@class = "article-blk"]/div[@class = "art-keywords col-2-305 cf"]/div/div/h2[text() = "AUTHOR KEYWORDS"]')
    if(author_header.__len__() > 0):
        author = Helper.get_keywords(author_header[0].xpath("./following-sibling::ul")[0])
    else:
        author = []

    # (4) IEEE TERMS
    ieee_header =\
        tree.xpath('//div[@class = "article-blk"]/div[@class = "art-keywords col-2-305 cf"]/div/div/h2[text() = "IEEE TERMS"]')
    if(ieee_header.__len__() > 0):
        ieee = Helper.get_keywords(ieee_header[0].xpath("./following-sibling::ul")[0])
    else:
        ieee = []

    # add to result list
    keywords[article] = Keywords(article, inspec_controlled, inspec_noncontrolled, author, ieee)
    print keywords[article]

    # write updated result list (we are doing this in every iteration so that we can observe the progress)
    Helper.save_results_to_json(target_file, keywords)
