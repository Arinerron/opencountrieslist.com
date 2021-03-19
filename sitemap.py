#!/usr/bin/env python3

import xml.etree.cElementTree as ET
import datetime


def generate_sitemap():
    root = ET.Element('urlset')
    root.attrib['xmlns'] = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    root.attrib['xmlns:xhtml'] = 'http://www.w3.org/1999/xhtml'

    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    doc = ET.SubElement(root, 'url')
    ET.SubElement(doc, 'loc').text = 'https://opencountrieslist.com/'
    ET.SubElement(doc, 'lastmod').text = dt
    ET.SubElement(doc, "changefreq").text = 'hourly'
    ET.SubElement(doc, 'priority').text = '1.0'

    with open('web/sitemap.xml', 'wb') as f:
        f.write(ET.tostring(root, encoding='utf-8', xml_declaration=True))


if __name__ == '__main__':
    print('Generating sitemap.xml...')
    generate_sitemap()
