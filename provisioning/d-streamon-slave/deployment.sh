#!/bin/bash -xe

# get parameters
export config_name=""

export USER="root"
export PASSWD="scissorslave"
export HOME="/${USER}"

export LOG="${HOME}/log"

# create log
su -c 'touch ${LOG}' ${USER}

# root password update
echo -e "$PASSWD\n$PASSWD\n" | sudo passwd $USER

if [ "$?" = "0" ]; then
        echo -e "password impostata\n" >> $LOG
        else
          echo "errore nell'impostazione della password!" >> $LOG
          exit 2
fi

# permit ssh password login
sed -i 's/prohibit-password/yes/g' /etc/ssh/sshd_config && /etc/init.d/ssh reload

sed -ie 's/PermitRootLogin without-password/PermitRootLogin yes/g' /etc/ssh/sshd_config

service ssh restart
