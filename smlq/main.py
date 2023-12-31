import uuid
import duckdb
from queue import Empty, Queue
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
from .config import settings

logger.info("""
                   __     
   _________ ___  / /___ _
  / ___/ __ `__ \/ / __ `/
 (__  ) / / / / / / /_/ / 
/____/_/ /_/ /_/_/\__, /  
                    /_/               
            """)

logger.info("Using configuration:")
logger.info(settings)

# create FASTAPI instance
app = FastAPI()

# in memory set of queues
q = {}

# duckdb connection
con = None


# data model
class Item(BaseModel):
    uid: str
    payload: str


class Completion(BaseModel):
    code: str
    detail: str


# Add something to a queue
@app.post("/queue/{qid}")
async def add(qid, data: Item):
    global con
    # print(f"qid {qid}, data {data}")
    if qid not in q:
        raise HTTPException(
            status_code=404, detail="Queue not known"
        )

    try:
        data.uid = str(uuid.uuid1())
        now = datetime.now().isoformat()
        con.execute(
            f"INSERT INTO tasks VALUES(?,?,?,?,NULL,NULL,?,?)",
            [data.uid, qid, 0, now, "", data.payload],
        )

        q[qid].put(data)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="??")

    return data.uid

@app.patch("/queue/{qid}")
async def reload(qid):
    global con

    if qid not in q:
        raise HTTPException(
            status_code=404, detail="Queue not known"
        )

    try:
        results = con.execute(f"select * from tasks where completed is NULL and queue_name='{qid}';").fetchall()
        q[qid] = Queue()
        logger.info(f"Reloading queue {qid} with tasks not completed {len(results)}")
        for r in results:
            item = Item(uid=r[0], payload=r[7])          
            q[qid].put(item)

        return len(results)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="??")

    

@app.get("/reset/{qid}")
async def reset(qid):
    try:
        con.execute(f"DELETE FROM tasks WHERE queue_name='{qid}';")
        q[qid] = Queue()
        return True
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="??")


@app.get("/queue/{qid}")
def gettask(qid: str):
    if qid not in q:
        raise HTTPException(
            status_code=404, detail="Queue not known - call reset first"
        )
    try:
        item = q[qid].get(block=False)
        now = datetime.now().isoformat()
        con.execute("UPDATE tasks SET assigned=$1 WHERE uid=$2", [now, item.uid])
        return item
    except Empty as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="empty")
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="??")


@app.post("/task/{uid}")
async def complete(uid: str, comp: Completion):
    try:
        now = datetime.now().isoformat()
        con.execute(
            "UPDATE tasks SET completed=$1, status=$2 WHERE uid=$3",
            [now, f"{comp.code}_{comp.detail}", uid],
        )
        return now
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Complete: {e}")


@app.get("/debug")
async def root():
    global con
    d = {
        "queues": {
            
        },
    }

    results = con.execute(
        " select count(*),queue_name from tasks group by queue_name;"
    ).fetchall()
    for r in results:        
        size = r[0]
        qn = r[1]
        if qn not in d["queues"]:
            d["queues"][qn] = {}
        d["queues"][qn]["total"] = size

    results = con.execute(
        " select count(*),queue_name from tasks where completed is NULL and assigned is not NULL group by queue_name ;"
    ).fetchall()
    for r in results:
        
        size = r[0]
        qn = r[1]
        if qn not in d["queues"]:
            d["queues"][qn] = {}

        d["queues"][qn]["assigned"] = size

    results = con.execute(
        " select count(*),queue_name from tasks where completed is not NULL and assigned is not NULL group by queue_name ;"
    ).fetchall()
    for r in results:
        print(r)
        size = r[0]
        qn = r[1]
        if qn not in d["queues"]:
            d["queues"][qn] = {}
        d["queues"][qn]["completed"] = size

    print(d)

    return d

## main code - todo: lookup how fast api manages it's main entry point
# create the default queues
for dq in settings.default_queues:
    logger.info(f"Setting up {dq}")
    q[dq] = Queue()

# create a connection to a file
con = duckdb.connect(f"{settings.database_path}/{settings.database_file_name}")
con.execute(
    "CREATE TABLE IF NOT EXISTS tasks (uid TEXT NOT NULL, queue_name TEXT NOT NULL, retries SMALLINT, added TIMESTAMP,	assigned TIMESTAMP,	completed TIMESTAMP,	status TEXT, data TEXT, 	PRIMARY KEY (uid));"
)

# preload the queue
# this may result in additional queues being created
results = con.execute("select * from tasks where completed is NULL;").fetchall()
for r in results:
    item = Item(uid=r[0], payload=r[7])
    qname = r[1]
    if qname not in q:
        q[qname] = Queue()
    q[qname].put(item)
