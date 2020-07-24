#!/bin/bash

REPO=/home/kvl/nas01_Multimedia
SRC_DIR=/home/kvl/src/tablo_tools
shouldUnmount="FALSE"
shouldRemove="FALSE"

pkill ffmpeg
if ! grep -qs ${REPO} /proc/mounts ; then
    if [ ! -e ${REPO} ] ; then
        mkdir -p ${REPO}
        shouldRemove="TRUE"
    fi
    echo "Mounting ${REPO}"
    mount ${REPO}
    shouldUnmount="TRUE"
else
    echo "${REPO} already mounted"
fi

if [ ! -e ${REPO}/TvShows ] ; then
    echo "Something is wrong, can't find TvShows"
    exit 1
fi

if [ $? != 0 ] ; then
    echo "Could not mount ${REPO}, exiting..."
    exit 1
fi

cp ${REPO}/TvShows/tablo_library.p /home/kvl/.tablo/tablo_library.p
${SRC_DIR}/venv/bin/python ${SRC_DIR}/tablo_util.py record new --repo=${REPO}/TvShows
cp /home/kvl/.tablo/tablo_library.p ${REPO}/TvShows/tablo_library.p

if [ ${shouldUnmount} == "TRUE" ] ; then
    echo "Unmounting ${REPO}"
    umount ${REPO}
fi
if [ ${shouldRemove} == "TRUE" ] ; then
    echo "Removing ${REPO}"
    rmdir ${REPO} 
fi
