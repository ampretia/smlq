import uuid
import duckdb
from queue import Empty, Queue
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

app = FastAPI()
q = {}

# create a connection to a file called 'file.db'
con = duckdb.connect('file.db')

# create a table
con.execute("CREATE TABLE IF NOT EXISTS tasks (uid TEXT NOT NULL,retries SMALLINT,	added TIMESTAMP,	assigned TIMESTAMP,	completed TIMESTAMP,	status TEXT, data TEXT, 	PRIMARY KEY (uid));")

class Item(BaseModel):
    uid: str
    payload: str 
      
class Completion(BaseModel):
    code: str
    detail: str

q['default'] = Queue()

@app.post("/queue/{qid}")
async def add( qid, data: Item):        
    print(f"qid {qid}, data {data}")

    if qid != 'default':
        raise HTTPException(status_code=404, detail="default only queue")
    try:
        data.uid = str(uuid.uuid1())
        now = datetime.now().isoformat()
        con.execute("INSERT INTO tasks VALUES(?,?,?,NULL,NULL,?,?)",[data.uid,0,now,'',data.payload])

        q[qid].put(data)
    except Exception as e:       
        print(e)
        raise HTTPException(status_code=500, detail="??")


    return data.uid
    
@app.get("/queue/{qid}")
def gettask(qid: str):   
    if qid != 'default':
        raise HTTPException(status_code=404, detail="default only queue")
    
    try:
        item = q[qid].get(block=False)
        now = datetime.now().isoformat()
        con.execute("UPDATE tasks SET assigned=$1 WHERE uid=$2",[now,item.uid])
        return item
    except Empty as e:
       raise HTTPException(status_code=404, detail="empty") 
    except Exception as e:       
       print(e)
       raise HTTPException(status_code=500, detail="??")
    
@app.post("/task/{uid}")
async def complete(uid: str,comp: Completion):
    try:
     
        now = datetime.now().isoformat()
        con.execute("UPDATE tasks SET completed=$1, status=$2 WHERE uid=$3",[now,f"{comp.code}_{comp.detail}",uid])
        return now
    except Exception as e:       
       print(e)
       raise HTTPException(status_code=500, detail="??")

@app.get("/debug")
async def root():
    results = con.execute("SELECT * FROM TASKS;").fetchall()
    for r in results:
        print(r)

    print(f"QueueSize={q['default'].qsize()}")
    

    return 

# preload the queue
results = con.execute("select * from tasks where completed is NULL;").fetchall()
for r in results:
    item = Item(uid=r[0],payload=r[6])
    q['default'].put(item)


