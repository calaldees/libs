#!/bin/bash
# Wait for a docker container (by name) to be healthy
# A hybrid of solutions from stackoverflow + cutom enhancements
# https://stackoverflow.com/questions/21183088/how-can-i-wait-for-a-docker-container-to-be-up-and-running
container_name=$1
if [ -z "$container_name" ]; then echo "container_name must be provided" && exit 1; fi
attempts=${2:-65}
attempt=0
while [ $attempt -le $attempts ]; do
    attempt=$(( $attempt + 1 ))
    container_id=$(docker ps -a -q --filter "name=$container_name" 2>/dev/null)
    echo "Waiting for container '$container_name -> $container_id' to be healthy (attempt: $attempt of $attempts)..."
    if [ "$(docker inspect -f {{.State.Health.Status}} $container_id 2>/dev/null)" == "healthy" ]; then
        break
    fi
    sleep 1
done
