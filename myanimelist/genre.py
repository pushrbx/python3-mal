#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from . import utilities
from .base import Base, MalformedPageError, InvalidBaseError, loadable


class MalformedGenrePageError(MalformedPageError):
    pass


class InvalidGenreError(InvalidBaseError):
    pass


class Genre(Base):
    def __init__(self, session, genre_id):
        super(Genre, self).__init__(session)
        self.id = genre_id
        if not isinstance(self.id, int) or int(self.id) < 1:
            raise InvalidGenreError(self.id)
        self._name = None

    def parse(self, genre_page):
        """Parses the DOM and returns genre attributes in the main-content area.

        :type genre_page: :class:`lxml.html.HtmlElement`
        :param genre_page: MAL character page's DOM

        :rtype: dict
        :return: Genre attributes.

        """
        genre_info = {}

        try:
            header = genre_page.find(".//div[@id='contentWrapper']//h1[@class='h1']")
            if header is not None:
                genre_info["name"] = header.text.split(' ')[0]
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return genre_info

    def load(self):
        genre = self.session.get('https://myanimelist.net/anime/genre/' + str(self.id)).text
        self.set(self.parse(utilities.get_clean_dom(genre)))
        pass

    @property
    @loadable('load')
    def name(self):
        return self._name
