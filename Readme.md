# Recommendation system

A university project focused on engineering an ML solution to a problem. Chosen was the subject of an recommendation system for an online shop.

The publicly shared project repo contains no usable data. Sample data, cleaned of most of recognizable information, is located in `data_raw/`.

## Contributors
 - [psawicki0](https://github.com/psawicki0)
 - [Skwiwel](https://github.com/Skwiwel)

## Functionalities
Two simple recommendation models:
 - popularity based
 - collaborative filtering based

Additionally, a microservice serving the recommendations on a per-user basis was implemented. The service offers running of a transparent (to the user) A/B test functionality for comparison of the aforementioned models. The service offers a JSON based RESTful interface.

## Compiling
The data handling parts of the project are made using loose python scripts. To install the required Python libraries:
```
python3 -m pip install -r requirements.txt
```
The microservice is implemented with go and internally uses an SQLite database for A/B testing. To compile the service:
```
go get github.com/mattn/go-sqlite3
cd ./microservice/go
go build -o ./../../service.exe ./cmd
```
This compiles the microservice into `service.exe` located in the root directory of the repo. The `.exe` extension is mainly for compatibility with Windows.

## Running
The required data `sessions.jsonl` and `products.jsonl` needs to be located in `data_raw`.  
For A/B testing the database in `ab_testing/` needs to be manually reset by removing the trailing `.init`.

To run the service with just collaborative filtering based model:
```
./service.exe
```
Running with A/B testing enabled:
```
./service.exe --abtest
```
Data relevant for A/B testing is saved to the database.

The service interface takes in request via HTTP GET at the location `/recommendations`. The user for whom we are requesting recommendations should be specified by a `user_id` and the optionam number of recommendations by `num`.  
For example:
```
curl -i "<service_address>/recommendations?user_id=106&num=10"
```

## Docker image
The microservice is also packed into a Docker image available at [DockerHub](https://hub.docker.com/r/skwiwel/uni-recommendation-system).  
Running it will require mounting the `data_raw/` dir containing actual data as well as the `ab_testing` dir with a db for A/B testing.

To run:
```
docker pull skwiwel/uni-recommendation-system
docker run \
    --name recommendations \
    -p 80:80 \
    --mount type=bind,source="$(pwd)"/data_raw,target=/uni-recommendation-system/data_raw,readonly \
    --mount type=bind,source="$(pwd)"/ab_testing,target=/uni-recommendation-system/ab_testing \
    skwiwel/uni-recommendation-system --mode abtest
```
The last `--mode abtest` argument is passed to the service executable and runs the service in A/B testing mode.

## System demo
The service is (hopefully still) currently running on a cloud container under the public ip `130.61.188.211`.  
You can check out how it's working by requesting recommendations, e.g.:
```
curl -i "130.61.188.211/recommendations?user_id=106&num=10"
```