#  https://help.github.com/en/articles/splitting-a-subfolder-out-into-a-new-repository (this doesnt do tags)
#  https://stackoverflow.com/a/359759/3356840

# $1 == git@repo.git
# $2 == SUBFOLDER/TO/EXTRACT

git remote rm origin
git remote add origin $1
git filter-branch --tag-name-filter cat --prune-empty --subdirectory-filter $2 -- --all
git reset --hard
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
git reflog expire --expire=now --all
git gc --aggressive --prune=now
git push -u
git push --follow-tags
