import re

from bs4 import BeautifulSoup
import html2text
import requests


HOME_URL = 'https://covid19.rpi.edu'


def construct_url(path):
    return HOME_URL + path


def collect_communications_paths():
    paths = []
    soup = create_soup('/communications')
    for link in soup.findAll('a', attrs={'href': re.compile('announcements')}):
        paths.append(link.get('href'))
    return paths


def filter_paths(paths):
    with open('.cache_sample', 'r') as f:
        cache_paths = f.readlines()
    already_processed_paths = [path.rstrip('\n') for path in cache_paths]
    return [path for path in paths if path not in already_processed_paths]


def update_cache(paths):
    with open('.cache_sample', 'a') as f:
        lines = [path + '\n' for path in paths]
        f.writelines(lines)


def create_soup(path):
    url = construct_url(path)
    html = requests.get(url).text
    soup = BeautifulSoup(html, features='lxml')
    return soup


def get_author_from_bs_tag(bs_tag):
    author = bs_tag.find('div', attrs={'class': 'field__item'}).contents[0]
    return author


def get_post_content_from_bs_tag(bs_tag):
    post_content = html2text.html2text(str(bs_tag))
    return post_content


def get_date_from_bs_tag(bs_tag):
    date_pattern = '[A-Za-z]+ [0-9]+, [0-9]+'
    span_content = bs_tag.find('span').contents[0]
    date = re.search(date_pattern, span_content).group()
    return date


def get_post_author_date_and_content(bs_tags):
    property_getters = {'author': get_author_from_bs_tag,
                        'date': get_date_from_bs_tag,
                        'content': get_post_content_from_bs_tag}
    results = {}
    for property_, property_getter in property_getters.items():
        bs_tag = bs_tags[property_]
        try:
            results[property_] = property_getter(bs_tag)
        except Exception:
            results[property_] = None
    return {name: value for name, value in results.items() if value}


def collect_beautifulsoup_tags(path):
    beautifulsoup_tags = {}
    div_attributes = {'author': {'class': 'field--name-field-from'},
                      'content': {'property': 'schema:text'},
                      'date': {'class': 'node__meta'}}
    soup = create_soup(path)
    for post_property, attrs in div_attributes.items():
        beautifulsoup_tags[post_property] = soup.find('div', attrs=attrs)
    return beautifulsoup_tags


if __name__ == '__main__':

    all_paths = collect_communications_paths()
    new_paths = filter_paths(all_paths)

    for path in new_paths:
        bs_tags = collect_beautifulsoup_tags(path)
        announcement_data = get_post_author_date_and_content(bs_tags)

    # update_cache(new_paths)
