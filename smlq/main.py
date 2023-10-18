import uuid
import duckdb
from queue import Empty, Queue
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
from .config import settings


app = FastAPI()

q = {}
q["default"] = Queue()
con = None

# data model
class Item(BaseModel):
    uid: str
    payload: str


class Completion(BaseModel):
    code: str
    detail: str


@app.post("/queue/{qid}")
async def add(qid, data: Item):
    global con
    # print(f"qid {qid}, data {data}")
    if qid not in q:
        raise HTTPException(
            status_code=404, detail="Queue not known - call reset first"
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


@app.get("/reset/{qid}")
async def reset(qid):
    try:
        con.execute(f"DELETE FROM tasks WHERE queuename='{qid}';")
        q[qid] = Queue()

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
        "queueszies": {
            "default": q["default"].qsize(),
        },
        "db": {
            "default": {"total": 0, "assigned": 0, "completed": 0},
        },
    }

    results = con.execute(
        " select count(*),queuename from tasks group by queuename;"
    ).fetchall()
    for r in results:
        print(r)
        size = r[0]
        qn = r[1]
        d["db"][qn]["total"] = size

    results = con.execute(
        " select count(*),queuename from tasks where completed is NULL and assigned is not NULL group by queuename ;"
    ).fetchall()
    for r in results:
        print(r)
        size = r[0]
        qn = r[1]
        d["db"][qn]["assigned"] = size

    results = con.execute(
        " select count(*),queuename from tasks where completed is not NULL and assigned is not NULL group by queuename ;"
    ).fetchall()
    for r in results:
        print(r)
        size = r[0]
        qn = r[1]
        d["db"][qn]["completed"] = size

    print(d)

    return d


# create a connection to a file
con = duckdb.connect(f"{settings.database_path}/{settings.database_file_name}")

con.execute(
    "CREATE TABLE IF NOT EXISTS tasks (uid TEXT NOT NULL, queue_name TEXT NOT NULL, retries SMALLINT, added TIMESTAMP,	assigned TIMESTAMP,	completed TIMESTAMP,	status TEXT, data TEXT, 	PRIMARY KEY (uid));"
)

# preload the queue
results = con.execute("select * from tasks where completed is NULL;").fetchall()
for r in results:
    item = Item(uid=r[0], payload=r[7])
    qname = r[1]
    if qname not in q:
        q[qname] = Queue()
    q[qname].put(item)
