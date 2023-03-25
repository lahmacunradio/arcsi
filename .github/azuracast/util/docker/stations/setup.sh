#!/bin/bash
set -e
set -x

apt-get update

# Install common scripts
# cp -rT /bd_build/stations/scripts/ /usr/local/bin

# cp -rT /bd_build/stations/startup_scripts/. /etc/my_init.d/

# cp -rT /bd_build/stations/service.minimal/. /etc/supervisor/minimal.conf.d/

# cp -rT /bd_build/stations/service.full/. /etc/supervisor/full.conf.d/

# Run service setup for all setup scripts
for f in /bd_build/stations/setup/*.sh; do
  bash "$f" -H 
done

# Cleanup
apt-get -y autoremove
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/tmp*

chmod -R a+x /usr/local/bin
chmod -R +x /etc/my_init.d
