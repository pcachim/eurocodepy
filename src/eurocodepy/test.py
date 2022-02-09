import ec2
import ec_base as ec
import json, os
import pandas as pd

print ("Executing ec_base\n")
db = json.loads(open(os.path.join(os.path.dirname(__file__),'eurocodes.json'),'r').read())
# pststeel = get_prestress()
pststeel = db["Eurocodes"]["Materials"]["Prestress"]
print(pststeel)

df = pd.DataFrame.from_dict(pststeel)
print(df)