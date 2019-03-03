#!/bin/bash

REPO=/Users/kvl/Multimedia
SRC_DIR=/Users/kvl/src/tablo_tools

pkill ffmpeg
mkdir ${REPO}
echo "Mounting ${REPO}"
mount -t smbfs //media_archiver:y9i2ejnGk3U1ei8WZa@nas01/Multimedia ${REPO}
if [ $? != 0 ] ; then
    echo "Could not mount ${REPO}, exiting..."
    exit 1
fi
caffeinate -s ${SRC_DIR}/venv3/bin/python ${SRC_DIR}/tablo_util.py record new --repo=${REPO}/TvShows
echo "Unmounting ${REPO}"
umount ${REPO}
rmdir ${REPO} 
