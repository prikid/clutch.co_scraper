import json
from Nested2CSV import Nested2CSV

filename_jl = 'clutch2.jl'
filename_csv = 'clutch2.csv'

list=[]
with open(filename_jl) as f:
    for row in f:
        list.append(json.loads(row))


Nested2CSV(list).to_csv(filename_csv)

