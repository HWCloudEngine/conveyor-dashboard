#! /bin/bash
#PYTHON_VERSION=python -c 'import platform; print platform.python_version()' | cut -d . -f 1,2
if [ ! $# -eq 1 ]; then
    echo "You should provide a cmd to execute, install or uninstall." 
    exit 1;
fi

cd `dirname $0`

if [ "$1" = "install" ]; then
    PACKAGE_DIR=`python package_path.py`
    echo $PACKAGE_DIR > conveyordashboard_path
    cp -rf ../conveyordashboard/ $PACKAGE_DIR
    cp ../conveyordashboard/local/_50_conveyor.py /usr/share/openstack-dashboard/openstack_dashboard/local/enabled/_50_conveyor.py
    if [ -L /usr/share/openstack-dashboard/openstack_dashboard/static/conveyordashboard/conveyordashboard ];then
        rm /usr/share/openstack-dashboard/openstack_dashboard/static/conveyordashboard/conveyordashboard
    fi
    ln -s ${PACKAGE_DIR}/conveyordashboard/static/conveyordashboard/ /usr/share/openstack-dashboard/openstack_dashboard/static/conveyordashboard
elif [ "$1" = "uninstall" ]; then
    PACKAGE_DIR=`cat conveyordashboard_path`
    rm /usr/share/openstack-dashboard/openstack_dashboard/local/enabled/_50_conveyor.py*
    rm -rf $PACKAGE_DIR/conveyordashboard/
else
    exit 1;
fi
