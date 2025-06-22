"""Utilities for comparing XML strings for equivalence."""

import xml.etree.ElementTree as ET


def _normalize_text(s):
    """Normalize text by stripping if it consists only of whitespace."""
    if s is None:
        return None
    s = s.strip()
    return None if s == "" else s


def _elements_are_equal(e1, e2):
    """Compare two XML elements for structural and textual equivalence."""
    if e1.tag != e2.tag:
        return False
    if _normalize_text(e1.text) != _normalize_text(e2.text):
        return False
    if _normalize_text(e1.tail) != _normalize_text(e2.tail):
        return False
    if list(e1.attrib.items()) != list(e2.attrib.items()):  # Order-sensitive
        return False
    if len(e1) != len(e2):
        return False
    return all(_elements_are_equal(c1, c2) for c1, c2 in zip(e1, e2))


def xml_are_equivalent(xml1, xml2):
    """
    Compare two XML strings for structural and textual equivalence,
    ignoring insignificant whitespace but preserving attribute order.

    Args:
        xml1: First XML string to compare
        xml2: Second XML string to compare

    Returns:
        bool: True if XML strings are structurally equivalent
    """
    # This covers the case where the strings are not actually XML, like "FAILED"
    if xml1 == xml2:
        return True

    if xml1 is None and xml2 is None:
        return True
    if xml1 is None or xml2 is None:
        return False

    try:
        tree1 = ET.fromstring(xml1)
        tree2 = ET.fromstring(xml2)
        return _elements_are_equal(tree1, tree2)
    except ET.ParseError:
        return False


def xml_lists_are_equivalent(xml_list1, xml_list2):
    """
    Compare two lists of XML strings for equivalence.

    Args:
        xml_list1: First list of XML strings
        xml_list2: Second list of XML strings

    Returns:
        bool: True if lists have same length and all corresponding XML strings are equivalent
    """
    return len(xml_list1) == len(xml_list2) and all(
        xml_are_equivalent(x, y) for x, y in zip(xml_list1, xml_list2)
    )
