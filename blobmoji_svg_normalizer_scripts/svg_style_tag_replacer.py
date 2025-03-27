#!/usr/bin/env python3
# Before using script: pip install lxml cssselect cssutils
import os
from lxml import etree
from cssselect import GenericTranslator
import cssutils

cssutils.log.setLevel("ERROR")  # Suppress CSS parsing warnings

def apply_inline_styles(svg_path):
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(svg_path, parser)
    root = tree.getroot()

    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    style_elements = root.xpath('//svg:style', namespaces=namespaces)
    if not style_elements:
        return

    for style in style_elements:
        css = cssutils.parseString(style.text)
        for rule in css:
            if rule.type != rule.STYLE_RULE:
                continue
            selector = rule.selectorText
            try:
                xpath = GenericTranslator().css_to_xpath(selector)
            except Exception as e:
                print(f"Skipping invalid selector '{selector}' in {svg_path}: {e}")
                continue

            elements = root.xpath(xpath, namespaces=namespaces)
            for el in elements:
                style_attr = el.get('style', '')
                new_styles = {k.strip(): v.strip() for k, v in (s.split(':', 1) for s in style_attr.split(';') if s.strip())}
                for prop in rule.style:
                    new_styles[prop.name] = prop.value
                el.set('style', '; '.join(f'{k}: {v}' for k, v in new_styles.items()))

        # Remove the <style> tag after applying
        style.getparent().remove(style)

    # Save modified SVG
    tree.write(svg_path, pretty_print=True, xml_declaration=True, encoding='utf-8')

def process_svg_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.svg'):
                full_path = os.path.join(root, file)
                try:
                    apply_inline_styles(full_path)
                    print(f"Processed: {full_path}")
                except Exception as e:
                    print(f"Error processing {full_path}: {e}")

svg_folder = "svg"
process_svg_folder(svg_folder)
