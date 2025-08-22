FROM debian:12

ENV ICECAST_HOSTNAME=localhost
ENV ICECAST_ADMIN=admin@localhost
ENV ICECAST_LOCATION=Earth

ENV ICECAST_SOURCE_PASSWORD=password
ENV ICECAST_RELAY_PASSWORD=password
ENV ICECAST_ADMIN_USER=admin
ENV ICECAST_ADMIN_PASSWORD=password

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        icecast2 \
        media-types \
        gettext-base \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN mkdir logs
RUN chown -R icecast2 /etc/icecast2 /opt

ADD entrypoint.sh icecast.xml.template .

USER icecast2
ENTRYPOINT [ "./entrypoint.sh" ]
CMD [ "icecast2", "-c", "/etc/icecast2/icecast.xml" ]