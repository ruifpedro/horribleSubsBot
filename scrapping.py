import json
import os
from collections import OrderedDict

import regex as re
import requests
from ghost import Ghost, TimeoutError
from lxml import html

global links
links = dict()
links["main"]="http://horriblesubs.info"
links["schedule"]=links["main"]+"/release-schedule"
links["shows"]=links["main"]+"/shows"
links["season"]=links["main"]+"/current-season"

def getPageTree(pageType="main"):
	link = links[pageType]
	page = requests.get(link)
	return html.fromstring(page.content)

def getPage(pageType="main"):
	link = links[pageType]
	return requests.get(link)

def orderTimeTable(jsonData):
	auxDict = dict()
	for weekday in jsonData:
		weeklist = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "To be scheduled"]
		
		shows = jsonData[weekday]

		sortedShows = sorted(shows.items(), key=lambda t : t[1]["time"])
		auxDict[weeklist.index(weekday)] = sortedShows

	sortedDict = OrderedDict()
	for i, day in enumerate(weeklist):
		sortedDict[day] = auxDict[i]
	
	return sortedDict

def extractTimeTable():
	sp = getPageTree("schedule")

	weekdaysEle = sp.xpath("//h2[@class=\"weekday\"]")

	timeTable = dict()
	for element in weekdaysEle:

		value = element.text
		pred = "//h2[@class=\"weekday\" and text()=\""+value+"\"]/following::table[1]"

		tables = sp.xpath(pred)
		for table in tables:
			slots = table.xpath("./tr")
			dayShows=dict()
			for slot in slots:
				sPSNode = slot.xpath("./td[@class=\"schedule-page-show\"]/a")
				sTNode = slot.xpath("./td[@class=\"schedule-time\"]")[0]

				showHref = ""
				showName = ""

				if len(sPSNode) > 0:
					getA = sPSNode[0]
					showHref = getA.get("href")
					showName = getA.text

				showTime = sTNode.text
				showLink = links["main"] + showHref

				showInfo = dict()
				showInfo["name"] = showName
				showInfo["time"] = showTime
				showInfo["link"] = showLink

				dayShows[showName] = showInfo
		timeTable[value] = dayShows
	return orderTimeTable(timeTable)

def getShowsList():
	tree = getPageTree("shows")
	pred = "//div[@class=\"shows-wrapper\"]/div[@class=\"ind-show linkful\"]/following::a[1]"
	shows = tree.xpath(pred)
	
	showList = list()
	for show in shows:
		showHref = show.get("href")
		showLink = links["main"] + showHref
		#showName = show.get("title")
		showName = show.text
		
		showInfo = dict()
		showInfo["name"] = showName
		showInfo["link"] = showLink
		
		showList.append(showInfo)
	return showList

def getCurrentSeasonShowsList():
	tree = getPageTree("season")
	pred = "//div[@class=\"shows-wrapper\"]/div[@class=\"ind-show linkful\"]/following::a[1]"
	shows = tree.xpath(pred)
	
	showList = list()
	for show in shows:
		showHref = show.get("href")
		showLink = links["main"] + showHref
		#showName = show.get("title")
		showName = show.text
		
		showInfo = dict()
		showInfo["name"] = showName
		showInfo["link"] = showLink
		
		showList.append(showInfo)
	return showList

def getReleaseInfo(session, showLink):
	# page = requests.get(showLink)
	# tree = html.fromstring(page.content)
	#
	# #------
	# # page = download.Download().get(showLink)
	# # tree = html.fromstring(page.content)
	# #------
	#
	# pred = "//div[@class=\"hs-shows\"]"
	# showsParent = tree.xpath(pred)
	# ghost = Ghost()
	# session = ghost.start()
	page = None
	while page is None:
		try:
			page = session.open(showLink)
		except TimeoutError:
			pass

	# for i in range(1):
	# 	session.evaluate('document.getElementsByClassName(\'morebutton\')[0].click()')

	# res_links = session.evaluate('document.getElementsByClassName(\'res-link\')')[0]
	#
	# for i in range(len(res_links)):
	# 	session.evaluate('document.getElementsByClassName(\'res-link\')['+str(i)+'].click()')

	result = session.evaluate("document;")

	# result = session.evaluate(
	# 	"for(var i=0; i < 10; i++) document.getElementsByClassName('morebutton')[i].click();var l = document.getElementsByClassName('res-link').length;for(var j=0; j < l; j++) document.getElementsByClassName('res-link')[j].click();document;"
	# )

	# session.exit()
	# ghost.exit()

	# inner = result[0]["0"]["innerHTML"]
	inner = result[0]['all']['0']['innerHTML']

	tree = html.fromstring(inner)
	# pred = "//div[@class=\"hs-shows\"]"
	pred = "//table[@class=\"release-info\"]/tbody/tr"
	showsParent = tree.xpath(pred)

	# print(len(showsParent))
	episodes = list()
	for child in showsParent:
		# print(child.tag)
		# print(child.attrib)
		# print(etree.tostring(child, pretty_print=True))
		entry_id= child.attrib['id']
		pred_rls_label = "//table[@class=\"release-info\"]/tbody/tr[@id=\""+entry_id+"\"]/td[@class=\"rls-label\"]"
		rls_label = tree.xpath(pred_rls_label)
		entry_text = rls_label[0].text

		release_links_tag = "release-links"
		quality_sufixes = ["-480p", "-720p", "-1080p"]
		e = dict()
		for sufix in quality_sufixes:
			class_name = release_links_tag +" "+ entry_id + sufix
			pred_link = "//div[@class=\""+class_name+"\"]/table/tbody/tr/td/span/a"
			dl_links_tr = tree.xpath(pred_link)

			dls = list()
			for dl_link in dl_links_tr:
				dl_href = dl_link.attrib["href"]
				dl_title = dl_link.attrib["title"]
				dl_text = dl_link.text
				dl = dict()
				dl["link"] = dl_href
				dl["title"] = dl_title
				dl["text"] = dl_text
				dls.append(dl)
			# e[class_name] = dls
			e[sufix.replace("-", "")] = dls
		# \(([\d]+)\/([\d]+)\/([\d]+)\)\s([[:print:]|]*)\s-\s([\d]+)
		entry_text_regex = "\(([\d]+)\/([\d]+)\/([\d]+)\)\s([\p{ASCII}&&\p{Letter}]*)\s-\s([\d]+)"
		m = re.search(entry_text_regex, entry_text)
		e_day = ""
		e_month = ""
		e_year = ""
		e_title = ""
		e_num = ""
		if m is not None:
			e_day = m.group(1)
			e_month = m.group(2)
			e_year = m.group(3)
			e_title = m.group(4)
			e_num = m.group(5)

		episode = dict()
		episode["id"] = entry_id
		# episode["text"] = entry_text
		ep_info = dict()
		ep_info["title"] = e_title
		ep_info["date"] = e_day +"/"+e_month+"/"+e_year
		ep_info["num"] = e_num
		episode["episode"] = ep_info
		episode["downloads"] = e
		# episodes[entry_id] = episode
		episodes.append(episode)

	showDict = dict()
	showDict["id"] = showLink.split("/")[-1]
	showDict["episodes"] = episodes
	return showDict

def findShow(name, showList):
	return list(filter(lambda x: name.lower() in x["name"].lower(), showList))

'''

TESTING ZONE

'''


timeTable = extractTimeTable()
showList = getShowsList()
seasonShowList = getCurrentSeasonShowsList()

show = findShow("smartphone", seasonShowList)[0]

ghost = Ghost()
sess = ghost.start()

info = getReleaseInfo(sess, show["link"])


with open("showInfo.json", "w") as f:
	jsonData = json.dumps(info, indent=4, sort_keys=True)
	f.write(jsonData)

with open("timeTable.json", "w") as f:
	jsonData = json.dumps(timeTable, indent=4, sort_keys=False)
	f.write(jsonData)

with open("showsList.json", "w") as f:
	jsonData = json.dumps(showList, indent=4, sort_keys=False)
	f.write(jsonData)

with open("seasonShowList.json", "w") as f:
	jsonData = json.dumps(seasonShowList, indent=4, sort_keys=False)
	f.write(jsonData)

if not os.path.exists("./shows"):
	os.makedirs("./shows")

for show in showList:
	name = show["name"]
	filename = str(show["link"]).split('/')[-1]
	dirname = "shows"

	find = findShow(name, showList)
	if len(find) > 0:
		info = getReleaseInfo(sess, find[0]["link"])
		with open(dirname+"/"+filename+".json", "w") as f:
			jsonData = json.dumps(info, indent=4, sort_keys=True)
			f.write(jsonData)

sess.exit()
ghost.exit()