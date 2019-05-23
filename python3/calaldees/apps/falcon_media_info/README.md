# Can't use PORT env in CMD?
#CMD ["--port", "8000"]

#HEALTHCHECK --interval=15s --timeout=1s --retries=3 --start-period=1s \
#    CMD netstat -an | grep ${PORT} > /dev/null; if [ 0 != $? ]; then exit 1; fi;

# docker build -t falcon_media_info --file falcon_media_info.dockerfile .
# docker run --rm -it -p 8000:8000 falcon_media_info

# docker run --rm -it -p 8000:8000 -v /Users/allancallaghan/code/personal/libs/python3/calaldees/apps/:/meh/ -v /Users/allancallaghan/Sync/superLimitBreak/assets/visuals/:/Users/allancallaghan/Sync/superLimitBreak/assets/visuals/ --entrypoint /bin/sh falcon_media_info
