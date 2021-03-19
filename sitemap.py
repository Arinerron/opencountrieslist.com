#!/usr/bin/env python3

import xml.etree.cElementTree as ET
import datetime


def generate_sitemap():
    root = ET.Element('urlset')
    root.attrib['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    root.attrib['xsi:schemaLocation'] = 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd'
    root.attrib['xmlns'] = 'http://www.sitemaps.org/schemas/sitemap/0.9'

    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    doc = ET.SubElement(root, 'url')
    ET.SubElement(doc, 'loc').text = 'https://opencountrieslist.com/'
    ET.SubElement(doc, 'lastmod').text = dt
    ET.SubElement(doc, "changefreq").text = 'hourly'
    ET.SubElement(doc, 'priority').text = '1.0'

    tree = ET.ElementTree(root)
    tree.write('web/sitemap.xml', encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    print('Generating sitemap.xml...')
    generate_sitemap()
