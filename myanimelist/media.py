#!/usr/bin/python
# -*- coding: utf-8 -*-
import abc
import decimal
import re

from . import utilities
from .base import Base, MalformedPageError, InvalidBaseError, loadable
from lxml.etree import XPath
from urllib3 import PoolManager as HttpSocketPool


class MalformedMediaPageError(MalformedPageError):
    """Indicates that a media-related page on MAL has broken markup in some way.
    """
    pass


class InvalidMediaError(InvalidBaseError):
    """Indicates that the media requested does not exist on MAL.
    """
    pass


# noinspection PyBroadException
class Media(Base, metaclass=abc.ABCMeta):
    """Abstract base class for all media resources on MAL.

    To subclass, create a class that inherits from Media, implementing status_terms and consuming_verb at the bare minimum.
    """

    @abc.abstractproperty
    def _status_terms(self):
        """
        :rtype: dict
        A status dict with::

          keys -- int statuses
          values -- string statuses e.g. "Airing"
        """
        pass

    @abc.abstractproperty
    def _consuming_verb(self):
        """
        :rtype: str
        :return: the verb used to consume this media, e.g. "read"
        """
        pass

    @classmethod
    def newest(cls, session):
        """Fetches the latest media added to MAL.

        :type session: :class:`myanimelist.session.Session`
        :param session: A valid MAL session

        :rtype: :class:`.Media`
        :return: the newest media on MAL

        :raises: :class:`.MalformedMediaPageError`

        """
        media_type = cls.__name__.lower()
        p = session.session.get('https://myanimelist.net/' + media_type + '.php?o=9&c[]=a&c[]=d&cv=2&w=1').text
        soup = utilities.get_clean_dom(p)
        latest_entry = utilities.css_select_first("div.hoverinfo", soup)
        if latest_entry is None:
            raise MalformedMediaPageError(0, p, "No media entries found on recently-added page")
        latest_id = int(latest_entry.get("rel", "")[1:])
        return getattr(session, media_type)(latest_id)

    def __init__(self, session, id):
        """Creates an instance of Media.

        :type session: :class:`myanimelist.session.Session`
        :param session: A valid MAL session.

        :type id: int
        :param id: The media's ID.

        :raises: :class:`.InvalidMediaError`

        """
        super(Media, self).__init__(session)
        self.consuming_verb = ''
        self.id = id
        if not isinstance(self.id, int) or int(self.id) < 1:
            raise InvalidMediaError(self.id)
        self._title = None
        self._picture = None
        self._alternative_titles = None
        self._type = None
        self._status = None
        self._genres = None
        self._score = None
        self._rank = None
        self._popularity = None
        self._members = None
        self._favorites = None
        self._popular_tags = None
        self._synopsis = None
        self._related = None
        self._characters = None
        self._score_stats = None
        self._status_stats = None
        self._http = HttpSocketPool(retries=3)

    def parse_sidebar(self, media_page):
        """Parses the DOM and returns media attributes in the sidebar.

        :type media_page: :class:`lxml.html.HtmlElement`
        :param media_page: MAL media page's DOM

        :rtype: dict
        :return: media attributes.

        :raises: InvalidMediaError, MalformedMediaPageError

        """
        media_info = {}

        # if MAL says the series doesn't exist, raise an InvalidMediaError.
        if not self._validate_page(media_page):
            raise InvalidMediaError(self.id)

        title_tag = None

        try:
            result_list = utilities.css_select("#contentWrapper", media_page)
            if len(result_list) == 0:
                raise MalformedMediaPageError(self.id, media_page, message="Could not find content wrapper")

            title_tag = result_list[0].find('.//h1')
            if title_tag is None and title_tag.find("span") is None:
                # otherwise, raise a MalformedMediaPageError.
                raise MalformedMediaPageError(self.id, media_page, message="Could not find title div")
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            if title_tag is None:
                raise MalformedMediaPageError(self.id, media_page,
                                              message="Could not find h1 element to find the title")

            title_tag_span = title_tag.find("span")
            if title_tag_span is None and title_tag.text is not None:
                media_info['title'] = title_tag.text.strip()
            elif title_tag_span is not None and title_tag_span.text is not None:
                media_info['title'] = title_tag_span.text.strip()
            else:
                raise MalformedMediaPageError(self.id, media_page, message="Could not find title in h1")
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        info_panel_first = None
        try:
            container = utilities.css_select_first("#content", media_page)
            if container is None:
                raise MalformedMediaPageError(self.id, media_page, message="Could not find the info table. (Ph1)")

            info_panel_first = container.find(".//table/tr/td")
            if info_panel_first is None:
                raise MalformedMediaPageError(self.id, media_page, message="Could not find the info table. (Ph2)")
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            picture_tag = info_panel_first.find('.//img')
            if picture_tag is not None:
                media_info['picture'] = picture_tag.get('src').encode("utf-8").decode("utf-8")
            else:
                media_info['picture'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # assemble alternative titles for this series.
            media_info['alternative_titles'] = {}
            alt_titles_results = info_panel_first.xpath(".//h2[text()[contains(.,'Alternative Titles')]]")

            if len(alt_titles_results) == 0:
                raise MalformedMediaPageError(self.id, media_page, message="Could not find the alternative titles")

            alt_titles_header = alt_titles_results[0]
            if alt_titles_header is not None:
                next_tag = utilities.css_select("h2 + div.spaceit_pad", alt_titles_header)[0]
                while True:
                    if next_tag is None or len(utilities.css_select("span.dark_text", next_tag)) == 0:
                        # not a language node, break.
                        break
                    # get language and remove the node.
                    language = next_tag.find(".//span").text[:-1]
                    names = next_tag.xpath(".//text()")[-1].strip().split(', ')
                    media_info['alternative_titles'][language] = names
                    temp = next_tag.xpath("./following-sibling::div[@class='spaceit_pad']")
                    if len(temp) == 0:
                        break
                    else:
                        next_tag = temp[0]
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            type_tag_results = info_panel_first.xpath(".//span[text()[contains(.,'Type:')]]")
            if len(type_tag_results) == 0:
                raise Exception("Couldnt find type tag.")
            type_tag = "".join(type_tag_results[0].getparent().xpath(".//text()")).strip().replace('\n', '') \
                .split(": ")[-1].rstrip()
            media_info['type'] = type_tag.strip()
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            status_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Status:')]]")
            if len(status_tag_results) == 0:
                raise Exception("Couldn't find status tag.")
            status_tag = status_tag_results[0].getparent().xpath(".//text()")[-1]
            media_info['status'] = status_tag.strip()
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            genres_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Genres:')]]")
            if len(genres_tag_results) == 0:
                raise Exception("Couldn't find genres tag.")
            genres_tag = genres_tag_results[0].getparent().findall("a")
            media_info['genres'] = []
            for genre_link in genres_tag:
                link_parts = genre_link.get('href').split('[]=')
                if len(link_parts) == 0:
                    link_parts = genre_link.get('href').split('/')
                    genre = self.session.genre(int(link_parts[-2])).set({'name': genre_link.text})
                else:
                    link_parts = genre_link.get('href').split("/")
                    if "myanimelist.net" in genre_link.get('href'):
                        genre = self.session.genre(int(link_parts[-2])).set({'name': genre_link.text})
                    else:
                        genre = self.session.genre(int(link_parts[-2])).set({'name': genre_link.text})

                media_info['genres'].append(genre)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # grab statistics for this media.
            score_tag_results = info_panel_first.xpath(
                ".//div[contains(@class,'js-statistics-info')]//span[text()[contains(.,'Score:')]]")
            if len(score_tag_results) == 0:
                raise Exception("Couldn't find score tag.")

            # there are two types of layout for scores: the ones with span elements with open graph / html5 attributes
            # and the ones without these special attributes
            if utilities.is_open_graph_style_stat_element(score_tag_results[0]):
                score_text = utilities.css_select('span.dark_text + span', score_tag_results[0])[0].text
                score_tag = utilities.css_select('span.dark_text + span', score_tag_results[0])[0]

                rating_count_els = score_tag.getparent().xpath(".//span[3]|.//small/span[1]")
                if len(rating_count_els) > 0:
                    num_users = int(rating_count_els[0].text.replace(',', ''))
                else:
                    small_tags = score_tag.getparent().xpath("./small[1]")
                    if len(small_tags) > 0:
                        small_tag = small_tags[0]
                        m = re.match("\(scored by ([0-9]+)", small_tag.text)
                        num_users = int(m.group(1))
                    else:
                        num_users = 0
            else:
                score_text = score_tag_results[0].tail.strip()
                small_tags = score_tag_results[0].xpath("./following-sibling::small")
                if len(small_tags) > 0:
                    small_tag = small_tags[0]
                    m = re.match("\(scored by ([0-9]+)", small_tag.text)
                    num_users = int(m.group(1))
                else:
                    num_users = 0

            if score_text == "N/A":
                score = None
            else:
                score = float(score_text)

            stripped_score = score
            if stripped_score is not None:
                media_info['score'] = (decimal.Decimal(stripped_score), num_users)
            else:
                media_info['score'] = (0, 0)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            rank_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Ranked:')]]")
            if len(rank_tag_results) == 0:
                raise Exception("Couldn't find rank tag.")
            # rank_tag is a lxml.etree._ElementUnicodeResult here:

            contains = rank_tag_results[0].getparent().xpath(".//text()[contains(.,'#')]")
            if contains:
                rank_tag = contains[0]
                media_info['rank'] = int(rank_tag.strip()[1:].replace(',', ''))
            else:
                media_info['rank'] = "N/A"

        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            popularity_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Popularity:')]]")
            if len(popularity_tag_results) == 0:
                raise Exception("Couldn't find popularity tag.")
            # popularity_tag is a lxml.etree._ElementUnicodeResult here:
            popularity_tag = popularity_tag_results[0].getparent().xpath(".//text()[contains(.,'#')]")[0]
            media_info['popularity'] = int(popularity_tag.strip()[1:].replace(',', ''))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            members_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Members:')]]")
            if len(members_tag_results) == 0:
                raise Exception("Couldn't find members tag.")
            members_tag = members_tag_results[0].getparent().xpath(".//text()")[-1]
            media_info['members'] = int(members_tag.strip().replace(',', ''))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            favorites_tag_results = info_panel_first.xpath(".//div/span[text()[contains(.,'Favorites:')]]")
            if len(favorites_tag_results) == 0:
                raise Exception("Couldn't find favorites tag.")
            favorites_tag = favorites_tag_results[0].getparent().xpath(".//text()")[-1]
            media_info['favorites'] = int(favorites_tag.strip().replace(',', ''))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        # not available anymore
        # try:
        #     # get popular tags.
        #     tags_header = media_page.find('h2', text='Popular Tags')
        #     media_info['popular_tags'] = {}
        #     if tags_header is not None:
        #         tags_tag = tags_header.find_next_sibling('span')
        #         for tag_link in tags_tag.find_all('a'):
        #             tag = self.session.tag(tag_link.text)
        #             num_people = int(re.match(r'(?P<people>[0-9]+) people', tag_link.get('title')).group('people'))
        #             media_info['popular_tags'][tag] = num_people
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise

        return media_info

    def parse(self, media_page):
        """Parses the DOM and returns media attributes in the main-content area.

        :type media_page: :class:`lxml.html.HtmlElement`
        :param media_page: MAL media page's DOM

        :rtype: dict
        :return: media attributes.

        """
        media_info = self.parse_sidebar(media_page)

        try:
            temp = media_page.xpath(".//h2[text()[contains(.,'Synopsis')]]")
            media_info['synopsis'] = ""
            if temp is not None and len(temp) > 0:
                elemf = temp[0]
                elemf = elemf.getparent().find(".//span[@itemprop='description']")
                if elemf is not None:
                    synopsis_elt = elemf
                    media_info['synopsis'] = synopsis_elt.text_content().strip()
                else:
                    media_info['synopsis'] = ''
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            related_tile_results = media_page.xpath(".//h2[text()[contains(.,'Related %s')]]" % self.__class__.__name__)
            if len(related_tile_results) == 0:
                related_title = None
            else:
                related_title = related_tile_results[0]

            if related_title is not None:
                # first we need the table
                related_table = utilities.css_select("table.anime_detail_related_anime", related_title.getparent())[0]
                table_rows = related_table.findall("tr")
                related = {}
                # loop through the rows
                for row in table_rows:
                    cols = row.findall("td")
                    if len(cols) != 2:
                        raise MalformedMediaPageError(self.id, related_table,
                                                      message="There are too much columns in the related table.")
                    relation_type_el = cols[0]
                    relation_type = relation_type_el.text.strip().replace(":", "")
                    relations_el = cols[1].findall("a")
                    for link in relations_el:
                        href = link.get("href").replace("http://myanimelist.net", "")
                        if not re.match(r'/(anime|manga)', href):
                            break
                        title = link.text
                        href_parts = href.split("/")
                        # sometimes links on MAL are broken, of the form /anime//
                        if href_parts[2] == '':
                            continue
                        # of the form: /(anime|manga)/1/Cowboy_Bebop
                        obj_id = int(href_parts[2])
                        new_obj = getattr(self.session, href_parts[1])(obj_id).set({'title': title})
                        if relation_type not in related:
                            related[relation_type] = [new_obj]
                        else:
                            related[relation_type].append(new_obj)
                media_info['related'] = related
            else:
                media_info['related'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return media_info

    def parse_stats(self, media_page):
        """Parses the DOM and returns media statistics attributes.

        :type media_page: :class:`lxml.html.HtmlElement`
        :param media_page: MAL media stats page's DOM

        :rtype: dict
        :return: media stats attributes.

        """

        # cache common xpath strings:
        xget_text = XPath(".//text()")

        def _get_stat_row(property_name):
            results = media_page.xpath(".//span[@class='dark_text' and text()[contains(.,'%s')]]" % property_name)
            if len(results) == 0:
                return None

            return results[0]

        def _get_clean_property_val(el):
            return int(xget_text(el.getparent())[1].strip().replace(',', ''))

        media_info = self.parse_sidebar(media_page)
        verb_progressive = self.consuming_verb + 'ing'
        status_stats = {
            verb_progressive: 0,
            'completed': 0,
            'on_hold': 0,
            'dropped': 0,
            'plan_to_' + self.consuming_verb: 0
        }

        try:
            consuming_elt = _get_stat_row(verb_progressive.capitalize())
            if consuming_elt:
                status_stats[verb_progressive] = _get_clean_property_val(consuming_elt)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            completed_elt = _get_stat_row("Completed:")
            if completed_elt is not None:
                status_stats['completed'] = _get_clean_property_val(completed_elt)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # On-Hold:
            on_hold_elt = _get_stat_row("On-Hold:")
            if on_hold_elt is not None:
                status_stats['on_hold'] = _get_clean_property_val(on_hold_elt)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            dropped_elt = _get_stat_row("Dropped:")
            if dropped_elt is not None:
                status_stats['dropped'] = _get_clean_property_val(dropped_elt)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # "Plan to " + self.consuming_verb.capitalize() + ":"
            planning_elt = _get_stat_row("Plan to %s:" % self.consuming_verb.capitalize())
            if planning_elt:
                status_stats['plan_to_' + self.consuming_verb] = _get_clean_property_val(planning_elt)
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        media_info['status_stats'] = status_stats

        score_stats = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
            8: 0,
            9: 0,
            10: 0
        }
        try:
            temp = media_page.xpath(".//h2[text()[contains(.,'Score Stats')]]/following-sibling::table[1]")
            if len(temp) != 0:
                score_stats_table = temp[0]
                if score_stats_table is not None:
                    score_stats = {}
                    score_rows = score_stats_table.findall('tr')
                    for i in range(len(score_rows)):
                        score_value = int(score_rows[i].find('td').text)
                        score_stats[score_value] = int(
                            score_rows[i].find('.//span/small').text.replace('(', '').replace(' votes)', ''))

        except:
            if not self.session.suppress_parse_exceptions:
                raise

        media_info['score_stats'] = score_stats

        return media_info

    def parse_characters(self, character_page):
        """Parses the DOM and returns media character attributes in the sidebar.

        :type character_page: :class:`lxml.html.HtmlElement`
        :param character_page: MAL character page's DOM

        :rtype: dict
        :return: character attributes.

        """
        media_info = self.parse_sidebar(character_page)

        try:
            temp = character_page.xpath(".//h2[text()[contains(.,'Characters')]]/following-sibling::table[1]")
            media_info['characters'] = {}
            if len(temp) != 0:
                curr_elt = temp[0]
                while curr_elt is not None:
                    curr_row = curr_elt.find('tr')
                    # character in second col.
                    character_col = curr_row.find(".//td[2]")
                    character_link = character_col.find('.//a')
                    character_name = ' '.join(reversed(character_link.text.split(', ')))
                    link_parts = character_link.get('href').split('/')
                    # of the form /character/7373/Holo
                    if "myanimelist.net" not in link_parts:
                        character_id = int(link_parts[2])
                    # or of the form https://myanimelist.net/character/7373/Holo
                    else:
                        character_id = int(link_parts[4])

                    character = self.session.character(character_id).set({'name': character_name})
                    role = character_col.find('.//small').text
                    media_info['characters'][character] = {'role': role}
                    temp = curr_elt.xpath("./following-sibling::table[1]")
                    if len(temp) != 0:
                        curr_elt = temp[0]
                    else:
                        curr_elt = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return media_info

    def load(self):
        """Fetches the MAL media page and sets the current media's attributes.

        :rtype: :class:`.Media`
        :return: current media object.

        """
        media_page = self.session.session.get(
            'https://myanimelist.net/' + self.__class__.__name__.lower() + '/' + str(self.id)).text
        self.set(self.parse(utilities.get_clean_dom(media_page)))
        return self

    def load_stats(self):
        """Fetches the MAL media statistics page and sets the current media's statistics attributes.

        :rtype: :class:`.Media`
        :return: current media object.

        """
        stats_page = self.session.session.get('https://myanimelist.net/' + self.__class__.__name__.lower() + '/' + str(
            self.id) + '/' + utilities.urlencode(self.title) + '/stats').text
        self.set(self.parse_stats(utilities.get_clean_dom(stats_page)))
        return self

    def load_characters(self):
        """Fetches the MAL media characters page and sets the current media's character attributes.

        :rtype: :class:`.Media`
        :return: current media object.

        """
        characters_page = self.session.session.get(
            'https://myanimelist.net/' + self.__class__.__name__.lower() + '/' + str(
                self.id) + '/' + utilities.urlencode(self.title).replace('/', '_') + '/characters').text
        self.set(self.parse_characters(utilities.get_clean_dom(characters_page)))
        return self

    @property
    @loadable('load')
    def title(self):
        """Media's title.
        """
        return self._title

    @property
    @loadable('load')
    def picture(self):
        """URL of media's primary pictures.
        """
        return self._picture

    @property
    @loadable('load')
    def alternative_titles(self):
        """Alternative titles dict, with types of titles, e.g. 'Japanese', 'English', or 'Synonyms' as keys, and lists of said alternative titles as values.
        """
        return self._alternative_titles

    @property
    @loadable('load')
    def type(self):
        """Type of this media, e.g. 'TV' or 'Manga' or 'Movie'
        """
        return self._type

    @property
    @loadable('load')
    def status(self):
        """Publication status, e.g. 'Finished Airing'
        """
        return self._status

    @property
    @loadable('load')
    def genres(self):
        """A list of :class:`myanimelist.genre.Genre` objects associated with this media.
        """
        return self._genres

    @property
    @loadable('load')
    def score(self):
        """A tuple(2) containing an instance of decimal.Decimal storing the aggregate score, weighted or non-weighted, and an int storing the number of ratings

        """
        return self._score

    @property
    @loadable('load')
    def rank(self):
        """Score rank.
        """
        return self._rank

    @property
    @loadable('load')
    def popularity(self):
        """Popularity rank.
        """
        return self._popularity

    @property
    @loadable('load')
    def members(self):
        """Number of members.
        """
        return self._members

    @property
    @loadable('load')
    def favorites(self):
        """Number of users who favourited this media.
        """
        return self._favorites

    @property
    @loadable('load')
    def popular_tags(self):
        """Tags dict with :class:`myanimelist.tag.Tag` objects as keys, and the number of tags as values.
        """
        return self._popular_tags

    @property
    @loadable('load')
    def synopsis(self):
        """Media synopsis.
        """
        return self._synopsis

    @property
    @loadable('load')
    def related(self):
        """Related media dict, with strings of relation types, e.g. 'Sequel' as keys, and lists containing instances of :class:`.Media` subclasses as values.
        """
        return self._related

    @property
    @loadable('load_characters')
    def characters(self):
        """Character dict, with :class:`myanimelist.character.Character` objects as keys, and a dict with attributes of this role, e.g. 'role': 'Main' as values.
        """
        return self._characters

    @property
    @loadable('load_stats')
    def status_stats(self):
        """Status statistics dict, with strings of statuses, e.g. 'on_hold' as keys, and an int number of users as values.
        """
        return self._status_stats

    @property
    @loadable('load_stats')
    def score_stats(self):
        """Score statistics dict, with int scores from 1-10 as keys, and an int number of users as values.
        """
        return self._score_stats

