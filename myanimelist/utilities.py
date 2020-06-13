#!/usr/bin/python
# -*- coding: utf-8 -*-
from lxml.cssselect import CSSSelector
from lxml import html as ht
from lxml import etree as et
from lxml.html import HtmlElement
import datetime
import re
import urllib.parse as urllib


def fix_bad_html(html):
    """
      Fixes for various DOM errors that MAL commits.
      Yes, I know this is a cardinal sin, but there's really no elegant way to fix this.
    """
    # on anime list pages, sometimes tds won't be properly opened.
    html = re.sub(r'[\s]td class=', "<td class=", html)

    # on anime list pages, if the user doesn't specify progress, MAL will try to close a span it didn't open.
    def anime_list_closing_span(match):
        return match.group('count') + '/' + match.group('total') + '</td>'

    html = re.sub(r'(?P<count>[0-9\-]+)</span>/(?P<total>[0-9\-]+)</a></span></td>', anime_list_closing_span, html)

    # on anime info pages, under rating, there's an extra </div> by the "licensing company" note.
    html = html.replace('<small>L</small></sup><small> represents licensing company</small></div>',
                        '<small>L</small></sup><small> represents licensing company</small>')

    # on manga character pages, sometimes the character info column will have an extra </div>.
    def manga_character_double_closed_div_picture(match):
        return "<td " + match.group('td_tag') + ">\n\t\t\t<div " + match.group('div_tag') + "><a " + match.group(
                'a_tag') + "><img " + match.group('img_tag') + "></a></div>\n\t\t\t</td>"

    html = re.sub(
            r"""<td (?P<td_tag>[^>]+)>\n\t\t\t<div (?P<div_tag>[^>]+)><a (?P<a_tag>[^>]+)><img (?P<img_tag>[^>]+)></a></div>\n\t\t\t</div>\n\t\t\t</td>""",
            manga_character_double_closed_div_picture, html)

    def manga_character_double_closed_div_character(match):
        return """<a href="/character/""" + match.group('char_link') + """">""" + match.group(
                'char_name') + """</a>\n\t\t\t<div class="spaceit_pad"><small>""" + match.group(
                'role') + """</small></div>"""

    html = re.sub(
            r"""<a href="/character/(?P<char_link>[^"]+)">(?P<char_name>[^<]+)</a>\n\t\t\t<div class="spaceit_pad"><small>(?P<role>[A-Za-z ]+)</small></div>\n\t\t\t</div>""",
            manga_character_double_closed_div_character, html)
    return html


def get_clean_dom(html):
    """
      Given raw HTML from a MAL page, return a lxml.objectify object with cleaned HTML.
    """
    return ht.fromstring(fix_bad_html(html))


def urlencode(url):
    """
      Given a string, return a string that can be used safely in a MAL url.
    """
    return urllib.urlencode({'': url.replace(' ', '_')})[1:].replace('%2F', '/')


def extract_tags(tags):
    list(map(lambda x: x.extract(), tags))


def parse_profile_date(text, suppress=False):
    """
      Parses a MAL date on a profile page.
      May raise ValueError if a malformed date is found.
      If text is "Unknown" or "?" or "Not available" then returns None.
      Otherwise, returns a datetime.date object.
    """
    try:
        if text == "Unknown" or text == "?" or text == "Not available":
            return None
        if text == "Now":
            return datetime.datetime.now()

        seconds_match = re.match(r'(?P<seconds>[0-9]+) second(s)? ago', text)
        if seconds_match:
            return datetime.datetime.now() - datetime.timedelta(seconds=int(seconds_match.group('seconds')))

        minutes_match = re.match(r'(?P<minutes>[0-9]+) minute(s)? ago', text)
        if minutes_match:
            return datetime.datetime.now() - datetime.timedelta(minutes=int(minutes_match.group('minutes')))

        hours_match = re.match(r'(?P<hours>[0-9]+) hour(s)? ago', text)
        if hours_match:
            return datetime.datetime.now() - datetime.timedelta(hours=int(hours_match.group('hours')))

        today_match = re.match(r'Today, (?P<hour>[0-9]+):(?P<minute>[0-9]+) (?P<am>[APM]+)', text)
        if today_match:
            hour = int(today_match.group('hour'))
            minute = int(today_match.group('minute'))
            am = today_match.group('am')
            if am == 'PM' and hour < 12:
                hour += 12
            today = datetime.date.today()
            return datetime.datetime(year=today.year, month=today.month, day=today.day, hour=hour, minute=minute,
                                     second=0)

        yesterday_match = re.match(r'Yesterday, (?P<hour>[0-9]+):(?P<minute>[0-9]+) (?P<am>[APM]+)', text)
        if yesterday_match:
            hour = int(yesterday_match.group('hour'))
            minute = int(yesterday_match.group('minute'))
            am = yesterday_match.group('am')
            if am == 'PM' and hour < 12:
                hour += 12
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            return datetime.datetime(year=yesterday.year, month=yesterday.month, day=yesterday.day, hour=hour,
                                     minute=minute, second=0)

        try:
            return datetime.datetime.strptime(text, '%m-%d-%y, %I:%M %p')
        except ValueError:
            pass
        # see if it's a date.
        try:
            return datetime.datetime.strptime(text, '%m-%d-%y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%Y-%m-%d').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%Y-%m-00').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%Y-00-00').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%B %d, %Y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%b %d, %Y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%Y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%b %d, %Y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, '%b, %Y').date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, "%b %d, %Y %I:%M %p")
        except ValueError:
            pass
        parsed_date = None
        try:
            parsed_date = datetime.datetime.strptime(text, '%b %d, %I:%M %p')
        except ValueError:
            try:
                parsed_date = datetime.datetime.strptime(text, '%b %d, %Y %I:%M %p')
            except ValueError: # if the user don't display his birthday year, it never work.
                try:
                    parsed_date = datetime.datetime.strptime(text, '%b %Y')
                except ValueError:
                    parsed_date = None
        # see if it's a month/year pairing.
        return parsed_date if parsed_date is not None else None
    except:
        if suppress:
            return None
        raise


def css_select(selector_str, element):
    if not isinstance(element, et.ElementBase):
        raise TypeError("css_select_first - the element argument (1) is not a subtype of lxml.etree.ElementBase")
    selector = CSSSelector(selector_str)
    return selector(element)


def css_select_first(selector_str, element):
    if not isinstance(element, et.ElementBase):
        raise TypeError("css_select_first - the element argument (1) is not a subtype of lxml.etree.ElementBase")
    selector = CSSSelector(selector_str)
    results = selector(element)
    return results[0] if len(results) >= 1 else None


def check_if_mal_response_is_empty(xmlel):
    if xmlel is None:
        raise Exception("xmlel argument cannot be None.")

    if len(xmlel) == 0:
        return True

    return False


def is_open_graph_style_stat_element(element):
    return element is not None and type(element) is HtmlElement and ((element.tail is not None and element.tail.strip() == "") or element.tail is None)


def extract_datasheet_title(title_tag):
    result = ""
    title_tag_span = title_tag.find("span")
    if title_tag_span is None and title_tag.text is not None:
        result = title_tag.text.strip()
    elif title_tag_span is not None and title_tag_span.text is not None:
        result = title_tag_span.text.strip()
    elif title_tag_span is not None and title_tag_span.text is None:
        sub_span = title_tag_span.find("span")
        if sub_span is not None:
            result = sub_span.text.strip()

    return result
