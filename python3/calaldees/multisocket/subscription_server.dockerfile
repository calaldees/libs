FROM python:alpine
COPY . /multisocket
ENTRYPOINT ["python3", "/multisocket/subscription_server.py"]
#CMD ["--help"]

ENV TCP_PORT=9872
ENV WEBSOCKET_PORT=9873

# Cant use ENV variables in CMD. Maybe we could use ARGS?
CMD ["--tcp_port", "9872", "--websocket_port", "9873"]

HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
    CMD netstat -an | grep ${WEBSOCKET_PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# docker build -t subscription_server --file subscription_server.dockerfile .
# docker run --rm -it -p 9872:9872 -p 9873:9873 subscription_server
