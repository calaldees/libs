set +e
for REPO in $( ls )
do
    if [ -d "$REPO/.git" ]
    then
        echo ""
        echo ""
        echo "Updating $REPO ----------------"
        cd $REPO && git co master && git pull && git fetch --tags && cd ..
    fi
done
