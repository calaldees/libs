FROM python:alpine
RUN pip install falcon
COPY falcon_url_to_subscription_bridge.py /
ENTRYPOINT ["python3", "falcon_url_to_subscription_bridge.py"]
CMD ["--help"]
