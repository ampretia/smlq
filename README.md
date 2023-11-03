# smql

A *very* simple, yet effective 'job queue' for distributed applications.  The genesis was to have a simple K8S deployment where producers could submit work (eg a file to process in S3) and then have multiple consumers access to get their next job. 

Consumers would have the ability to mark jobs as complete; should a consumer crash therefore, otherrs would be able to pickup the work. In effect the work is 'sharded' between different consumers. 

Access to the queue is via REST


## Examples

- [`load.py`](./examples/load.py) reads simple text file and puts each line to a queue

- [`get.py`](./examples/get.py) gets until nothing available

- [`getcomplete.py`](./examples/getcomplete.py) gets and completes all tasks


```
python load.py --queue input --datafile datafile
```

## Running
As docker container; default queues, db is not externally mapped.
 
```
docker run -it -p 3000:3000 smlq
``` 

As a docker container, default queues, mapping to db directory to local disk. Persists therefore past container restart

```
docker run -it -p 3000:3000 -v $(pwd):/opt/smlq/data smlq
```


As a docker contain, set of queues plus mappining db to local disk
```
docker run -it -p 3000:3000 -e default_queues='["input","output"]' -v $(pwd):/opt/smlq/data smlq
```