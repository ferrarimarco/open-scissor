FROM ubuntu:16.04

LABEL maintainer "ferrari.marco@gmail.com"

RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
    default-jre=2:1.8-56ubuntu2 \
    iproute2=4.3.0-1ubuntu3 \
    net-tools=1.60-26ubuntu1 \
    netcat=1.10-41 \
    wget=1.17.1-1ubuntu1.3 \
  && apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN \
  wget -q 'https://archive.cloudera.com/cdh5/ubuntu/xenial/amd64/cdh/cloudera.list' -O /etc/apt/sources.list.d/cloudera.list \
  && wget -q 'https://archive.cloudera.com/cdh5/ubuntu/xenial/amd64/cdh/archive.key' -O archive.key \
  && apt-key add archive.key \
  && rm archive.key

RUN \
  apt-get update \
  && apt-get install -y --no-install-recommends \
    flume-ng=1.6.0+cdh5.14.2+181-1.cdh5.14.2.p0.11~xenial-cdh5.14.2 \
    flume-ng-agent=1.6.0+cdh5.14.2+181-1.cdh5.14.2.p0.11~xenial-cdh5.14.2 \
  && apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

ENV FLUME_CONFIG_PATH /opt/flume-config
COPY flume-config/ $FLUME_CONFIG_PATH

ENV MORPHLINE_LIB_PATH /opt/morphline-lib
COPY morphline-lib/ $MORPHLINE_LIB_PATH

ENV ZOOKEEPER_AGENT_PATH /opt/zookeeper-agent
COPY zookeeper-agent/ $ZOOKEEPER_AGENT_PATH

ENV INIT_SCRIPT_PATH /opt/start-flume.sh
COPY start-flume.sh $INIT_SCRIPT_PATH
RUN chmod a+x "$INIT_SCRIPT_PATH"

ENV SCISSOR_LOG_DIR /var/log/scissor
RUN mkdir -p "$SCISSOR_LOG_DIR"

EXPOSE 5445 5446 5447 10000 15222 20000 44444

ENTRYPOINT ["/opt/start-flume.sh"]
