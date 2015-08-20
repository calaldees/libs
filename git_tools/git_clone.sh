for F in $(cat repos.txt) ; do
  git clone $F
done
