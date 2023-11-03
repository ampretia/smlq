# Main justfile to run all the development scripts
# To install 'just' see https://github.com/casey/just#installation

# Ensure all properties are exported as shell env-vars
set export

# set the current directory, and the location of the test dats
CWDIR := justfile_directory()

_default:
  @just -f {{justfile()}} --list

start:
    #!/bin/bash
    DB_PATH={{CWDIR}}/smlq uvicorn smlq.main:app --host 0.0.0.0 --port 3000

k8s:
    #!/bin/bash
    
    kubectl create configmap env-conf --from-file=./.env    
    kubectl apply -f deployment.yaml


docker:
    #!/bin/bash
    TAG=smlq    
    IMAGE=${TAG}:latest
    
    docker build -t ${TAG} .
    docker tag ${TAG} $IMAGE
      
    
