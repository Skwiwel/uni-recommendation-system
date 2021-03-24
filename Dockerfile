FROM golang:alpine as golang-builder
# get gcc from build-base for go-sqlite3
RUN apk add --no-cache build-base
RUN go get github.com/mattn/go-sqlite3
COPY . "/go/src/github.com/skwiwel/uni-recommendation-system/"
WORKDIR "/go/src/github.com/skwiwel/uni-recommendation-system/microservice/go"
RUN CGO_ENABLED=1 GOOS=linux go build -a -ldflags '-extldflags "-static"' -o /service.exe ./cmd

FROM python:3-slim
RUN apt-get update -y && apt-get install apt-file -y && apt-file update && apt-get install -y build-essential
COPY ./requirements.txt "/uni-recommendation-system/"
RUN pip install --no-cache-dir -r /uni-recommendation-system/requirements.txt
COPY --from=golang-builder /service.exe "/uni-recommendation-system/"
COPY . "/uni-recommendation-system/"
WORKDIR "/uni-recommendation-system/"
ENTRYPOINT ["./service.exe"]