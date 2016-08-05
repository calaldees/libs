set +e
for REPO in $( ls )
do
    if [ -d "$REPO/.git" ]
    then
        echo ""
        echo ""
        echo "Updating $REPO ----------------"
        cd $REPO && git co master && git reset --hard origin/master && git fetch --tags && cd ..
    fi
done
