GIT Repo Tools
==============

Overview
--------

A set of tools to help maintain and transfer a folder of lots of 3rd party
repositorys.

I was re-installing my development machine and thought "Damn, how will I preserve my folder of 3rd party projects". So I wrote `git_repo_list.py` to scan
the *./git/config*. files, extract the *url* of the project and write them to a
`repos.txt` file. 

`git_clone.sh` can then be used to re-instate the repos.

`git_update.sh` is a tool to *pull* all of these repo and ensure they are kept
up to date
