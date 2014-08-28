import re
import difflib
import pandas as pd
import numpy as np

from nameparser import HumanName
from nameparser.config import CONSTANTS
CONSTANTS.titles.remove("gen")
CONSTANTS.titles.remove("prin")


def parse_paper_type(section_name):
    section_name = section_name.strip().lower()
    if section_name == '':
        paper_type = None
    elif re.match('.*workshop.*', section_name):
        paper_type = 'workshop'
    elif re.match('.*symposi.*', section_name):
        paper_type = 'symposium'
    elif re.match('.*poster.*', section_name):
        paper_type = 'poster'
    elif re.match('.*tutorial.*', section_name):
        paper_type = 'workshop'
    elif re.match('.*abstract.*', section_name):
        paper_type = 'poster'
    elif re.match('.*addenda.*', section_name):
        paper_type = 'other'
    else:
        paper_type = 'talk'

    return paper_type


def clean_authors(authors):
    cleaned_authors = []
    authors = authors.lower()

    # get rid of commas where there are suffixes, like Jr. or III
    authors = authors.replace(", jr.", " jr.")
    authors = authors.replace(", iii", " iii")
    authors = authors.replace(", ph.d", "")

    # special cases
    authors = authors.replace("organizer:", "")
    authors = authors.replace("roel m,", "roel m.")
    if authors == 'kozue miyashiro, etsuko harada, t.':
        author_list = ['kozue miyashiro', 'etsuko harada, t.']
    else:
        author_list = authors.split(",")

    for author in author_list:
        author = HumanName(author.lower())

        if author.first == '' or author.last == '':
            raise ValueError("invalid author name: {}".format(author))

        author.capitalize()
        author.string_format = u"{last}, {title} {first} {middle}, {suffix}"

        cleaned_authors.append(unicode(author))

    return cleaned_authors


def extract_authors(papers):
    author_papers = []
    for i, paper in papers.iterrows():
        authors = clean_authors(paper['authors'])
        for author in authors:
            entry = paper.copy().drop('authors')
            entry['author'] = author
            author_papers.append(entry)
    author_papers = pd.DataFrame(author_papers)
    return author_papers


def fix_author_misspellings(papers, G):
    authors = np.sort(papers['author'].unique())
    for i in xrange(len(authors)):
        window = 20
        lower = i + 1
        upper = min(i + 1 + window, len(authors) - 1)
        for j in xrange(len(authors[lower:upper])):
            author1 = authors[i]
            author2 = authors[lower + j]
            if author1 == author2:
                continue

            author1_hn = HumanName(author1)
            author2_hn = HumanName(author2)
            same_first = author1_hn.first == author2_hn.first
            same_last = author1_hn.last == author2_hn.last

            if same_first and same_last:
                replace = True
            else:
                ratio = difflib.SequenceMatcher(None, author1, author2).ratio()
                if ratio > 0.9:
                    coauthors = set(G[author1].keys()) & set(G[author2].keys())
                    if len(coauthors) > 0:
                        replace = True
                    else:
                        print u"\nPossible match: '{}' vs '{}' (r={})".format(
                            author1, author2, ratio)
                        print sorted(G[author1].keys())
                        print sorted(G[author2].keys())
                        accept = ""
                        while accept not in ("y", "n"):
                            accept = raw_input("Accept? (y/n) ")
                        replace = accept == "y"
                else:
                    replace = False

            if replace:
                num1 = len(papers.groupby('author').get_group(author1))
                num2 = len(papers.groupby('author').get_group(author2))
                if num1 > num2:
                    oldname = author2
                    newname = author1
                else:
                    oldname = author1
                    newname = author2

                print u"Replacing '{}' with '{}'".format(oldname, newname)
                papers.loc[papers['author'] == oldname, 'author'] = newname
                authors[authors == oldname] = newname
                for neighbor in G[oldname]:
                    if neighbor not in G[newname]:
                        G.add_edge(newname, neighbor)
                        G[newname][neighbor]['weight'] = 0
                    weight = G[oldname][neighbor]['weight']
                    G[newname][neighbor]['weight'] += weight
                G.remove_node(oldname)

    return papers, G


if __name__ == "__main__":
    import graph
    papers = pd.read_csv("cogsci_proceedings_raw.csv")
    papers['type'] = papers['section'].apply(parse_paper_type)
    papers = extract_authors(papers)
    G = graph.make_author_graph(papers)
    papers, G = fix_author_misspellings(papers, G)
    papers.to_csv("cogsci_proceedings.csv", encoding='utf-8')
