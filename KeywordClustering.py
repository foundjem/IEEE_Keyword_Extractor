import os
import json
import glob

class Helper:

    @staticmethod
    def load_results_from_json(results, filename):
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
    def count_keywords(keyword_dict):
        kws = {}
        for (_,key) in keyword_dict.iteritems():
            Helper.add_to_list(kws, key.kw_inspec)
            Helper.add_to_list(kws, key.kw_inspec_unc)
            Helper.add_to_list(kws, key.kw_authors)
            Helper.add_to_list(kws, key.kw_ieee)
        return kws

    @staticmethod
    def sorted_keywords(keywords):
        return sorted(keywords.items(), key=lambda keyword: keyword[1], reverse=True)

    @staticmethod
    def add_to_list(dict, kw_list):
        for keyword in kw_list:
            if not keyword in dict:
                dict[keyword] = 1
            else:
                dict[keyword] += 1

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

# start main script

# load keywords from files
keywords = {}
for f in glob.glob('/Users/philipp/Dropbox/paperService/*_results.json'):
    Helper.load_results_from_json(keywords, f)

# do stemming and decapitalization
# TODO

# count keywords
counts = Helper.count_keywords(keywords)
counts = Helper.sorted_keywords(counts)
print (counts)
