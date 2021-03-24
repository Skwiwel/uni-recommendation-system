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
