import os
import tempfile
import zipfile

from bs4 import BeautifulSoup


class HTMLParser:
    def __init__(self, filename=None, html=None):
        self.filename = filename
        self.html = html
        self.link_tags = {
            'a': 'href',
            'audio': 'src',
            'img': 'src',
            'link': 'href',
            'script': 'src'
        }

    def get_links(self):
        basename = None
        if self.html is None:
            basename = os.path.basename(self.filename)
            self.html = open(self.filename).read()
        soup = BeautifulSoup(self.html, 'html.parser')

        extracted_links = []
        for tag_name in self.link_tags:
            tags = soup.find_all(tag_name)
            for tag in tags:
                link = tag.get(self.link_tags[tag_name])
                # don't include links to ourselves or # links
                # TODO: Should this part be moved to get_local_files instead?
                if (basename and not link.startswith(basename)) and not link.strip().startswith("#"):
                    if '?' in link:
                        link, query = link.split('?')
                    if '#' in link:
                        link, marker = link.split('#')
                    extracted_links.append(link)

        return extracted_links

    def get_local_files(self):
        links = self.get_links()
        local_links = []
        for link in links:
            # NOTE: This technically fails to handle file:// URLs, but we're highly unlikely to see
            # file:// URLs in any distributed package, so this is simpler than parsing out the protocol.
            if not '://' in link:
                local_links.append(link)

        return local_links

    def replace_links(self, links_to_replace):
        if self.html is None:
            basename = os.path.basename(self.filename)
            self.html = open(self.filename).read()
        soup = BeautifulSoup(self.html, 'html.parser')

        extracted_links = []
        for tag_name in self.link_tags:
            tags = soup.find_all(tag_name)
            print("tag_name = {}, tags = {}".format(tag_name, tags))
            for tag in tags:
                link = tag.get(self.link_tags[tag_name])
                if link in links_to_replace:
                    tag[self.link_tags[tag_name]] = links_to_replace[link]

        return soup.prettify()