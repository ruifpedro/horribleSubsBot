import logging
import threading
import time
import uuid

from pymongo import MongoClient

import scrapping


class Bot:
    def __init__(self):
        self.name = "hs-daemon-"+ str(uuid.uuid4())
        self.running = True
        self.db_timeTable_collection = "timeTable"
        self.db_seasons_collection = "seasons"
        self.db_currentSeason_collection = "currentSeason"
        self.db_shows_collection = "shows"
        self.db_mongo_ip = "localhost"
        self.db_mongo_port = 27017
        self.db_mongo_dbname = "hs"

        self.db_connector = None
        self.db = None

    def __startup(self):
        self.db_connector = MongoClient(self.db_mongo_ip, self.db_mongo_port)
        self.db = self.db_connector[self.db_mongo_dbname]

    def __run(self):
        self.__startup()

        logging.debug("Daemon started")
        while(self.running):
            dbEmpty = self.__db_isEmpty()

            if(dbEmpty == True):
                timetable = self.__getTimeTable()
                allShows = self.__getAllShowsList()
                season = self.__getSeasonList()
                self.__db_save_timetable(timetable)
                self.__db_save_allshows(allShows)
                self.__db_save_season(season)
            else:
                self.__db_check_consistency()
                db_season = self.__db_get_season()
                current_season = self.__getSeasonList()

                diffs = self.__compare_season(db_season, season)

                self.__db_update_season(season)
                time.sleep(1000)

        logging.debug("Daemon exiting")

    def __getTimeTable(self):
        return scrapping.extractTimeTable()

    def __getSeasonList(self):
        return scrapping.getCurrentSeasonShowsList()

    def __getAllShowsList(self):
        return scrapping.getShowsList()

    def __getReleaseInfo(self, showLink):
        return scrapping.getReleaseInfo(showLink)

    def __findShow(self, name, showList):
        return scrapping.findShow(name, showList)

    def start_daemon(self):
        thread = threading.Thread(name=self.name, target=self.__run())
        thread.start()
        while(thread.is_alive):
            thread.join()

    def stop_daemon(self):
        self.running = False

    def __db_isEmpty(self):
        c1 = True if self.db[self.db_currentSeason_collection].find_one() == None else False
        c2 = True if self.db[self.db_shows_collection].find_one() == None else False
        return c1 or c2

    def __db_save_timetable(self, timetable):
        self.db[self.db_timeTable_collection].insert_one(timetable)

    def __db_save_allshows(self, allShows):
        # jsonData = json.dumps(allShows, indent=4, sort_keys=False)
        # bsonData = dumps(allShows)
        self.db[self.db_shows_collection].insert_many(allShows)

    def __db_save_season(self, season):
        # jsonData = json.dumps(season, indent=4, sort_keys=False)
        # bsonData = dumps(season)
        self.db[self.db_currentSeason_collection].insert_many(season)

    def __db_check_consistency(self):
        pass

    def __db_get_season(self):
        pass

    def __db_update_season(self, season):
        pass

    def __compare_season(self, db_season, season):
        pass