import json
from collections import OrderedDict

weeklist = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "To be scheduled"]

filename = "timeTable.json"

with open(filename, "r") as f:
	jsonData = json.load(f)

prettyJ = json.dumps(jsonData, indent=4, sort_keys=False)

d = dict()

for weekday in jsonData:
	shows = jsonData[weekday]

	xp = sorted(shows.items(), key=lambda t : t[1]["time"])
	d[weeklist.index(weekday)] = xp

nn = dict()
for i, day in enumerate(weeklist):
	nn[day] = d[i]

with open("orderded.json", "w") as f:
	f.write(json.dumps(nn, indent=4, sort_keys=False))

