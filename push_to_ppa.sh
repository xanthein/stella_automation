#!/bin/bash

platforms=("$@")

SERIES='noble'
git_repo='https://git.launchpad.net/~oem-solutions-engineers/pc-enablement/+git/oem-stella-projects-meta'

if [ ${#platforms} -eq 0 ];then
    echo Need to pass platforms
    exit
fi

if [ "$GPG_KEY" == "" ];then
    echo Need to set GPG_KEY environment variable
    exit
fi

origin_folder=$(pwd)
for platform in ${platforms[@]};
do
    echo ==== $platform ====
    ppa_version=$(apt-cache policy oem-stella-$platform-meta | awk '/Candidate:/{print $2}')
    echo "PPA: $ppa_version"
    temp_folder=$(mktemp -d)
    echo $temp_folder
    cd $temp_folder
    git clone --depth 1 -b $platform-$SERIES-oem $git_repo
    cd oem-stella-projects-meta
    git_version=$(dpkg-parsechangelog --show-field Version)
    echo "GIT: $git_version"
    if  dpkg --compare-versions $git_version gt $ppa_version ;then
        echo "Need to push to PPA"
        dpkg-buildpackage -S -us -uc
        cd $temp_folder
        debsign -k $GPG_KEY *.changes
        dput ppa:oem-archive/stella *.changes
    fi
    cd $origin_foler
    rm -rf $temp_folder
done
