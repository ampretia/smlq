# smql

A *very* simple, yet effective 'job queue' for distributed applications.  The genesis was to have a simple K8S deployment where producers could submit work (eg a file to process in S3) and then have multiple consumers access to get their next job. 

Consumers would have the ability to mark jobs as complete; should a consumer crash therefore, otherrs would be able to pickup the work. In effect the work is 'sharded' between different consumers. 

Access to the queue is via REST



