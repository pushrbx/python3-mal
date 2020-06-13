#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib.request, urllib.parse, urllib.error

from . import utilities
from .base import Base, MalformedPageError, InvalidBaseError, loadable


class MalformedUserPageError(MalformedPageError):
    """Indicates that a user-related page on MAL has irreparably broken markup in some way.
    """
    pass


class InvalidUserError(InvalidBaseError):
    """Indicates that the user requested does not exist on MAL.
    """
    pass


class User(Base):
    """Primary interface to user resources on MAL.
    """
    _id_attribute = "username"

    @staticmethod
    def find_username_from_user_id(session, user_id):
        """Look up a MAL username's user ID.

        :type session: :class:`myanimelist.session.Session`
        :param session: A valid MAL session.

        :type user_id: int
        :param user_id: The user ID for which we want to look up a username.

        :raises: :class:`.InvalidUserError`

        :rtype: str
        :return: The given user's username.
        """
        comments_page = session.get(
                'https://myanimelist.net/comments.php?' + urllib.parse.urlencode({'id': int(user_id)})).text
        comments_page = utilities.get_clean_dom(comments_page)
        username_elt = comments_page.find('.//h1')
        if "'s Comments" not in username_elt.text:
            raise InvalidUserError(user_id, message="Invalid user ID given when looking up username")
        return username_elt.text.replace("'s Comments", "")

    def __init__(self, session, username):
        """Creates a new instance of User.

        :type session: :class:`myanimelist.session.Session`
        :param session: A valid MAL session
        :type username: str
        :param username: The desired user's username on MAL

        :raises: :class:`.InvalidUserError`

        """
        super(User, self).__init__(session)
        self.username = username
        if not isinstance(self.username, str) or len(self.username) < 1:
            raise InvalidUserError(self.username)
        self._id = None
        self._picture = None
        self._favorite_anime = None
        self._favorite_manga = None
        self._favorite_characters = None
        self._favorite_people = None
        self._last_online = None
        self._gender = None
        self._birthday = None
        self._location = None
        self._website = None
        self._join_date = None
        self._access_rank = None
        self._anime_list_views = None
        self._manga_list_views = None
        self._num_comments = None
        self._num_forum_posts = None
        self._last_list_updates = None
        self._about = None
        self._anime_stats = None
        self._manga_stats = None
        self._reviews = None
        self._recommendations = None
        self._clubs = None
        self._friends = None

    def parse_sidebar(self, user_page):
        """Parses the DOM and returns user attributes in the sidebar.

        :type user_page: :class:`lxml.html.HtmlElement`
        :param user_page: MAL user page's DOM

        :rtype: dict
        :return: User attributes

        :raises: :class:`.InvalidUserError`, :class:`.MalformedUserPageError`
        """
        user_info = {}

        # if MAL says the series doesn't exist, raise an InvalidUserError.
        if not self._validate_page(user_page):
            raise InvalidUserError(self.id)

        # parse general details.
        general_detail_ul = user_page.xpath("//ul[@class='user-status border-top pb8 mb4']")
        if len(general_detail_ul) > 0:
            general_detail_ul = general_detail_ul[0]
        else:
            raise MalformedUserPageError('Cant find general details ul element.', user_page)

        last_online_elt = general_detail_ul.xpath(".//span[text()[contains(.,'Last Online')]]")[0]
        if last_online_elt is not None:
            try:
                last_online_elt = last_online_elt.xpath("./following-sibling::span")[0]
                if last_online_elt is not None:
                    user_info['last_online'] = utilities.parse_profile_date(last_online_elt.text)
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            user_info['gender'] = None
            try:
                temp = general_detail_ul.xpath(".//span[text()[contains(.,'Gender')]]")
                if len(temp) > 0:
                    gender_tag = temp[0]
                    user_info['gender'] = gender_tag.xpath("./following-sibling::span")[0].text
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            user_info['birthday'] = None
            try:
                temp = general_detail_ul.xpath(".//span[text()[contains(.,'Birthday')]]")
                if len(temp) > 0:
                    birthday = temp[0]
                    user_info['birthday'] = utilities.parse_profile_date(
                            birthday.xpath("./following-sibling::span")[0].text)
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            user_info['location'] = None
            try:
                temp = general_detail_ul.xpath(".//span[text()[contains(.,'Location')]]")
                if len(temp) > 0:
                    location = temp[0]
                    user_info['location'] = location.xpath("./following-sibling::span")[0].text
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            user_info['website'] = None
            try:
                temp = user_page.xpath(
                        "//h4[contains(text(),'Also Available at')]")
                if len(temp) > 0:
                    website = temp[0]
                else:
                    website = None
                if website is not None:
                    user_info['website'] = [{"name": x.text, "link": x.get("href")} for x in
                                            website.xpath("./following-sibling::div[1]/a")]
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            user_info['join_date'] = None
            try:
                join_date = general_detail_ul.xpath(".//span[text()[contains(.,'Joined')]]")[0]
                if join_date is not None:
                    user_info['join_date'] = utilities.parse_profile_date(
                            join_date.xpath("./following-sibling::span")[0].text)
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

        try:
            username_tag = user_page.find(".//div[@id='contentWrapper']//h1[1]")
            if username_tag is not None and username_tag.find('.//div') is not None:
                # otherwise, raise a MalformedUserPageError.
                raise MalformedUserPageError(self.username, user_page, message="Could not find title div")
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        info_panel_first = user_page.find(".//div[@id='content']//div[@class='user-profile']")

        try:
            picture_tag = info_panel_first.find('.//img')
            if picture_tag is not None:
                user_info['picture'] = picture_tag.get('data-src')
            else:
                user_info['picture'] = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            # the user ID is always present in report link.
            user_info['id'] = -1
            temp = user_page.xpath("//a[@class='header-right mt4 mr0']")
            if len(temp) > 0:
                all_comments_link = temp[0]
                all_comments_link_parts = all_comments_link.get('href').split('&id=')
                if len(all_comments_link_parts) > 1:
                    user_info['id'] = int(all_comments_link.get('href').split('&id=')[1])
                    self._id = user_info['id']
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return user_info

    def parse(self, user_page):
        """Parses the DOM and returns user attributes in the main-content area.

        :type user_page: :class:`lxml.html.HtmlElement`
        :param user_page: MAL user page's DOM

        :rtype: dict
        :return: User attributes.

        """
        user_info = self.parse_sidebar(user_page)

        infobar_headers = utilities.css_select("div.container-right div.user-favorites h5.mb8", user_page)
        if len(infobar_headers) > 0:
            try:
                favorite_anime_header = infobar_headers[0]
                if 'Anime' in favorite_anime_header.text:
                    user_info['favorite_anime'] = []
                    favorite_anime_ul = favorite_anime_header.getnext()
                    if favorite_anime_ul.tag == 'ul':
                        for row in favorite_anime_ul.findall('./li'):
                            cols = row.findall('./div')
                            anime_link = cols[1].find('.//a')
                            link_parts = anime_link.get('href').split('/')
                            if "myanimelist.net" in anime_link.get('href'):
                                # of the form https://myanimelist.net/anime/467/Ghost_in_the_Shell:_Stand_Alone_Complex
                                user_info['favorite_anime'].append(
                                        self.session.anime(int(link_parts[4])).set({'title': anime_link.text}))
                            else:
                                user_info['favorite_anime'].append(
                                        self.session.anime(int(link_parts[2])).set({'title': anime_link.text}))
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            try:
                favorite_manga_header = infobar_headers[1]
                if 'Manga' in favorite_manga_header.text:
                    user_info['favorite_manga'] = []
                    favorite_manga_ul = favorite_manga_header.getnext()
                    if favorite_manga_ul.tag == 'ul':
                        for row in favorite_manga_ul.findall('./li'):
                            cols = row.findall('./div')
                            manga_link = cols[1].find('.//a')
                            link_parts = manga_link.get('href').split('/')
                            if "myanimelist.net" in manga_link.get('href'):
                                # of the form https://myanimelist.net/manga/467/Ghost_in_the_Shell:_Stand_Alone_Complex
                                user_info['favorite_manga'].append(
                                        self.session.manga(int(link_parts[4])).set({'title': manga_link.text}))
                            else:
                                user_info['favorite_manga'].append(
                                        self.session.manga(int(link_parts[2])).set({'title': manga_link.text}))
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            try:
                favorite_character_header = infobar_headers[2]
                if 'Characters' in favorite_character_header.text:
                    user_info['favorite_characters'] = {}
                    favorite_character_ul = favorite_character_header.getnext()
                    if favorite_character_ul.tag == 'ul':
                        for row in favorite_character_ul.findall('./li'):
                            cols = row.findall('./div')
                            character_link = cols[1].find('.//a')
                            link_parts = character_link.get('href').split('/')
                            if "myanimelist.net" in character_link.get('href'):
                                # of the form https://myanimelist.net/character/467/Ghost_in_the_Shell
                                character = self.session.character(int(link_parts[4])).set(
                                        {'title': character_link.text})
                            else:
                                character = self.session.character(int(link_parts[2])).set(
                                        {'title': character_link.text})

                            media_link = cols[1].find('.//span').find('a')
                            link_parts = media_link.get('href').split('/')
                            # of the form /anime|manga/467 or None when link is missing. E.g. for https://myanimelist.net/character/8841/Miriya_Sterling
                            if link_parts[2] == '':
                                anime = None
                            else:
                                anime = getattr(self.session, link_parts[1])(int(link_parts[2])).set(
                                        {'title': media_link.text})

                            user_info['favorite_characters'][character] = anime
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

            try:
                favorite_people_header = infobar_headers[3]
                if 'People' in favorite_people_header.text:
                    user_info['favorite_people'] = []
                    favorite_person_ul = favorite_people_header.getnext()
                    if favorite_person_ul.tag == 'ul':
                        for row in favorite_person_ul.findall('./li'):
                            cols = row.findall('./div')
                            person_link = cols[1].find('.//a')
                            link_parts = person_link.get('href').split('/')
                            if "myanimelist.net" in person_link.get('href'):
                                # of the form /person/467/Ghost_in_the_Shell:_Stand_Alone_Complex
                                user_info['favorite_people'].append(
                                        self.session.person(int(link_parts[4])).set({'title': person_link.text}))
                            else:
                                user_info['favorite_people'].append(
                                        self.session.person(int(link_parts[2])).set({'title': person_link.text}))
            except:
                if not self.session.suppress_parse_exceptions:
                    raise

        # todo: later
        # try:
        #     access_rank = general_table.find('td', text='Access Rank')
        #     if access_rank:
        #         user_info['access_rank'] = access_rank.findNext('td').text
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise
        #
        # try:
        #     anime_list_views = general_table.find('td', text='Anime List Views')
        #     if anime_list_views:
        #         user_info['anime_list_views'] = int(anime_list_views.findNext('td').text.replace(',', ''))
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise
        #
        # try:
        #     manga_list_views = general_table.find('td', text='Manga List Views')
        #     if manga_list_views:
        #         user_info['manga_list_views'] = int(manga_list_views.findNext('td').text.replace(',', ''))
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise
        #
        # try:
        #     num_comments = general_table.find('td', text='Comments')
        #     if num_comments:
        #         user_info['num_comments'] = int(num_comments.findNext('td').text.replace(',', ''))
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise
        #
        # try:
        #     num_forum_posts = general_table.find('td', text='Forum Posts')
        #     if num_forum_posts:
        #         user_info['num_forum_posts'] = int(
        #                 num_forum_posts.findNext('td').text.replace(" (Find All)", "").replace(',', ''))
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise

        try:
            # last list updates.
            user_info['last_list_updates'] = {}
            for elem in utilities.css_select(
                    "div#statistics.user-statistics div.user-statistics-stats div.statistics-updates a.image",
                    user_page):
                list_update = {}
                link_parts = elem.get("href").split("/")
                if "myanimelist.net" in elem.get("href"):
                    if link_parts[3] == 'anime':
                        media = self.session.anime(int(link_parts[4])).set({'title': elem.text})
                    else:
                        media = self.session.manga(int(link_parts[4])).set({'title': elem.text})
                else:
                    if link_parts[1] == 'anime':
                        media = self.session.anime(int(link_parts[2])).set({'title': elem.text})
                    else:
                        media = self.session.manga(int(link_parts[2])).set({'title': elem.text})

                # div.data div.fn-grey2
                data_container = elem.getnext().find("./div[2]")
                if data_container is None:
                    temp = None
                else:
                    temp = data_container.find("./span[1]")
                if temp is not None:
                    progress = int(temp.text)
                    el_text_matches = temp.xpath("./following-sibling::text()")
                    if len(el_text_matches) > 0:
                        total_match = re.match(r'/(?P<total>[0-9]+)', el_text_matches[0])
                        if total_match is not None:
                            total_match = total_match.groupdict()
                        if total_match is None:
                            list_update["total"] = None
                        else:
                            list_update["total"] = int(total_match["total"].replace("/", ""))
                        status = temp.get("class").split(" ")[-1]
                        status = status[0].upper() + status[1:]
                        list_update["status"] = status
                        list_update["progress"] = progress
                        time_tag = elem.getnext().find("./div[1]/span[1]")
                        list_update["time"] = utilities.parse_profile_date(time_tag.text)
                        user_info['last_list_updates'][media] = list_update
                        media = None
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        # all the statistics
        try:
            stats_divs = utilities.css_select("div#statistics.user-statistics div.user-statistics-stats div.stats",
                                              user_page)
            for elem in stats_divs:
                temp = elem.get("class")
                media = temp.split(" ")[1]
                user_info['%s_stats' % media] = {}

                # mean score and days
                for val_name_tag in elem.findall("./div[1]/div/span[1]"):
                    extracted_str_val = val_name_tag.xpath("./following-sibling::text()")[0].strip().replace(",", "")
                    if extracted_str_val == '':
                        extracted_str_val = val_name_tag.getparent().find('./span[2]').text.strip().replace(",", "")

                    value = float(extracted_str_val)
                    user_info['%s_stats' % media][val_name_tag.text.strip().replace(":", "")] = value

                # the rest
                for li in elem.findall("./div[3]/ul/li"):
                    temp = li.xpath("./a[contains(@class,'circle')] | ./span[contains(@class,'fn-grey2')]")
                    name_tag = temp[0].text
                    user_info['%s_stats' % media][name_tag] = int(
                            li.xpath("./span[contains(@class,'fl-r')]")[0].text.strip().replace(",", ""))
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        try:
            temp = utilities.css_select("div.profile-about-user div.word-break", user_page)
            if len(temp) != 0:
                elem = temp[0]
                user_info['about'] = elem.text.strip()
        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return user_info

    def parse_reviews(self, reviews_page):
        """Parses the DOM and returns user reviews attributes.

        :type reviews_page: :class:`lxml.html.HtmlElement`
        :param reviews_page: MAL user reviews page's DOM

        :rtype: dict
        :return: User reviews attributes.

        """
        user_info = self.parse_sidebar(reviews_page)
        user_info['reviews'] = {}

        try:
            review_containers = utilities.css_select("div#content div.borderDark", reviews_page)
            for review_container in review_containers:
                review_info = {}
                media_link = review_container.find("./div[1]/div[1]/a[1]")
                link_parts = media_link.get('href').split('/')
                if "myanimelist.net" not in media_link.get("href"):
                    media = getattr(self.session, link_parts[1])(int(link_parts[2])).set({'title': media_link.text})
                else:
                    media = getattr(self.session, link_parts[3])(int(link_parts[4])).set({'title': media_link.text})

                helpful_span = review_container.find("./div[1]/div[2]/span")
                review_info['people_helped'] = 0
                temp = helpful_span.find("./strong/span")

                if temp is not None:
                    review_info['people_helped'] = int(temp.text.strip())

                review_info['people_total'] = 0
                review_info['media_consumed'] = 0
                review_info['media_total'] = None
                review_info['rating'] = -1
                review_info['text'] = ""
                media_consumed_tag = review_container.find("./div[1]/div[2]/div[1]")
                if media_consumed_tag is not None:
                    media_consumed_text = media_consumed_tag.text
                    consumption_match = re.match(r'(?P<media_consumed>[0-9]+) of (?P<media_total>[0-9?]+)',
                                                 media_consumed_text).groupdict()
                    review_info['media_consumed'] = int(consumption_match['media_consumed'])
                    if consumption_match['media_total'] == '?':
                        review_info['media_total'] = None
                    else:
                        review_info['media_total'] = int(consumption_match['media_total'])

                rating_tag = review_container.find("./div[1]/div[3]/div")
                temp = rating_tag.xpath("./text()")
                if len(temp) > 0:
                    text = temp[0].strip().replace(":", "")[1:]
                    review_info['rating'] = int(text)

                temp = review_container.find("./div[2]")
                if temp is not None:
                    review_info['text'] = "".join(temp.find("div").getnext().getnext().xpath(
                            "./following-sibling::text() | ./following-sibling::span/text()")).strip()

                user_info['reviews'][media] = review_info

        except:
            if not self.session.suppress_parse_exceptions:
                raise

        return user_info

    def parse_recommendations(self, recommendations_page):
        """Parses the DOM and returns user recommendations attributes.

        :type recommendations_page: :class:`lxml.html.HtmlElement`
        :param recommendations_page: MAL user recommendations page's DOM

        :rtype: dict
        :return: User recommendations attributes.

        """
        user_info = self.parse_sidebar(recommendations_page)
        # second_col = recommendations_page.find('div', {'id': 'content'}).find('table').find('tr').find_all('td',
        #                                                                                                    recursive=False)[
        #     1]
        #
        # try:
        #     recommendations = second_col.find_all("div", {"class": "spaceit borderClass"})
        #     if recommendations:
        #         user_info['recommendations'] = {}
        #         for row in recommendations[1:]:
        #             anime_table = row.find('table')
        #             animes = anime_table.find_all('td')
        #             liked_media_link = animes[0].find('a', recursive=False)
        #             link_parts = liked_media_link.get('href').split('/')
        #             # of the form /anime|manga/64/Rozen_Maiden
        #             liked_media = getattr(self.session, link_parts[1])(int(link_parts[2])).set(
        #                     {'title': liked_media_link.text})
        #
        #             recommended_media_link = animes[1].find('a', recursive=False)
        #             link_parts = recommended_media_link.get('href').split('/')
        #             # of the form /anime|manga/64/Rozen_Maiden
        #             recommended_media = getattr(self.session, link_parts[1])(int(link_parts[2])).set(
        #                     {'title': recommended_media_link.text})
        #
        #             recommendation_text = row.find('p').text
        #
        #             recommendation_menu = row.find('div', recursive=False)
        #             utilities.extract_tags(recommendation_menu)
        #             recommendation_date = utilities.parse_profile_date(recommendation_menu.text.split(' - ')[1])
        #
        #             user_info['recommendations'][liked_media] = {link_parts[1]: recommended_media,
        #                                                          'text': recommendation_text,
        #                                                          'date': recommendation_date}
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise

        return user_info

    def parse_clubs(self, clubs_page):
        """Parses the DOM and returns user clubs attributes.

        :type clubs_page: :class:`lxml.html.HtmlElement`
        :param clubs_page: MAL user clubs page's DOM

        :rtype: dict
        :return: User clubs attributes.

        """
        user_info = self.parse_sidebar(clubs_page)
        # second_col = \
        #     clubs_page.find('div', {'id': 'content'}).find('table').find('tr').find_all('td', recursive=False)[1]
        #
        # try:
        #     user_info['clubs'] = []
        #
        #     club_list = second_col.find('ol')
        #     if club_list:
        #         clubs = club_list.find_all('li')
        #         for row in clubs:
        #             club_link = row.find('a')
        #             link_parts = club_link.get('href').split('?cid=')
        #             # of the form /clubs.php?cid=10178
        #             user_info['clubs'].append(self.session.club(int(link_parts[1])).set({'name': club_link.text}))
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise
        return user_info

    def parse_friends(self, friends_page):
        """Parses the DOM and returns user friends attributes.

        :type friends_page: :class:`lxml.html.HtmlElement`
        :param friends_page: MAL user friends page's DOM

        :rtype: dict
        :return: User friends attributes.

        """
        user_info = self.parse_sidebar(friends_page)
        # second_col = \
        #     friends_page.find('div', {'id': 'content'}).find('table').find('tr').find_all('td', recursive=False)[
        #         1]
        #
        # try:
        #     user_info['friends'] = {}
        #
        #     friends = second_col.find_all('div', {'class': 'friendHolder'})
        #     if friends:
        #         for row in friends:
        #             block = row.find('div', {'class': 'friendBlock'})
        #             cols = block.find_all('div')
        #
        #             friend_link = cols[1].find('a')
        #             friend = self.session.user(friend_link.text)
        #
        #             friend_info = {}
        #             if len(cols) > 2 and cols[2].text != '':
        #                 friend_info['last_active'] = utilities.parse_profile_date(cols[2].text.strip())
        #
        #             if len(cols) > 3 and cols[3].text != '':
        #                 friend_info['since'] = utilities.parse_profile_date(
        #                         cols[3].text.replace('Friends since', '').strip())
        #             user_info['friends'][friend] = friend_info
        # except:
        #     if not self.session.suppress_parse_exceptions:
        #         raise

        return user_info

    def load(self):
        """Fetches the MAL user page and sets the current user's attributes.

        :rtype: :class:`.User`
        :return: Current user object.

        """
        user_profile = self.session.get(
                'https://myanimelist.net/profile/' + utilities.urlencode(self.username)).text
        self.set(self.parse(utilities.get_clean_dom(user_profile)))
        return self

    def load_reviews(self):
        """Fetches the MAL user reviews page and sets the current user's reviews attributes.

        :rtype: :class:`.User`
        :return: Current user object.

        """
        page = 0
        # collect all reviews over all pages.
        review_collection = []
        while True:
            user_reviews = self.session.get('https://myanimelist.net/profile/' + utilities.urlencode(
                    self.username) + '/reviews/?' + urllib.parse.urlencode({'p': page})).text
            if user_reviews is None:
                break
            parse_result = self.parse_reviews(utilities.get_clean_dom(user_reviews))
            if page == 0:
                # only set attributes once the first time around.
                self.set(parse_result)
            if len(parse_result['reviews']) == 0:
                break
            review_collection.append(parse_result['reviews'])
            page += 1

        # merge the review collections into one review dict, and set it.
        self.set({
            'reviews': {k: v for d in review_collection for k, v in d.items()}
        })
        return self

    def load_recommendations(self):
        """Fetches the MAL user recommendations page and sets the current user's recommendations attributes.

        :rtype: :class:`.User`
        :return: Current user object.

        """
        user_recommendations = self.session.get(
                'https://myanimelist.net/profile/' + utilities.urlencode(self.username) + '/recommendations').text
        self.set(self.parse_recommendations(utilities.get_clean_dom(user_recommendations)))
        return self

    def load_clubs(self):
        """Fetches the MAL user clubs page and sets the current user's clubs attributes.

        :rtype: :class:`.User`
        :return: Current user object.

        """
        user_clubs = self.session.get(
                'https://myanimelist.net/profile/' + utilities.urlencode(self.username) + '/clubs').text
        self.set(self.parse_clubs(utilities.get_clean_dom(user_clubs)))
        return self

    def load_friends(self):
        """Fetches the MAL user friends page and sets the current user's friends attributes.

        :rtype: :class:`.User`
        :return: Current user object.

        """
        user_friends = self.session.get(
                'https://myanimelist.net/profile/' + utilities.urlencode(self.username) + '/friends').text
        self.set(self.parse_friends(utilities.get_clean_dom(user_friends)))
        return self

    @property
    @loadable('load')
    def id(self):
        """User ID.
        """
        return self._id

    @property
    @loadable('load')
    def picture(self):
        """User's picture.
        """
        return self._picture

    @property
    @loadable('load')
    def favorite_anime(self):
        """A list of :class:`myanimelist.anime.Anime` objects containing this user's favorite anime.
        """
        return self._favorite_anime

    @property
    @loadable('load')
    def favorite_manga(self):
        """A list of :class:`myanimelist.manga.Manga` objects containing this user's favorite manga.
        """
        return self._favorite_manga

    @property
    @loadable('load')
    def favorite_characters(self):
        """A dict with :class:`myanimelist.character.Character` objects as keys and :class:`myanimelist.media.Media` as values.
        """
        return self._favorite_characters

    @property
    @loadable('load')
    def favorite_people(self):
        """A list of :class:`myanimelist.person.Person` objects containing this user's favorite people.
        """
        return self._favorite_people

    @property
    @loadable('load')
    def last_online(self):
        """A :class:`datetime.datetime` object marking when this user was active on MAL.
        """
        return self._last_online

    @property
    @loadable('load')
    def gender(self):
        """This user's gender.
        """
        return self._gender

    @property
    @loadable('load')
    def birthday(self):
        """A :class:`datetime.datetime` object marking this user's birthday.
        """
        return self._birthday

    @property
    @loadable('load')
    def location(self):
        """This user's location.
        """
        return self._location

    @property
    @loadable('load')
    def website(self):
        """This user's website.
        """
        return self._website

    @property
    @loadable('load')
    def join_date(self):
        """A :class:`datetime.datetime` object marking when this user joined MAL.
        """
        return self._join_date

    @property
    @loadable('load')
    def access_rank(self):
        """This user's access rank on MAL.
        """
        return self._access_rank

    @property
    @loadable('load')
    def anime_list_views(self):
        """The number of times this user's anime list has been viewed.
        """
        return self._anime_list_views

    @property
    @loadable('load')
    def manga_list_views(self):
        """The number of times this user's manga list has been viewed.
        """
        return self._manga_list_views

    @property
    @loadable('load')
    def num_comments(self):
        """The number of comments this user has made.
        """
        return self._num_comments

    @property
    @loadable('load')
    def num_forum_posts(self):
        """The number of forum posts this user has made.
        """
        return self._num_forum_posts

    @property
    @loadable('load')
    def last_list_updates(self):
        """A dict of this user's last list updates, with keys as :class:`myanimelist.media.Media` objects, and values as dicts of attributes, e.g. {'status': str, 'episodes': int, 'total_episodes': int, 'time': :class:`datetime.datetime`}
        """
        return self._last_list_updates

    @property
    @loadable('load')
    def about(self):
        """This user's self-bio.
        """
        return self._about

    @property
    @loadable('load')
    def anime_stats(self):
        """A dict of this user's anime stats, with keys as strings, and values as numerics.
        """
        return self._anime_stats

    @property
    @loadable('load')
    def manga_stats(self):
        """A dict of this user's manga stats, with keys as strings, and values as numerics.
        """
        return self._manga_stats

    @property
    @loadable('load_reviews')
    def reviews(self):
        """A dict of this user's reviews, with keys as :class:`myanimelist.media.Media` objects, and values as dicts of attributes, e.g.

          {

            'people_helped': int,

            'people_total': int,

            'media_consumed': int,

            'media_total': int,

            'rating': int,

            'text': str,

            'date': :class:`datetime.datetime`

          }

        """
        return self._reviews

    @property
    @loadable('load_recommendations')
    def recommendations(self):
        """A dict of this user's recommendations, with keys as :class:`myanimelist.media.Media` objects, and values as dicts of attributes, e.g.

          {

            'anime|media': :class:`myanimelist.media.Media`,

            'text': str,

            'date': :class:`datetime.datetime`

          }
        """
        return self._recommendations

    @property
    @loadable('load_clubs')
    def clubs(self):
        """A list of :class:`myanimelist.club.Club` objects containing this user's club memberships.
        """
        return self._clubs

    @property
    @loadable('load_friends')
    def friends(self):
        """A dict of this user's friends, with keys as :class:`myanimelist.user.User` objects, and values as dicts of attributes, e.g.

          {

            'last_active': :class:`datetime.datetime`,

            'since': :class:`datetime.datetime`

          }
        """
        return self._friends

    def anime_list(self):
        """This user's anime list.

        :rtype: :class:`myanimelist.anime_list.AnimeList`
        :return: The desired anime list.
        """
        return self.session.anime_list(self.username)

    def manga_list(self):
        """This user's manga list.

        :rtype: :class:`myanimelist.manga_list.MangaList`
        :return: The desired manga list.
        """
        return self.session.manga_list(self.username)
