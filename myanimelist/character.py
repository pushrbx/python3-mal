#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from . import utilities
from .base import Base, MalformedPageError, InvalidBaseError, loadable


class MalformedCharacterPageError(MalformedPageError):
    """Indicates that a character-related page on MAL has irreparably broken markup in some way.
    """
    pass


class InvalidCharacterError(InvalidBaseError):
    """Indicates that the character requested does not exist on MAL.
    """
    pass


class Character(Base):
    """Primary interface to character resources on MAL.
    """

    def __init__(self, session, character_id):
        """Creates a new instance of Character.

        :type session: :class:`myanimelist.session.Session`
        :param session: A valid MAL session
        :type character_id: int
        :param character_id: The desired character's ID on MAL

        :raises: :class:`.InvalidCharacterError`

        """
        super(Character, self).__init__(session)
        self.id = character_id
        if not isinstance(self.id, int) or int(self.id) < 1:
            raise InvalidCharacterError(self.id)
        self._name = None
        self._full_name = None
        self._name_jpn = None
        self._description = None
        self._voice_actors = None
        self._animeography = None
        self._mangaography = None
        self._num_favorites = None
        self._favorites = None
        self._picture = None
        self._pictures = None
        self._clubs = None

    def parse_sidebar(self, character_page):
        """Parses the DOM and returns character attributes in the sidebar.

        :type character_page: :class:`lxml.html.HtmlElement`
        :param character_page: MAL character page's DOM

        :rtype: dict
        :return: Character attributes

        :raises: :class:`.InvalidCharacterError`, :class:`.MalformedCharacterPageError`
        """
        character_info = {}

        error_tag = character_page.xpath(".//div[contains(@class,'error')] | .//div[@class='badresult']")
        if len(error_tag) > 0:
            # MAL says the character does not exist.
            raise InvalidCharacterError(self.id)

        info_panel_first = None

        try:
            container = character_page.find(".//div[@id='contentWrapper']")
            if container is None:
                raise MalformedCharacterPageError(self.id, character_page, message="Could not find title div")
            full_name_tag = container.find('.//h1')
            if full_name_tag is None:
                # Page is malformed.
                raise MalformedCharacterPageError(self.id, character_page, message="Could not find title div")
            title_tag_span = full_name_tag.find("span")
            title_text = utilities.extract_datasheet_title(title_tag_span)

            if title_text is None or title_text == '':
                raise MalformedCharacterPageError(self.id, character_page, message="Could not find character name")
            character_info['full_name'] = title_text
            info_panel_first = container.find(".//table/tr/td")
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        if "Invalid" in character_info['full_name']:
            raise InvalidCharacterError(self.id)

        try:
            picture_tag = info_panel_first.find('.//img')
            character_info['picture'] = picture_tag.get('data-src')
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # assemble animeography for this character.
            character_info['animeography'] = {}
            temp = info_panel_first.xpath(".//div[text()[contains(.,'Animeography')]]")
            if len(temp) == 0:
                raise Exception("Could not find Animeography header")
            animeography_header = temp[0]
            animeography_table = animeography_header.xpath("./following-sibling::table[1]")
            if len(animeography_table) == 0:
                raise Exception("Could not find Animeography header")
            animeography_table = animeography_table[0]
            for row in animeography_table.findall('.//tr'):
                # second column has anime info.
                info_col = row.findall('.//td')[1]
                anime_link = info_col.find('a')
                link_parts = anime_link.get('href').split('/')
                # of the form: /anime/1/Cowboy_Bebop
                anime = self.session.anime(int(link_parts[4])).set({'title': anime_link.text})
                role = info_col.find('.//small').text
                character_info['animeography'][anime] = role
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # assemble mangaography for this character.
            character_info['mangaography'] = {}
            temp = info_panel_first.xpath(".//div[text()[contains(.,'Mangaography')]]")
            if len(temp) == 0:
                raise Exception("Could not find Mangaography header")
            mangaography_header = temp[0]
            mangaography_table = mangaography_header.xpath("./following-sibling::table[1]")[0]
            for row in mangaography_table.findall('tr'):
                # second column has manga info.
                info_col = row.findall('.//td')[1]
                manga_link = info_col.find('a')
                link_parts = manga_link.get('href').split('/')
                # of the form: /manga/1/Cowboy_Bebop
                manga = self.session.manga(int(link_parts[4])).set({'title': manga_link.text})
                role = info_col.find('.//small').text
                character_info['mangaography'][manga] = role
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            temp = info_panel_first.xpath("./text()")
            if len(temp) > 0:
                needle = None
                for n in temp:
                    ns = str(n)
                    if "Favorites" in str(n):
                        needle = ns
                        break
                if needle is None:
                    character_info['num_favorites'] = 0
                else:
                    num_favorites_node = needle
                    character_info['num_favorites'] = int(num_favorites_node.strip().split(': ')[1].replace(',', ''))
            else:
                character_info['num_favorites'] = 0
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return character_info

    def parse(self, character_page):
        """Parses the DOM and returns character attributes in the main-content area.

        :type character_page: :class:`lxml.html.HtmlElement`
        :param character_page: MAL character page's DOM

        :rtype: dict
        :return: Character attributes.

        """
        character_info = self.parse_sidebar(character_page)

        second_col = character_page.find(".//div[@id='content']//table[1]//tr[1]/td[2]")
        name_elt = second_col.find(".//div[@class='normal_header']")

        try:
            name_jpn_node = name_elt.find('.//small')
            if name_jpn_node is not None:
                character_info['name_jpn'] = name_jpn_node.text[1:-1]
            else:
                character_info['name_jpn'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            character_info['name'] = name_elt.text.rstrip()
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            character_info['description'] = "".join(name_elt.xpath("./following-sibling::text()")).strip()
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            character_info['voice_actors'] = {}
            voice_actors_header = second_col.xpath(".//div[text()[contains(.,'Voice Actors')]]")[0]
            if voice_actors_header is not None:
                voice_actors_tables = voice_actors_header.xpath("./following-sibling::table")
                for voice_actors_table in voice_actors_tables:
                    for row in voice_actors_table.findall('tr'):
                        # second column has va info.
                        info_col = row.find('./td[2]')
                        voice_actor_link = info_col.find('.//a')
                        name = ' '.join(reversed(voice_actor_link.text.split(', ')))
                        link_parts = voice_actor_link.get('href').split('/')
                        # of the form: /people/82/Romi_Park
                        if "myanimelist.net" in voice_actor_link.get('href'):
                            person = self.session.person(int(link_parts[4])).set({'name': name})
                        else:
                            person = self.session.person(int(link_parts[4])).set({'name': name})
                        language = info_col.find('.//small').text
                        character_info['voice_actors'][person] = language
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return character_info

    def parse_favorites(self, favorites_page):
        """Parses the DOM and returns character favorites attributes.

        :type favorites_page: :class:`lxml.html.HtmlElement`
        :param favorites_page: MAL character favorites page's DOM

        :rtype: dict
        :return: Character favorites attributes.

        """
        character_info = self.parse_sidebar(favorites_page)
        second_col = favorites_page.find(".//div[@id='content']//table//tr/td[2]")

        try:
            character_info['favorites'] = []
            favorite_links = second_col.findall('a')
            for link in favorite_links:
                # of the form /profile/shaldengeki
                character_info['favorites'].append(self.session.user(username=link.text))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return character_info

    def parse_pictures(self, picture_page):
        """Parses the DOM and returns character pictures attributes.

        :type picture_page: :class:`lxml.html.HtmlElement`
        :param picture_page: MAL character pictures page's DOM

        :rtype: dict
        :return: character pictures attributes.

        """
        character_info = self.parse_sidebar(picture_page)
        second_col = picture_page.find(".//div[@id='content']//table[1]//tr[1]/td[2]")

        if second_col is None:
            character_info['pictures'] = []
            return character_info

        try:
            picture_table = second_col.find('.//table')
            character_info['pictures'] = []
            if picture_table is not None:
                character_info['pictures'] = [img.get('data-src') for img in picture_table.findall('.//img')]
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return character_info

    def parse_clubs(self, clubs_page):
        """Parses the DOM and returns character clubs attributes.

        :type clubs_page: :class:`lxml.html.HtmlElement`
        :param clubs_page: MAL character clubs page's DOM

        :rtype: dict
        :return: character clubs attributes.

        """
        character_info = self.parse_sidebar(clubs_page)
        second_col = clubs_page.find(".//div[@id='content']//table[1]//tr[1]/td[2]")

        try:
            character_info['clubs'] = []
            clubs_header = second_col.xpath(".//h2[text()[contains(.,'Related Clubs')]]")[0]

            if clubs_header is not None:
                lines = clubs_header.xpath(
                    "./following-sibling::div[@class='borderClass' and text()[not(contains(.,'No related clubs'))]]")
                for line in lines:
                    curr_elt = line
                    link = curr_elt.find('.//a')
                    club_id = int(re.match(r'/clubs\.php\?cid=(?P<id>[0-9]+)', link.get('href')).group('id'))
                    num_members = int(
                                re.match(r'(?P<num>[0-9]+) members', curr_elt.find('.//small').text).group('num'))
                    character_info['clubs'].append(
                                self.session.club(club_id).set({'name': link.text, 'num_members': num_members}))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return character_info

    def load(self):
        """Fetches the MAL character page and sets the current character's attributes.

        :rtype: :class:`.Character`
        :return: Current character object.

        """
        character = self.session.get('https://myanimelist.net/character/' + str(self.id)).text
        self.set(self.parse(utilities.get_clean_dom(character)))
        return self

    def load_favorites(self):
        """Fetches the MAL character favorites page and sets the current character's favorites attributes.

        :rtype: :class:`.Character`
        :return: Current character object.

        """
        character = self.session.get(
                'https://myanimelist.net/character/' + str(self.id) + '/' + utilities.urlencode(
                        self.name) + '/favorites').text
        self.set(self.parse_favorites(utilities.get_clean_dom(character)))
        return self

    def load_pictures(self):
        """Fetches the MAL character pictures page and sets the current character's pictures attributes.

        :rtype: :class:`.Character`
        :return: Current character object.

        """
        character = self.session.get(
                'https://myanimelist.net/character/' + str(self.id) + '/' + utilities.urlencode(
                        self.name) + '/pictures').text
        self.set(self.parse_pictures(utilities.get_clean_dom(character)))
        return self

    def load_clubs(self):
        """Fetches the MAL character clubs page and sets the current character's clubs attributes.

        :rtype: :class:`.Character`
        :return: Current character object.

        """
        character = self.session.get(
                'https://myanimelist.net/character/' + str(self.id) + '/' + utilities.urlencode(
                        self.name) + '/clubs').text
        self.set(self.parse_clubs(utilities.get_clean_dom(character)))
        return self

    @property
    @loadable('load')
    def name(self):
        """Character name.
        """
        return self._name

    @property
    @loadable('load')
    def full_name(self):
        """Character's full name.
        """
        return self._full_name

    @property
    @loadable('load')
    def name_jpn(self):
        """Character's Japanese name.
        """
        return self._name_jpn

    @property
    @loadable('load')
    def description(self):
        """Character's description.
        """
        return self._description

    @property
    @loadable('load')
    def voice_actors(self):
        """Voice actor dict for this character, with :class:`myanimelist.person.Person` objects as keys and the language as values.
        """
        return self._voice_actors

    @property
    @loadable('load')
    def animeography(self):
        """Anime appearance dict for this character, with :class:`myanimelist.anime.Anime` objects as keys and the type of role as values, e.g. 'Main'
        """
        return self._animeography

    @property
    @loadable('load')
    def mangaography(self):
        """Manga appearance dict for this character, with :class:`myanimelist.manga.Manga` objects as keys and the type of role as values, e.g. 'Main'
        """
        return self._mangaography

    @property
    @loadable('load')
    def num_favorites(self):
        """Number of users who have favourited this character.
        """
        return self._num_favorites

    @property
    @loadable('load_favorites')
    def favorites(self):
        """List of users who have favourited this character.
        """
        return self._favorites

    @property
    @loadable('load')
    def picture(self):
        """URL of primary picture for this character.
        """
        return self._picture

    @property
    @loadable('load_pictures')
    def pictures(self):
        """List of picture URLs for this character.
        """
        return self._pictures

    @property
    @loadable('load_clubs')
    def clubs(self):
        """List of clubs relevant to this character.
        """
        return self._clubs
