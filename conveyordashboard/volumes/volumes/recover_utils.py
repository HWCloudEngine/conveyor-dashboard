from operator import attrgetter
import time
from horizon import exceptions
from horizon import messages

from django.utils.translation import ugettext_lazy as _
from horizon.utils.urlresolvers import reverse

from openstack_dashboard.api import cinder
from openstack_dashboard.api import nova
from openstack_dashboard.api import neutron
from openstack_dashboard.api import network

VERSION = '2.0'

def cinder_az_supported(request):
    try:
        return cinder.extension_supported(request, 'AvailabilityZones')
    except Exception:
        exceptions.handle(request, _('Unable to determine if '
                                     'availability zones extension '
                                     'is supported.'))
        return False


def get_volume_recover_status(request, volume_id):
    recover_status = None
    target_volume = None
    source_volume_meta = \
        cinder.volume_get(request, volume_id).metadata
    if source_volume_meta and 'recover_status' in source_volume_meta:
        recover_status = source_volume_meta['recover_status']
    if source_volume_meta and 'target_volume' in source_volume_meta:
        target_volume = cinder.volume_get(request,
                                          source_volume_meta['target_volume'])
    return recover_status, target_volume


def get_target_server(request, attachment_id):
    target_server = None
    if not attachment_id:
        return target_server
    source_server = nova.server_get(request, attachment_id)

    if source_server.metadata and 'target_server' in source_server.metadata:
        target_server = nova.server_get(request,
                                        source_server.metadata['target_server'])
        if not target_server:
            raise Exception(_("can't find target_server of server:%s, should be:%s" %
                              (attachment_id, source_server.metadata['target_server'])))
    return target_server


def set_volume_recover_status(request,
                              volume_id,
                              recover_status,
                              recover_target=None):
    print "set recover_status:%s, target_volume:%s" % \
          (recover_status, recover_target)
    meta_data = {'recover_status': recover_status}
    if recover_target:
        meta_data['target_volume'] = recover_target
    cinder.volume_set_metadata(request,
                               volume_id,
                               meta_data)


def set_server_recover_target(request,
                              server_id, recover_target):
    meta_data = {'target_server': recover_target}
    nova.server_set_meta(request, server_id, meta_data)


def recover_volume_only(request, source_volume_id, source_volume_name,
                        size, name, volume_type, az, recover_source_id,
                        recover_source_type):
    print "recover_source_id:%s, recover_source_type:%s" % \
          (recover_source_id, recover_source_type)
    if recover_source_type == 'snapshot':
        return recover_volume_only_from_snapshot(request, source_volume_id,
                                                 source_volume_name, size, name,
                                                 volume_type, az, recover_source_id)
    elif recover_source_type == 'backup':
        return recover_volume_only_from_backup(request, source_volume_id,
                                               source_volume_name, size, name,
                                               volume_type, az, recover_source_id)


def recover_volume_only_from_snapshot(
        request, source_volume_id, source_volume_name,
        size, name, volume_type, az, snapshot_id):
    print "snapshot_id:%s" % snapshot_id
    target_volume = cinder.volume_create(request,
                                         size,
                                         name,
                                         # data['description'],
                                         None,
                                         volume_type,
                                         snapshot_id=snapshot_id,
                                         image_id=None,
                                         metadata={},
                                         availability_zone=az,
                                         source_volid=None)
    # wait until volume status turned to be available
    volume_status = cinder.volume_get(request, target_volume.id).status
    sleep_time = 120
    while volume_status == 'creating':
        if sleep_time > 0:
            time.sleep(5)
        else:
            break
        volume_status = cinder.volume_get(request, target_volume.id).status
        sleep_time -= 5
    if volume_status != 'available':
        raise Exception(_("Unable to recover volume:%s." % source_volume_name))

    # update recover status
    set_volume_recover_status(request, source_volume_id, "volume_recovered",
                                   recover_target=target_volume.id)
    message = _('Recovered volume "%s"') % source_volume_name
    messages.info(request, message)
    return target_volume


def recover_volume_only_from_backup(
        request, source_volume_id, source_volume_name,
        size, name, volume_type, az, backup_id):
    # TODO: only support restore to specified volume now,
    # will add param to restore api to support restore&create
    # volume with cascading open stack

    try:
        # create a blank volume
        target_volume = cinder.volume_create(request,
                                             size,
                                             name,
                                             None,
                                             volume_type,
                                             metadata={},
                                             availability_zone=az)
        # wait until volume status turned to be available
        volume_status = cinder.volume_get(request, target_volume.id).status
        sleep_time = 120
        while volume_status == 'creating':
            if sleep_time > 0:
                time.sleep(5)
                print "waiting for volume creation:%s" % target_volume.id
            else:
                break
            volume_status = cinder.volume_get(request, target_volume.id).status
            sleep_time -= 5

        print "volume:%s status turns to:%s" % (target_volume.id, volume_status)
        if volume_status != 'available':
            print "Unable to create target volume:%s." % source_volume_name
            print "status:%s" % volume_status
            raise Exception(_("Unable to create target volume:%s."
                              % source_volume_name))

        # restore to the blank volume
        restore = cinder.volume_backup_restore(request,
                                               backup_id,
                                               target_volume.id)
        restore_status = cinder.volume_get(request, target_volume.id).status
        sleep_time = 120
        while restore_status == 'restoring-backup':
            if sleep_time > 0:
                time.sleep(5)
                print "waiting for volume restoring:%s" % target_volume.id
                restore_status = cinder.volume_get(request, target_volume.id).status
                sleep_time -= 5
            else:
                break

        print "volume:%s status turns to:%s" % (target_volume.id, restore_status)
        if restore_status != 'available':
            print "Unable to recover volume:%s." % source_volume_name
            print "status:%s" % restore_status
            raise Exception(_("Unable to recover volume:%s." % source_volume_name))

        # update recover status
        set_volume_recover_status(request, source_volume_id,
                                  "volume_recovered",
                                  recover_target=target_volume.id)

        message = _('Recovered volume "%s"') % source_volume_name
        messages.info(request, message)
        return target_volume

    except Exception:
        msg = _('Unable to restore backup.')
        redirect = reverse('horizon:project:volumes:index')
        exceptions.handle(request, msg, redirect=redirect)


def recover_attach_vm(request, volume_id, attachment_id, az):
    if not attachment_id:
        return None
    # support multiple disks attached to same vm,
    # check the source server, whether it has got a target server
    server = nova.server_get(request, attachment_id)
    if server.status == 'ACTIVE':
        nova.server_stop(request, attachment_id)
    sleep_time = 300
    status = nova.server_get(request, attachment_id).status

    while status != 'PAUSED' and status != 'SHUTOFF':
        if sleep_time > 0:
            time.sleep(5)
            print "waiting for vm paused:%s, status:%s" % (attachment_id, status)
        else:
            break
        status = nova.server_get(request, attachment_id).status
        sleep_time -= 5

    if status != 'PAUSED' and status != 'SHUTOFF':
        raise Exception(_("Unable to pause volume attachment vm:%s."
                          % attachment_id))

    print "start recover attach vm, original server:%s" % attachment_id
    target_server = get_target_server(request, attachment_id)
    nic_info = None
    floating_ip = None
    meta_data = {}
    print "addresses:%s" % server.addresses
    if server.addresses:
        for address in server.addresses.values()[0]:
            print "address:%s" % address
            mac_address = address['OS-EXT-IPS-MAC:mac_addr']
            ip_address = address['addr']
            address_type = address['OS-EXT-IPS:type']
            print "mac:%s, ip:%s, address_type:%s" % (mac_address, ip_address, address_type)

            if address_type == 'fixed':
                search_opts = {'mac_address': mac_address}
                ports = neutron.port_list(request, **search_opts)
                if ports:
                    nic_info = {"net-id": ports[0].network_id, "v4-fixed-ip": ip_address}
                    # nic_info = {"net-id": ports[0].network_id, "v4-fixed-ip": ''}
                    print "nic_info:%s" % nic_info
                    meta_data['net-id'] = ports[0].network_id
                    meta_data['v4-fixed-ip'] = ip_address
                    nova.instance_interface_detach(request, attachment_id, ports[0].id)
                    neutron.port_delete(request, ports[0].id)
            elif address_type == 'floating':
                floating_ip = ip_address
                meta_data['floating_ip'] = ip_address
        if meta_data:
            print "metadata:%s" % meta_data
            nova.server_set_meta(request, attachment_id, meta_data)
    elif server.metadata and 'net-id' in server.metadata \
            and 'v4-fixed-ip' in server.metadata:
        nic_info = {"net-id": server.metadata['net-id'],
                    "v4-fixed-ip": server.metadata['v4-fixed-ip']}
        if floating_ip in server.metadata:
            floating_ip = server.metadata['floating_ip']

    if not target_server:
        print "attachment server:%s" % server
        target_server_name = server.name + "-recovered"
        target_server = nova.server_create(request,
                                           target_server_name,
                                           server.image['id'],
                                           server.flavor['id'],
                                           server.key_name,
                                           user_data=None,
                                           security_groups=None,
                                           block_device_mapping=None,
                                           block_device_mapping_v2=None,
                                           nics=[nic_info] if nic_info else None,
                                           availability_zone=az,
                                           instance_count=1,
                                           admin_pass=None,
                                           disk_config=None,
                                           config_drive=None,
                                           meta={})
        print "target server:%s" % target_server

    # wait until target server ready
    status = target_server.status
    while status == 'BUILD':
        time.sleep(5)
        print "waiting for vm spawning:%s, status:%s" % (target_server.id, status)
        status = nova.server_get(request, target_server.id).status

    if status != 'ACTIVE':
        # delete target server in case it occupies the source ip
        print "delete target server:%s, status:%s" % (target_server.id, status)
        # nova.server_delete(request, target_server.id)
        raise Exception(_("Unable to recover volume attachment vm:%s."
                          % target_server_name))

    # associate floating ip to the running server
    if floating_ip:
        server = nova.server_get(request, target_server.id)
        port_id = None
        if server.addresses:
            mac_address = server.addresses.values()[0][0]['OS-EXT-IPS-MAC:mac_addr']
            ip4_address = server.addresses.values()[0][0]['addr']
            print "mac:%s, ipv4:%s" % (mac_address, ip4_address)
            search_opts = {'mac_address': mac_address}
            ports = neutron.port_list(request, **search_opts)
            if ports:
                port_id = ports[0].id
                print "found port id:%s" % port_id
                # compose port id as horizon format
                port_id = port_id + "_" + nic_info['v4-fixed-ip']
                print "composed port_id:%s" % port_id
        fips = network.tenant_floating_ip_list(request)
        floating_ip_id = None
        for fip in fips:
            if fip.ip == floating_ip:
                floating_ip_id = fip.id
                print "fip ip:%s, id:%s" % (floating_ip, floating_ip_id)
        network.floating_ip_associate(request, floating_ip_id, port_id)

    # if actually created target server, mark it in source server's meta
    set_server_recover_target(request, attachment_id, target_server.id)

    # mark volume's recover status
    set_volume_recover_status(request,
                              volume_id,
                              "vm_recovered",
                              recover_target=None)
    message = _('Recovered attachment instance"%s"') % server.name
    messages.info(request, message)
    return target_server


def wait_volume_restoring(request, target_volume):
    restore_status = cinder.volume_get(request, target_volume.id).status
    print "volume_status before attaching:%s, %s" % (target_volume.id, restore_status)
    sleep_time = 120
    while restore_status == 'restoring-backup':
        if sleep_time > 0:
            time.sleep(5)
            print "waiting for volume restoring:%s" % target_volume.id
            restore_status = cinder.volume_get(request, target_volume.id).status
            sleep_time -= 5
        else:
            break

    print "volume:%s status turns to:%s" % (target_volume.id, restore_status)
    # allow redo while disk in in-use status
    if restore_status != 'available' and restore_status != 'in-use':
        print "Unable to restore to volume:%s." % target_volume.id
        print "status:%s" % restore_status
        raise Exception(_("Unable to restore to volume:%s." % target_volume.name))


def attach_and_wait_volume_available(request, target_volume, target_server, device):
    nova.instance_volume_attach(request,
                                target_volume.id,
                                target_server.id,
                                device)
    volume_status = cinder.volume_get(request, target_volume.id).status

    while volume_status == 'attaching' or volume_status == 'available':
        time.sleep(5)
        print "waiting for attach volume:%s to vm:%s" % \
              (target_volume.id, target_server.id)
        volume_status = cinder.volume_get(request, target_volume.id).status
    return volume_status


def attach_target_volume_to_vm(request,
                               volume_id,
                               attachment_id,
                               target_volume,
                               target_server,
                               device):
    # has no attachment, just return
    # TODO: handle attach failure, which may have changed
    # volume status to attaching and can't be retried
    if not attachment_id:
        return True

    if not target_volume:
        raise Exception(_("target volume is None during attach"))

    if not target_server:
        raise Exception(_("target server is None during attach"))

    # volume and server both are ready, start to attach
    print "try to attach volume:%s to: %s at: %s" % \
          (target_volume.id, target_server.id, device)

    wait_volume_restoring(request, target_volume)

    volume_status = attach_and_wait_volume_available(
        request, target_volume,
        target_server, device)

    if volume_status == 'restoring-backup':
        wait_volume_restoring(request, target_volume)
        volume_status = attach_and_wait_volume_available()

    if volume_status != 'in-use':
        print "Unable to attach target volume:%s to vm:%s, status:%s" % \
              (target_volume.id, target_server.id, volume_status)
        raise Exception(_("Unable to attach target volume:%s.") %
                        target_volume.name)
    message = _('Attach recovered volume to instance"%s"') % \
              target_server.name
    messages.info(request, message)

    print "restart vm:%s" % target_server.id
    nova.server_reboot(request, target_server.id,
                       soft_reboot=True)
    time.sleep(5)
    status = nova.server_get(request, target_server.id).status
    while status != 'ACTIVE':
        time.sleep(5)
        print "waiting for vm rebooting:%s, status:%s" %\
              (target_server.id, status)
        status = nova.server_get(request, target_server.id).status

    if status != 'ACTIVE':
        raise Exception(_("Unable to soft reboot vm:%s."
                          % target_server.id))
    message = _('soft rebooted server "%s"') % \
              target_server.name
    messages.info(request, message)

    set_volume_recover_status(request,
                              volume_id,
                              "attachment_recovered",
                              recover_target=None)

    return True


def get_volume_backup_zone(request, volume):
    set_volume_backup_zone_from_type(request, [volume])
    return volume.backup_zone


def get_generic_volume_type_from_volume(volume):
    return volume.volume_type.split('@')[0] \
        if volume.volume_type is not None else 'None'


def get_generic_volume_type(volume_type):
    return volume_type.split('@')[0] \
        if volume_type is not None else 'None'


def set_volume_backup_zone_from_type(request, volumes):
    volume_types_dict = {}
    volume_types = cinder.volume_type_list(request)

    for volume_type in volume_types:
        volume_types_dict[volume_type.name] = volume_type

    for volume in volumes:
        volume.backup_zone = None
        if hasattr(volume, 'volume_type') and volume.volume_type:
            volume_type_object = volume_types_dict[volume.volume_type]
            if hasattr(volume_type_object, 'extra_specs') and \
                'volume_backend_name' in volume_type_object.extra_specs:
                backend = volume_type_object.extra_specs['volume_backend_name']
                # split backend fields as format type:support_az:backup_az
                backend_fields = backend.split(':')
                if len(backend_fields) >= 3:
                    volume.backup_zone = backend_fields[2]


def set_readable_volume_recover_status(request, volumes, source_type='snapshot'):
    for volume in volumes:
        recover_status = 'Not-Recoverable'
        recovered_volume_id = None

        if volume.volume_type and volume.volume_type.find('hybrid') >= 0:
            source_available = is_recover_source_available(request, volume.id, source_type)
            print "volume.metadata %s" % volume.metadata

            if volume.metadata and 'recover_status' in volume.metadata:
                original_status = volume.metadata['recover_status']
                if original_status == 'attachment_recovered':
                    try:
                        target_volume = cinder.volume_get(request,
                                                          volume.metadata['target_volume'])
                        # only return recovered_volume_id when it's done
                        recovered_volume_id = volume.metadata['target_volume']
                        recover_status = 'Done: recovered to %s' % target_volume.name
                    except Exception as e:
                        recover_status = 'Error: recovered volume missing!'
                        print "recovered volume:%s is missing!" % volume.metadata['target_volume']
                elif original_status == 'volume_recovered' \
                        and not volume.attachments:
                    try:
                        target_volume = cinder.volume_get(request,
                                                          volume.metadata['target_volume'])
                        # only return recovered_volume_id when it's done
                        recovered_volume_id = volume.metadata['target_volume']
                        recover_status = 'Done: recovered to %s' % target_volume.name
                    except Exception as e:
                        recover_status = 'Error: recovered volume missing!'
                        print "recovered volume:%s is missing!" % volume.metadata['target_volume']
                elif source_available:
                    recover_status = 'Recoverable'
            elif source_available:
                recover_status = 'Recoverable'
        volume.recover_status = recover_status
        volume.recovered_volume_id = recovered_volume_id
        print "recover_status is:%s" % recover_status


def is_recover_source_available(request, volume_id, source_type):
    avail_source = []
    if source_type == "snapshot":
        avail_source = cinder.volume_snapshot_list(request,
                                                   search_opts={'volume_id': volume_id,
                                                                'all_tenants': True,
                                                                'status': 'available'})
    elif source_type == "backup":
        backups = cinder.volume_backup_list(request)
        for backup in backups:
            if backup.volume_id == volume_id and backup.status == 'available':
                avail_source.append(backup)
                # NOTE, break once found one backup
                break
    return bool(avail_source)


def recover_volume_from_volume_id(request, source_volume_id):
    # get snapshot, recover volume name, size
    snapshot_id = None
    snapshots = cinder.volume_snapshot_list(request,
                                            search_opts={'all_tenants': True,
                                                         'status': 'available',
                                                         'volume_id': source_volume_id})
    if snapshots:
        snapshots = sorted(snapshots,
                           key=attrgetter('created_at'),
                           reverse=True)
        snapshot_id = snapshots[0].id
    else:
        error_info = "has no snapshot to recover from, volume:%s" % source_volume_id
        raise Exception(error_info)
    size = snapshots[0].size

    # get source_volume_name, target volume name, volume type,
    # backup az, attachment server id
    source_volume = cinder.volume_get(request, source_volume_id)
    source_volume_name = source_volume.name
    target_volume_name = source_volume_name + "_recovered"
    backup_zone = get_volume_backup_zone(request, source_volume)
    if not backup_zone:
        error_info = "has no backup zone to recover to, volume:%s" % source_volume_id
        raise Exception(error_info)
    attachment_server_id = source_volume.attachments[0]['server_id'] \
        if source_volume.attachments else None

    attach_device = source_volume.attachments[0]['device'] \
        if source_volume.attachments else None

    return recover_volume(request, source_volume_id, source_volume_name,
                          target_volume_name, size, "ec2", snapshot_id,
                          backup_zone, attachment_server_id, attach_device)


def recover_volume(request, source_volume_id, source_volume_name,
                   target_volume_name, target_volume_size,
                   volume_type, recover_source_id, backup_zone,
                   recover_source_type="snapshot",
                   attachment_server_id=None, attach_device=None):
    # check volume recover status, and act according to its
    # recover status

    recover_status, target_volume = \
        get_volume_recover_status(request, source_volume_id)
    print "volume:%s, recover status:%s, target_volume:%s" % \
          (source_volume_name, recover_status, target_volume)
    if not recover_status:
        # recover volume
        target_volume = recover_volume_only(request,
                                            source_volume_id,
                                            source_volume_name,
                                            target_volume_size,
                                            target_volume_name,
                                            volume_type,
                                            backup_zone,
                                            recover_source_id,
                                            recover_source_type)
        # recover potential attachment
        target_vm = recover_attach_vm(request,
                                      source_volume_id,
                                      attachment_server_id,
                                      backup_zone)
        # attach volume to vm
        attach_target_volume_to_vm(request,
                                   source_volume_id,
                                   attachment_server_id,
                                   target_volume,
                                   target_vm,
                                   attach_device)
    elif recover_status == "volume_recovered" and attachment_server_id:
        # recover potential attachment
        target_vm = recover_attach_vm(request,
                                      source_volume_id,
                                      attachment_server_id,
                                      backup_zone)
        # attach volume to vm
        attach_target_volume_to_vm(request,
                                   source_volume_id,
                                   attachment_server_id,
                                   target_volume,
                                   target_vm,
                                   attach_device)
    elif recover_status == "vm_recovered" and attachment_server_id:
        # attach volume to vm
        target_vm = get_target_server(request, attachment_server_id)
        attach_target_volume_to_vm(request,
                                   source_volume_id,
                                   attachment_server_id,
                                   target_volume,
                                   target_vm,
                                   attach_device)
    else:
        print "ERROR, volume:%s has already finished recovery" % \
              source_volume_name
        message = _("ERROR, volume:%s has already finished recovery") % \
                  source_volume_name
        messages.info(request, message)
    return target_volume

