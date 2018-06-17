FROM python:alpine
COPY . /multisocket
ENTRYPOINT ["python3", "/multisocket/subscription_server.py"]
CMD ["--help"]
# docker build -t subscription_server --file subscription_server.dockerfile .
# docker run --rm -it -p 9872:9872 -p 9873:9873 subscription_server --tcp_port 9872 --websocket_port 9873
