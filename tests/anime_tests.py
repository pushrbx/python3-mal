#!/usr/bin/python
# -*- coding: utf-8 -*-

from nose.tools import *
import datetime
import os

from tests import get_proxy_settings

if "RUNENV" in os.environ and os.environ["RUNENV"] == "travis":
    from myanimelist import session
    from myanimelist import anime
else:
    try:
        from ..myanimelist import session
        from ..myanimelist import anime
    except:
        from myanimelist import session
        from myanimelist import anime


class testAnimeClass(object):
    @classmethod
    def setUpClass(self):

        self.session = session.Session(proxy_settings=get_proxy_settings())
        self.bebop = self.session.anime(1)
        self.sunrise = self.session.producer(14)
        self.bandai = self.session.producer(23)
        self.fantasia = self.session.producer(24)
        self.funimation = self.session.producer(102)
        self.action = self.session.genre(1)
        self.hex = self.session.character(94717)
        self.hex_va = self.session.person(5766)
        self.bebop_side_story = self.session.anime(5)
        self.space_tag = self.session.tag(u'space')

        self.spicy_wolf = self.session.anime(2966)
        self.kadokawa = self.session.producer(352)
        self.imagin = self.session.producer(75)
        self.romance = self.session.genre(22)
        self.holo = self.session.character(7373)
        self.holo_va = self.session.person(70)
        self.spicy_wolf_sequel = self.session.anime(6007)
        self.adventure_tag = self.session.tag(u'adventure')

        self.space_dandy = self.session.anime(20057)
        self.bones = self.session.producer(4)
        self.scifi = self.session.genre(24)
        self.toaster = self.session.character(110427)
        self.toaster_va = self.session.person(611)

        self.totoro = self.session.anime(523)
        self.gkids = self.session.producer(783)
        self.studio_ghibli = self.session.producer(21)
        self.supernatural = self.session.genre(37)
        self.satsuki = self.session.character(267)
        self.satsuki_va = self.session.person(1104)

        self.prisma = self.session.anime(18851)
        self.silver_link = self.session.producer(300)
        self.sentai_filmworks = self.session.producer(376)
        self.fantasy = self.session.genre(10)
        self.ilya = self.session.character(503)
        self.ilya_va = self.session.person(117)

        self.invalid_anime = self.session.anime(457384754)
        self.latest_anime = anime.Anime.newest(self.session)

        self.non_tagged_anime = self.session.anime(10448)
        self.mobile_suit_gundam_f91 = self.session.anime(88)

    @raises(TypeError)
    def testNoIDInvalidAnime(self):
        self.session.anime()

    @raises(TypeError)
    def testNoSessionInvalidLatestAnime(self):
        anime.Anime.newest()

    @raises(anime.InvalidAnimeError)
    def testNegativeInvalidAnime(self):
        self.session.anime(-1)

    @raises(anime.InvalidAnimeError)
    def testFloatInvalidAnime(self):
        self.session.anime(1.5)

    @raises(anime.InvalidAnimeError)
    def testNonExistentAnime(self):
        self.invalid_anime.load()

    def testLatestAnime(self):
        assert isinstance(self.latest_anime, anime.Anime)
        assert self.latest_anime.id > 20000

    def testAnimeValid(self):
        assert isinstance(self.bebop, anime.Anime)

    def testTitle(self):
        assert self.bebop.title == u'Cowboy Bebop'
        assert self.spicy_wolf.title == u'Ookami to Koushinryou'
        assert self.space_dandy.title == u'Space☆Dandy'
        assert self.prisma.title == u'Fate/kaleid liner Prisma☆Illya: Undoukai de Dance!'

    def testPicture(self):
        assert isinstance(self.spicy_wolf.picture, str)
        assert isinstance(self.space_dandy.picture, str)
        assert isinstance(self.bebop.picture, str)
        assert isinstance(self.totoro.picture, str)
        assert isinstance(self.prisma.picture, str)

    def testAlternativeTitles(self):
        assert u'Japanese' in self.bebop.alternative_titles and isinstance(self.bebop.alternative_titles[u'Japanese'],
                                                                           list) and u'カウボーイビバップ' in \
                                                                                     self.bebop.alternative_titles[
                                                                                         u'Japanese']
        assert u'English' in self.spicy_wolf.alternative_titles and isinstance(
            self.spicy_wolf.alternative_titles[u'English'], list) and u'Spice and Wolf' in \
                                                                      self.spicy_wolf.alternative_titles[u'English']
        assert u'Japanese' in self.space_dandy.alternative_titles and isinstance(
            self.space_dandy.alternative_titles[u'Japanese'], list) and u'スペース☆ダンディ' in \
                                                                        self.space_dandy.alternative_titles[u'Japanese']
        assert u'Japanese' in self.prisma.alternative_titles and isinstance(self.prisma.alternative_titles[u'Japanese'],
                                                                            list) and u'Fate/kaleid liner プリズマ☆イリヤ 運動会 DE ダンス！' in \
                                                                                      self.prisma.alternative_titles[
                                                                                          u'Japanese']

    def testTypes(self):
        assert self.bebop.type == u'TV'
        assert self.totoro.type == u'Movie'
        assert self.prisma.type == u'OVA'

    def testEpisodes(self):
        assert self.spicy_wolf.episodes == 13
        assert self.bebop.episodes == 26
        assert self.totoro.episodes == 1
        assert self.space_dandy.episodes == 13
        assert self.prisma.episodes == 1

    def testStatus(self):
        assert self.spicy_wolf.status == u'Finished Airing'
        assert self.totoro.status == u'Finished Airing'
        assert self.bebop.status == u'Finished Airing'
        assert self.space_dandy.status == u'Finished Airing'
        assert self.prisma.status == u'Finished Airing'

    def testAired(self):
        assert self.spicy_wolf.aired == (
            datetime.date(month=1, day=9, year=2008), datetime.date(month=3, day=26, year=2008))
        assert self.bebop.aired == (datetime.date(month=4, day=3, year=1998), datetime.date(month=4, day=24, year=1999))
        assert self.space_dandy.aired == (
            datetime.date(month=1, day=5, year=2014), datetime.date(month=3, day=27, year=2014))
        assert self.totoro.aired == (datetime.date(month=4, day=16, year=1988),)
        assert self.prisma.aired == (datetime.date(month=3, day=10, year=2014),)

    def testProducers(self):
        assert isinstance(self.bebop.producers, list) and len(self.bebop.producers) > 0
        assert self.bandai in self.bebop.producers
        assert isinstance(self.spicy_wolf.producers, list) and len(self.spicy_wolf.producers) > 0
        assert self.kadokawa in self.spicy_wolf.producers
        assert isinstance(self.space_dandy.producers, list) and len(self.space_dandy.producers) > 0
        assert self.bandai in self.space_dandy.producers
        assert isinstance(self.totoro.producers, list) and len(self.totoro.producers) > 0
        assert self.fantasia in self.totoro.producers
        assert isinstance(self.prisma.producers, list) and len(self.prisma.producers) >= 0
        assert self.silver_link not in self.prisma.producers

    def testGenres(self):
        assert isinstance(self.bebop.genres, list) and len(self.bebop.genres) > 0
        assert self.action in self.bebop.genres
        assert isinstance(self.spicy_wolf.genres, list) and len(self.spicy_wolf.genres) > 0
        assert self.romance in self.spicy_wolf.genres
        assert isinstance(self.space_dandy.genres, list) and len(self.space_dandy.genres) > 0
        assert self.scifi in self.space_dandy.genres
        assert isinstance(self.totoro.genres, list) and len(self.totoro.genres) > 0
        assert self.supernatural in self.totoro.genres
        assert isinstance(self.prisma.genres, list) and len(self.prisma.genres) > 0
        assert self.fantasy in self.prisma.genres

    def testRating(self):
        assert self.spicy_wolf.rating != "Rating:"
        assert self.spicy_wolf.rating is not None
        assert self.bebop.rating != "Rating:"
        assert self.bebop.rating is not None
        assert self.bebop.rating == "R - 17+ (violence & profanity)"

    def testDuration(self):
        assert self.spicy_wolf.duration.total_seconds() == 1440
        assert self.totoro.duration.total_seconds() == 5160
        assert self.space_dandy.duration.total_seconds() == 1440
        assert self.bebop.duration.total_seconds() == 1440
        assert self.prisma.duration.total_seconds() == 1500

    def testScore(self):
        assert isinstance(self.spicy_wolf.score, tuple)
        assert self.spicy_wolf.score[0] > 0 and self.spicy_wolf.score[0] < 10
        assert isinstance(self.spicy_wolf.score[1], int) and self.spicy_wolf.score[1] >= 0
        assert isinstance(self.bebop.score, tuple)
        assert self.bebop.score[0] > 0 and self.bebop.score[0] < 10
        assert isinstance(self.bebop.score[1], int) and self.bebop.score[1] >= 0
        assert isinstance(self.space_dandy.score, tuple)
        assert self.space_dandy.score[0] > 0 and self.space_dandy.score[0] < 10
        assert isinstance(self.space_dandy.score[1], int) and self.space_dandy.score[1] >= 0
        assert isinstance(self.totoro.score, tuple)
        assert self.totoro.score[0] > 0 and self.totoro.score[0] < 10
        assert isinstance(self.totoro.score[1], int) and self.totoro.score[1] >= 0
        assert self.prisma.score[0] > 0 and self.prisma.score[0] < 10
        assert isinstance(self.prisma.score[1], int) and self.prisma.score[1] >= 0

    def testRank(self):
        assert isinstance(self.spicy_wolf.rank, int) and self.spicy_wolf.rank > 0
        assert isinstance(self.bebop.rank, int) and self.bebop.rank > 0
        assert isinstance(self.space_dandy.rank, int) and self.space_dandy.rank > 0
        assert isinstance(self.totoro.rank, int) and self.totoro.rank > 0
        assert isinstance(self.prisma.rank, int) and self.prisma.rank > 0

    def testPopularity(self):
        assert isinstance(self.spicy_wolf.popularity, int) and self.spicy_wolf.popularity > 0
        assert isinstance(self.bebop.popularity, int) and self.bebop.popularity > 0
        assert isinstance(self.space_dandy.popularity, int) and self.space_dandy.popularity > 0
        assert isinstance(self.totoro.popularity, int) and self.totoro.popularity > 0
        assert isinstance(self.prisma.popularity, int) and self.prisma.popularity > 0

    def testMembers(self):
        assert isinstance(self.spicy_wolf.members, int) and self.spicy_wolf.members > 0
        assert isinstance(self.bebop.members, int) and self.bebop.members > 0
        assert isinstance(self.space_dandy.members, int) and self.space_dandy.members > 0
        assert isinstance(self.totoro.members, int) and self.totoro.members > 0
        assert isinstance(self.prisma.members, int) and self.prisma.members > 0

    def testFavorites(self):
        assert isinstance(self.spicy_wolf.favorites, int) and self.spicy_wolf.favorites > 0
        assert isinstance(self.bebop.favorites, int) and self.bebop.favorites > 0
        assert isinstance(self.space_dandy.favorites, int) and self.space_dandy.favorites > 0
        assert isinstance(self.totoro.favorites, int) and self.totoro.favorites > 0
        assert isinstance(self.prisma.favorites, int) and self.prisma.favorites > 0

    def testSynopsis(self):
        assert isinstance(self.spicy_wolf.synopsis, str) and len(
            self.spicy_wolf.synopsis) > 0 and u'Holo' in self.spicy_wolf.synopsis
        assert isinstance(self.bebop.synopsis, str) and len(self.bebop.synopsis) > 0 and u'Spike' in self.bebop.synopsis
        assert isinstance(self.space_dandy.synopsis, str) and len(
            self.space_dandy.synopsis) > 0
        assert isinstance(self.totoro.synopsis, str) and len(
            self.totoro.synopsis) > 0 and u'Satsuki' in self.totoro.synopsis
        assert isinstance(self.prisma.synopsis, str) and len(
            self.prisma.synopsis) > 0

    def testRelated(self):
        assert isinstance(self.spicy_wolf.related,
                          dict) and 'Sequel' in self.spicy_wolf.related and self.spicy_wolf_sequel in \
                                                                            self.spicy_wolf.related[u'Sequel']
        assert isinstance(self.bebop.related, dict) and 'Side story' in self.bebop.related and self.bebop_side_story in \
                                                                                               self.bebop.related[
                                                                                                   u'Side story']

    def testCharacters(self):
        assert isinstance(self.spicy_wolf.characters, dict) and len(self.spicy_wolf.characters) > 0
        assert self.holo in self.spicy_wolf.characters and self.spicy_wolf.characters[self.holo][
                                                               u'role'] == 'Main' and self.holo_va in \
                                                                                      self.spicy_wolf.characters[
                                                                                          self.holo][u'voice_actors']
        assert isinstance(self.bebop.characters, dict) and len(self.bebop.characters) > 0
        assert self.hex in self.bebop.characters and self.bebop.characters[self.hex][
                                                         u'role'] == 'Supporting' and self.hex_va in \
                                                                                      self.bebop.characters[self.hex][
                                                                                          u'voice_actors']
        assert isinstance(self.space_dandy.characters, dict) and len(self.space_dandy.characters) > 0
        assert self.toaster in self.space_dandy.characters and self.space_dandy.characters[self.toaster][
                                                                   u'role'] == 'Supporting' and self.toaster_va in \
                                                                                                self.space_dandy.characters[
                                                                                                    self.toaster][
                                                                                                    u'voice_actors']
        assert isinstance(self.totoro.characters, dict) and len(self.totoro.characters) > 0
        assert self.satsuki in self.totoro.characters and self.totoro.characters[self.satsuki][
                                                              u'role'] == 'Main' and self.satsuki_va in \
                                                                                     self.totoro.characters[
                                                                                         self.satsuki][u'voice_actors']
        assert isinstance(self.prisma.characters, dict) and len(self.prisma.characters) > 0
        assert self.ilya in self.prisma.characters and self.prisma.characters[self.ilya][
                                                           u'role'] == 'Main' and self.ilya_va in \
                                                                                  self.prisma.characters[self.ilya][
                                                                                      u'voice_actors']

    def testVoiceActors(self):
        assert isinstance(self.spicy_wolf.voice_actors, dict)
        assert len(self.spicy_wolf.voice_actors) > 0
        assert isinstance(self.spicy_wolf.voice_actors[self.holo_va], list)
        assert self.holo_va in self.spicy_wolf.voice_actors and self.spicy_wolf.voice_actors[self.holo_va][0][
                                                                    u'role'] == 'Main' and \
               self.spicy_wolf.voice_actors[self.holo_va][0][u'character'] == self.holo
        assert isinstance(self.bebop.voice_actors, dict) and len(self.bebop.voice_actors) > 0
        assert self.hex_va in self.bebop.voice_actors and self.bebop.voice_actors[self.hex_va][0][
                                                              u'role'] == 'Supporting' and \
               self.bebop.voice_actors[self.hex_va][0][u'character'] == self.hex
        assert isinstance(self.space_dandy.voice_actors, dict) and len(self.space_dandy.voice_actors) > 0
        assert self.toaster_va in self.space_dandy.voice_actors and self.space_dandy.voice_actors[self.toaster_va][0][
                                                                        u'role'] == 'Supporting' and \
               self.space_dandy.voice_actors[self.toaster_va][0][u'character'] == self.toaster
        assert isinstance(self.totoro.voice_actors, dict) and len(self.totoro.voice_actors) > 0
        assert self.satsuki_va in self.totoro.voice_actors and self.totoro.voice_actors[self.satsuki_va][0][
                                                                   u'role'] == 'Main' and \
               self.totoro.voice_actors[self.satsuki_va][0][u'character'] == self.satsuki
        assert isinstance(self.prisma.voice_actors, dict) and len(self.prisma.voice_actors) > 0
        assert self.ilya_va in self.prisma.voice_actors and self.prisma.voice_actors[self.ilya_va][0][
                                                                u'role'] == 'Main' and \
               self.prisma.voice_actors[self.ilya_va][0][u'character'] == self.ilya

    def testStaff(self):
        assert isinstance(self.spicy_wolf.staff, dict) and len(self.spicy_wolf.staff) > 0
        assert self.session.person(472) in self.spicy_wolf.staff and u'Producer' in self.spicy_wolf.staff[
            self.session.person(472)]
        assert isinstance(self.bebop.staff, dict) and len(self.bebop.staff) > 0
        assert self.session.person(12221) in self.bebop.staff and u'Inserted Song Performance' in self.bebop.staff[
            self.session.person(12221)]
        assert isinstance(self.space_dandy.staff, dict) and len(self.space_dandy.staff) > 0
        assert self.session.person(10127) in self.space_dandy.staff and all(
            x in self.space_dandy.staff[self.session.person(10127)] for x in
            [u'Theme Song Composition', u'Theme Song Lyrics', u'Theme Song Performance'])
        assert isinstance(self.totoro.staff, dict) and len(self.totoro.staff) > 0
        assert self.session.person(1870) in self.totoro.staff and all(
            x in self.totoro.staff[self.session.person(1870)] for x in [u'Director', u'Script', u'Storyboard'])
        assert isinstance(self.prisma.staff, dict) and len(self.prisma.staff) > 0
        assert self.session.person(10617) in self.prisma.staff and u'ADR Director' in self.prisma.staff[
            self.session.person(10617)]

    def testPromotionVideos(self):
        assert isinstance(self.spicy_wolf.promotion_videos, list)
        assert len(self.spicy_wolf.promotion_videos) == 1
        assert isinstance(self.bebop.promotion_videos, list)
        assert len(self.bebop.promotion_videos) > 0
        assert self.spicy_wolf.promotion_videos[0]["title"] == "PV English dub version"

    def testSource(self):
        assert self.spicy_wolf.source == u'Light novel'
        assert self.bebop.source == u'Original'
        assert self.totoro.source == u'Original'
        assert self.space_dandy.source == u'Original'
        assert self.prisma.source == u'Manga'
        assert self.mobile_suit_gundam_f91.source == u''
  
    def testLicensors(self):
        assert isinstance(self.bebop.licensors, list) and len(self.bebop.licensors) > 0
        assert self.funimation in self.bebop.licensors
        assert isinstance(self.spicy_wolf.licensors, list) and len(self.spicy_wolf.licensors) > 0
        assert self.funimation in self.spicy_wolf.licensors
        assert isinstance(self.space_dandy.licensors, list) and len(self.space_dandy.licensors) > 0
        assert self.funimation in self.space_dandy.licensors
        assert isinstance(self.totoro.licensors, list) and len(self.totoro.licensors) > 0
        assert self.gkids in self.totoro.licensors
        assert isinstance(self.prisma.licensors, list) and len(self.prisma.licensors) >= 0
        assert self.sentai_filmworks in self.prisma.licensors
        assert isinstance(self.non_tagged_anime.licensors, list) and len(self.non_tagged_anime.licensors) == 0
        assert not self.non_tagged_anime.licensors

    def testStudios(self):
        assert isinstance(self.bebop.studios, list) and len(self.bebop.studios) > 0
        assert self.sunrise in self.bebop.studios
        assert isinstance(self.spicy_wolf.studios, list) and len(self.spicy_wolf.studios) > 0
        assert self.imagin in self.spicy_wolf.studios
        assert isinstance(self.space_dandy.studios, list) and len(self.space_dandy.studios) > 0
        assert self.bones in self.space_dandy.studios
        assert isinstance(self.totoro.studios, list) and len(self.totoro.studios) > 0
        assert self.studio_ghibli in self.totoro.studios
        assert isinstance(self.prisma.studios, list) and len(self.prisma.studios) >= 0
        assert self.silver_link in self.prisma.studios
        assert isinstance(self.non_tagged_anime.studios, list) and len(self.non_tagged_anime.studios) == 0
        assert not self.non_tagged_anime.studios

    def testPremiered(self):
        assert self.spicy_wolf.premiered == u'Winter 2008'
        assert self.bebop.premiered == u'Spring 1998'
        assert self.totoro.premiered == u''
        assert self.space_dandy.premiered == u'Winter 2014'
        assert self.prisma.premiered == u''

    # def testPopularTags(self):
    #     assert len(self.bebop.popular_tags) > 0 and self.space_tag in self.bebop.popular_tags
    #     assert len(self.spicy_wolf.popular_tags) > 0 and self.adventure_tag in self.spicy_wolf.popular_tags
    #     assert len(self.non_tagged_anime.popular_tags) == 0
