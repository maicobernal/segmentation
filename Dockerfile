## This Dockerfile is used to build an image for DCMTK storescp
## It will install DCMTK and start the storescp service when the container is started

FROM ubuntu:latest
RUN apt-get update && apt-get install dcmtk -y && apt-get clean

RUN mkdir /home/received

COPY ./config/start-storescp.sh /home/scripts/

RUN chmod +x /home/scripts/start-storescp.sh

ENTRYPOINT ["/home/scripts/start-storescp.sh"]