FROM ubuntu:latest
RUN apt-get update && apt-get install dcmtk -y && apt-get clean

RUN mkdir /home/received

COPY ./config/start-storescp.sh /home/scripts/

RUN chmod +x /home/scripts/start-storescp.sh

ENTRYPOINT ["/home/scripts/start-storescp.sh"]