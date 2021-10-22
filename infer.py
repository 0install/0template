# Copyright (C) 2017, Bastian Eicher
# See the README file for details, or visit http://0install.net.

from copy import copy
from xml.dom import minidom, Node
from zeroinstall.injector import namespaces
from formatting import format_doc

def from_feed(feed_path):
    doc = minidom.parse(feed_path)
    _replace_uri_with_feed_for(doc)
    _remove_digests_and_sizes(doc)
    _remove_entry_points(doc)
    _generate_variables(doc)
    format_doc(doc)
    return doc

def _replace_uri_with_feed_for(doc):
    root = doc.documentElement
    if not root.hasAttribute('uri'):
        return
    new_elem = doc.createElement('feed-for')
    new_elem.setAttribute('interface', root.getAttribute('uri'))
    root.appendChild(new_elem)
    root.removeAttribute('uri')

def _remove_digests_and_sizes(doc):
    def walk(elem):
        to_remove = []
        for child in elem.childNodes:
            if child.nodeType != Node.ELEMENT_NODE or not child.namespaceURI == namespaces.XMLNS_IFACE:
                continue
            if child.localName == 'manifest-digest':
                to_remove.append(child)
            elif child.localName == 'implementation':
                if child.hasAttribute('id') and not child.getAttribute('id').startswith('.') and not child.getAttribute('id').startswith('/'):
                    child.removeAttribute('id')
            elif child.localName == 'archive' or child.localName == 'file':
                if child.hasAttribute('size'):
                    child.removeAttribute('size')
            walk(child)
        for child in to_remove:
            elem.removeChild(child)

    walk(doc.documentElement)

def _remove_entry_points(doc):
    root = doc.documentElement
    to_remove = []
    for child in root.childNodes:
        if child.localName == 'entry-point' and child.namespaceURI == namespaces.XMLNS_IFACE:
            to_remove.append(child)
    for node in to_remove:
        root.removeChild(node)

def _generate_variables(doc):
    def introduce_var(elem, subst_map, attribute_name):
        if elem.hasAttribute(attribute_name):
            variable_str = '{' + attribute_name + '}'
            subst_map[elem.getAttribute(attribute_name)] = variable_str
            elem.setAttribute(attribute_name, variable_str)

    def apply_subst(value, subst_map):
        for old, new in subst_map.items():
            value = str.replace(value, old, new)
        return value

    def walk(elem, subst_map):
        for name, value in elem.attributes.items():
            elem.attributes[name] = apply_subst(value, subst_map)
        if elem.localName == 'implementation' or elem.localName == 'group':
            subst_map = copy(subst_map)
            introduce_var(elem, subst_map, 'version')
            introduce_var(elem, subst_map, 'released')
        for child in elem.childNodes:
            if not child.namespaceURI == namespaces.XMLNS_IFACE:
                continue
            if child.nodeType == Node.TEXT_NODE:
                child.data = apply_subst(child.data, subst_map)
            elif child.nodeType == Node.ELEMENT_NODE:
                walk(child, subst_map)

    walk(doc.documentElement, {})
