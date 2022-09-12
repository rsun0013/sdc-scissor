import json
import os

files = os.listdir()
#os.mkdir("./torun")
for i in files:
    if i.startswith("0"):
        print(i)
        file = json.load(open(i,"r"))
        if file["test_outcome"] == "NOT_EXECUTED":
            print(i)
            with open("./torun/{}".format(i),"w") as f:
                json.dump(file,f)

