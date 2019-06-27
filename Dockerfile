FROM python:3.7-slim
RUN apt update && \
    apt dist-upgrade -y && \
    pip3 install pipenv && \
    useradd -c "Jenkins Pillage" -m -s /sbin/nologin pillage
USER pillage
WORKDIR /home/pillage
COPY . /home/pillage
RUN pipenv install
ENTRYPOINT ["pipenv", "run", "start"]
