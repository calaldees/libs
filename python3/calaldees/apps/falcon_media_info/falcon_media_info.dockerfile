FROM python:alpine as base
RUN pip install --no-cache-dir \
    falcon \
    hachoir3

COPY falcon_media_info.py /

ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}
ENTRYPOINT python3 falcon_media_info.py --port ${PORT}


FROM base as test
RUN pip install --no-cache-dir \
    pytest
COPY falcon_media_info_test.py falcon_media_info_test.png /
RUN pytest --doctest-modules falcon_media_info_test.py


FROM base
