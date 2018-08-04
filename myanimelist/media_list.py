#!/usr/bin/python
# -*- coding: utf-8 -*-

import abc
import collections
from lxml import etree as et
import decimal
import datetime
import urllib.request, urllib.parse, urllib.error

from . import utilities
from .base import Base, MalformedPageError, InvalidBaseError, loadable


class MalformedMediaListPageError(MalformedPageError):
    pass


class InvalidMediaListError(InvalidBaseError):
    pass


class MediaList(Base, collections.Mapping, metaclass=abc.ABCMeta):
    __id_attribute = "username"

    def __getitem__(self, media):
        return self.list[media]

    def __contains__(self, media):
        return media in self.list

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        for media in self.list:
            yield media

    def __init__(self, session, user_name):
        super(MediaList, self).__init__(session)
        self.username = user_name
        if not isinstance(self.username, str) or len(self.username) < 1:
            raise InvalidMediaListError(self.username)
        self._list = None
        self._stats = None

    # subclasses must define a list type, ala "anime" or "manga"
    @abc.abstractmethod
    def type(self):
        pass

    # a list verb ala "watch", "read", etc
    @abc.abstractmethod
    def verb(self):
        pass

    # a list with status ints as indices and status texts as values.
    @property
    def user_status_terms(self):
        statuses = collections.defaultdict(lambda: 'Unknown')
        statuses[1] = self.verb.capitalize() + 'ing'
        statuses[2] = 'Completed'
        statuses[3] = 'On-Hold'
        statuses[4] = 'Dropped'
        statuses[6] = 'Plan to ' + self.verb.capitalize()
        return statuses

    def parse_entry_media_attributes(self, soup):
        """
          Args:
            soup: a lxml.html.HtmlElement containing a row from the current media list

          Return a dict of attributes of the media the row is about.
        """
        row_info = {}

        try:
            start = utilities.parse_profile_date(soup.find('.//series_start').text)
        except ValueError:
            start = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        if start is not None:
            try:
                row_info['aired'] = (start, utilities.parse_profile_date(soup.find('.//series_end').text))
            except ValueError:
                row_info['aired'] = (start, None)
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

        # look up the given media type's status terms.
        status_terms = getattr(self.session, self.type)(1)._status_terms

        try:
            row_info['id'] = int(soup.find('.//series_' + self.type + 'db_id').text)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            row_info['title'] = soup.find('.//series_title').text
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            row_info['status'] = status_terms[int(soup.find('.//series_status').text)]
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            row_info['picture'] = soup.find('.//series_image').text
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return row_info

    def parse_entry(self, soup):
        """
          Given:
            soup: a lxml.html.HtmlElement containing a row from the current media list

          Return a tuple:
            (media object, dict of this row's parseable attributes)
        """
        # parse the media object first.
        media_attrs = self.parse_entry_media_attributes(soup)
        media_id = media_attrs['id']
        del media_attrs['id']
        media = getattr(self.session, self.type)(media_id).set(media_attrs)

        entry_info = {}
        try:
            entry_info['started'] = utilities.parse_profile_date(soup.find('.//my_start_date').text)
        except ValueError:
            entry_info['started'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            entry_info['finished'] = utilities.parse_profile_date(soup.find('.//my_finish_date').text)
        except ValueError:
            entry_info['finished'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            entry_info['status'] = self.user_status_terms[int(soup.find('.//my_status').text)]
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            entry_info['score'] = int(soup.find('.//my_score').text)
            # if user hasn't set a score, set it to None to indicate as such.
            if entry_info['score'] == 0:
                entry_info['score'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            entry_info['last_updated'] = datetime.datetime.fromtimestamp(int(soup.find('.//my_last_updated').text))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return media, entry_info

    def parse_stats(self, soup):
        """
          Given:
            soup: a lxml.etree element containing the current media list's stats

          Return a dict of this media list's stats.
        """
        stats = {}
        for row in soup.getchildren():
            try:
                key = row.tag.replace('user_', '')
                if key == 'id':
                    stats[key] = int(row.text)
                elif key == 'name':
                    stats[key] = row.text
                elif key == self.verb + 'ing':
                    try:
                        stats[key] = int(row.text)
                    except ValueError:
                        stats[key] = 0
                elif key == 'completed':
                    try:
                        stats[key] = int(row.text)
                    except ValueError:
                        stats[key] = 0
                elif key == 'onhold':
                    try:
                        stats['on_hold'] = int(row.text)
                    except ValueError:
                        stats[key] = 0
                elif key == 'dropped':
                    try:
                        stats[key] = int(row.text)
                    except ValueError:
                        stats[key] = 0
                elif key == 'planto' + self.verb:
                    try:
                        stats['plan_to_' + self.verb] = int(row.text)
                    except ValueError:
                        stats[key] = 0
                # for some reason, MAL doesn't substitute 'read' in for manga for the verb here
                elif key == 'days_spent_watching':
                    try:
                        stats['days_spent'] = decimal.Decimal(row.text)
                    except decimal.InvalidOperation:
                        stats[key] = decimal.Decimal(0)
            except:
                if not self.session.suppress_parse_exceptions:
                    raise
        return stats

    def parse(self, xml):
        list_info = {}
        list_page = et.fromstring(xml.encode())

        primary_elt = list_page
        if primary_elt is None:
            raise MalformedMediaListPageError(self.username, xml,
                                              message="Could not find root XML element in " + self.type + " list")

        bad_username_elt = list_page.find('.//error')
        if bad_username_elt is not None:
            raise InvalidMediaListError(self.username, message="Invalid username when fetching " + self.type + " list")

        stats_elt = list_page.find('.//myinfo')
        if stats_elt is None and not utilities.check_if_mal_response_is_empty(list_page):
            raise MalformedMediaListPageError(self.username, xml,
                                              message="Could not find stats element in " + self.type + " list")

        if utilities.check_if_mal_response_is_empty(list_page):
            raise InvalidMediaListError(self.username, message="Empty result set when fetching " + self.type + " list")

        list_info['stats'] = self.parse_stats(stats_elt)

        list_info['list'] = {}
        for row in list_page.findall(".//%s" % self.type):
            (media, entry) = self.parse_entry(row)
            list_info['list'][media] = entry

        return list_info

    def load(self):
        media_list = self.session.session.get('https://myanimelist.net/malappinfo.php?' + urllib.parse.urlencode(
            {'u': self.username, 'status': 'all', 'type': self.type})).text
        self.set(self.parse(media_list))
        return self

    @property
    @loadable('load')
    def list(self):
        return self._list

    @property
    @loadable('load')
    def stats(self):
        return self._stats

    def section(self, status):
        return {k: self.list[k] for k in self.list if self.list[k]['status'] == status}
