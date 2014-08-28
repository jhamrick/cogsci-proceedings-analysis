import urllib2
import pandas as pd
from bs4 import BeautifulSoup, element


def load_html(url):
    response = urllib2.urlopen(url)
    html = response.read().replace("&nbsp;", "")
    return html


def get_papers_table(year):
    url = "https://mindmodeling.org/cogsci{}/".format(year)
    soup = BeautifulSoup(load_html(url))
    tables = soup.find_all("table")
    tds = tables[5].find_all("td")
    tds = [td for td in tds if len(td.contents) > 0]

    paper_type = None

    papers = []
    paper = {}
    for td in tds:
        elem = td.contents[0]
        if isinstance(elem, element.NavigableString):
            paper['authors'] = unicode(elem)
            paper['year'] = year
            paper['section'] = paper_type
            papers.append(paper)
            paper = {}
        elif elem.name == 'a':
            href = url + elem.attrs['href']
            title = "".join(elem.contents)
            paper['url'] = href
            paper['title'] = title
        elif elem.name == 'h2':
            section_name, = elem.contents
            paper_type = section_name.strip()

    return pd.DataFrame(papers)


def get_papers_list(year):
    url = "https://mindmodeling.org/cogsci{}/".format(year)
    html = load_html(url)
    html = html.replace("<li>", "").replace("<li id=session>", "")
    soup = BeautifulSoup(html)

    papers = []
    paper = {}

    paper_type = None

    for elem in soup.findAll("a"):
        if not isinstance(elem.contents[0], element.NavigableString):
            continue
        sibling = elem.findNextSibling()
        if not hasattr(sibling, "name"):
            continue
        if sibling.name != "ul":
            continue

        toplevel = elem.findParent().findParent()
        break

    for section in toplevel.contents:
        if isinstance(section, element.NavigableString):
            paper_type = section.strip()
            continue

        for elem in section.find_all("a"):
            href = url + elem.attrs['href']
            try:
                title = "".join(elem.contents)
            except TypeError:
                continue

            paper = {}
            paper['year'] = year
            paper['url'] = href
            paper['title'] = title
            paper['section'] = paper_type

            sibling = elem.findNextSibling()
            authors, = sibling.contents
            paper['authors'] = unicode(authors)
            papers.append(paper)

    return pd.DataFrame(papers)


def get_papers():
    papers = pd.concat([
        get_papers_table(2014),
        get_papers_list(2013),
        get_papers_list(2012),
        get_papers_list(2011),
        get_papers_list(2010)
    ])

    papers = papers\
        .set_index('url')\
        .sort()

    if papers.isnull().any().any():
        raise RuntimeError("some entries are null")

    return papers


if __name__ == "__main__":
    pathname = "cogsci_proceedings_raw.csv"
    papers = get_papers()
    papers.to_csv(pathname, encoding='utf-8')
