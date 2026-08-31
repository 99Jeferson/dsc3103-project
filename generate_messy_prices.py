#%%
import csv 
import random
from datetime import datetime, timedelta
random.seed(42)
#%%
base_date = datetime(2020, 1, 1)
market = ["mukono","Bwais","Nakasero","Kansanga",None]
commodity =  ["Maize","MAIZE","Beans","BEANS"]
rows = [] 
for i in range(1000):
    row = {
        "id": i if random.random() > 0.02 else i-1,
        "date": (base_date + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d") if random.random() > 0.03 else "2020-14-15",
        "market": random.choice(market),
        "commodity": random.choice(commodity),
        "price": random.randint(500, 500) if random.random() > 0.05 else -2000,
    }
    rows.append(row)
#%%
rows += rows[20:30]
with open("data/raw/prices.csv","w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames= ["id","date","market","commodity","price"])
    writer.writeheader()
    writer.writerows(rows)
# %%
