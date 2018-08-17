@echo off
REM https://gist.github.com/daredude/045910c5a715c02a3d06362830d045b6
FOR /f "tokens=*" %%i IN ('docker ps -aq') DO docker rm %%i
REM FOR /f "tokens=*" %%i IN ('docker images --format "{{.ID}}"') DO docker rmi %%i