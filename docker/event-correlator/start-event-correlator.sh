#!/bin/sh

echo "Waiting for prelude-manager to be ready on port 5553"
while ! ncat -vvz prelude-manager 5553; do echo "Wating 10 secs..."; sleep 10; done

prelude-admin register "$PRELUDE_PROFILE" "idmef:rw" prelude-manager --uid prelude-correlator --gid prelude --passwd "password"

# workaround for tail -F saying: "has been replaced with a remote file. giving up on this name"
truncate -s0 "$SCISSOR_LOG_DIR"/event-correlator-output.log;

prelude-correlator -P /run/prelude-correlator/prelude-correlator.pid --profile=prelude-correlator > "$SCISSOR_LOG_DIR"/event-correlator-output.log 2>&1 &

tail -F \
  "$SCISSOR_LOG_DIR"/event-correlator-output.log
