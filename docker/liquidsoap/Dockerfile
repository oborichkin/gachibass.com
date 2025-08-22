FROM debian:12

RUN apt-get update -y
RUN apt-get install -y liquidsoap gettext-base

RUN useradd -ms /bin/bash liquid
WORKDIR /opt
ADD radio.liq.template entrypoint.sh .
RUN chown -R liquid /opt

USER liquid

ENTRYPOINT [ "./entrypoint.sh" ]
