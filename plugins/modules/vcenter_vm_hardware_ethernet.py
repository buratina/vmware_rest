from __future__ import absolute_import, division, print_function

__metaclass__ = type
import socket
import json

DOCUMENTATION = """
module: vcenter_vm_hardware_ethernet
short_description: Handle resource of type vcenter_vm_hardware_ethernet
description: Handle resource of type vcenter_vm_hardware_ethernet
options:
  allow_guest_control:
    description:
    - Flag indicating whether the guest can connect and disconnect the device.
    - If unset, the value is unchanged.
    type: bool
  backing:
    description:
    - 'Physical resource backing for the virtual Ethernet adapter. '
    - ' This field may be modified at any time, and changes will be applied the next
      time the virtual machine is powered on.'
    - If unset, the value is unchanged.
    - 'Validate attributes are:'
    - ' - C(distributed_port) (str): Key of the distributed virtual port that backs
      the virtual Ethernet adapter. Depending on the type of the Portgroup, the port
      may be specified using this field. If the portgroup type is early-binding (also
      known as static), a port is assigned when the Ethernet adapter is configured
      to use the port. The port may be either automatically or specifically assigned
      based on the value of this field. If the portgroup type is ephemeral, the port
      is created and assigned to a virtual machine when it is powered on and the Ethernet
      adapter is connected. This field cannot be specified as no free ports exist
      before use.'
    - May be used to specify a port when the network specified on the Ethernet.BackingSpec.network
      field is a static or early binding distributed portgroup. If unset, the port
      will be automatically assigned to the Ethernet adapter based on the policy embodied
      by the portgroup type.
    - ' - C(network) (str): Identifier of the network that backs the virtual Ethernet
      adapter.'
    - This field is optional and it is only relevant when the value of Ethernet.BackingSpec.type
      is one of STANDARD_PORTGROUP, DISTRIBUTED_PORTGROUP, or OPAQUE_NETWORK.
    - 'When clients pass a value of this structure as a parameter, the field must
      be an identifier for the resource type: Network. When operations return a value
      of this structure as a result, the field will be an identifier for the resource
      type: Network.'
    - ' - C(type) (str): The Ethernet.BackingType enumerated type defines the valid
      backing types for a virtual Ethernet adapter.'
    type: dict
  mac_address:
    description:
    - 'MAC address. '
    - ' This field may be modified at any time, and changes will be applied the next
      time the virtual machine is powered on.'
    - If unset, the value is unchanged. Must be specified if Ethernet.UpdateSpec.mac-type
      is MANUAL. Must be unset if the MAC address type is not MANUAL.
    type: str
  mac_type:
    choices:
    - ASSIGNED
    - GENERATED
    - MANUAL
    description:
    - The Ethernet.MacAddressType enumerated type defines the valid MAC address origins
      for a virtual Ethernet adapter.
    type: str
  nic:
    description:
    - Virtual Ethernet adapter identifier.
    - 'The parameter must be an identifier for the resource type: vcenter.vm.hardware.Ethernet.
      Required with I(state=[''delete'', ''update''])'
    type: str
  pci_slot_number:
    description:
    - Address of the virtual Ethernet adapter on the PCI bus. If the PCI address is
      invalid, the server will change when it the VM is started or as the device is
      hot added.
    - If unset, the server will choose an available address when the virtual machine
      is powered on.
    type: int
  start_connected:
    description:
    - Flag indicating whether the virtual device should be connected whenever the
      virtual machine is powered on.
    - If unset, the value is unchanged.
    type: bool
  state:
    choices:
    - create
    - delete
    - update
    description: []
    type: str
  type:
    choices:
    - E1000
    - E1000E
    - PCNET32
    - VMXNET
    - VMXNET2
    - VMXNET3
    description:
    - The Ethernet.EmulationType enumerated type defines the valid emulation types
      for a virtual Ethernet adapter.
    type: str
  upt_compatibility_enabled:
    description:
    - 'Flag indicating whether Universal Pass-Through (UPT) compatibility should be
      enabled on this virtual Ethernet adapter. '
    - ' This field may be modified at any time, and changes will be applied the next
      time the virtual machine is powered on.'
    - If unset, the value is unchanged. Must be unset if the emulation type of the
      virtual Ethernet adapter is not VMXNET3.
    type: bool
  vm:
    description:
    - Virtual machine identifier.
    - 'The parameter must be an identifier for the resource type: VirtualMachine.'
    type: str
  wake_on_lan_enabled:
    description:
    - 'Flag indicating whether wake-on-LAN shoud be enabled on this virtual Ethernet
      adapter. '
    - ' This field may be modified at any time, and changes will be applied the next
      time the virtual machine is powered on.'
    - If unset, the value is unchanged.
    type: bool
author:
- Ansible VMware team
version_added: 1.0.0
requirements:
- python >= 3.6
"""
IN_QUERY_PARAMETER = []
from ansible.module_utils.basic import env_fallback

try:
    from ansible_module.turbo.module import AnsibleTurboModule as AnsibleModule
except ImportError:
    from ansible.module_utils.basic import AnsibleModule
from ansible_collections.vmware.vmware_rest.plugins.module_utils.vmware_rest import (
    gen_args,
    open_session,
    update_changed_flag,
)


def prepare_argument_spec():
    argument_spec = {
        "vcenter_hostname": dict(
            type="str", required=False, fallback=(env_fallback, ["VMWARE_HOST"])
        ),
        "vcenter_username": dict(
            type="str", required=False, fallback=(env_fallback, ["VMWARE_USER"])
        ),
        "vcenter_password": dict(
            type="str",
            required=False,
            no_log=True,
            fallback=(env_fallback, ["VMWARE_PASSWORD"]),
        ),
        "vcenter_certs": dict(
            type="bool",
            required=False,
            no_log=True,
            fallback=(env_fallback, ["VMWARE_VALIDATE_CERTS"]),
        ),
    }
    argument_spec["wake_on_lan_enabled"] = {
        "type": "bool",
        "operationIds": ["create", "update"],
    }
    argument_spec["vm"] = {
        "type": "str",
        "operationIds": ["create", "delete", "update"],
    }
    argument_spec["upt_compatibility_enabled"] = {
        "type": "bool",
        "operationIds": ["create", "update"],
    }
    argument_spec["type"] = {
        "type": "str",
        "choices": ["E1000", "E1000E", "PCNET32", "VMXNET", "VMXNET2", "VMXNET3"],
        "operationIds": ["create"],
    }
    argument_spec["state"] = {"type": "str", "choices": ["create", "delete", "update"]}
    argument_spec["start_connected"] = {
        "type": "bool",
        "operationIds": ["create", "update"],
    }
    argument_spec["pci_slot_number"] = {"type": "int", "operationIds": ["create"]}
    argument_spec["nic"] = {"type": "str", "operationIds": ["delete", "update"]}
    argument_spec["mac_type"] = {
        "type": "str",
        "choices": ["ASSIGNED", "GENERATED", "MANUAL"],
        "operationIds": ["create", "update"],
    }
    argument_spec["mac_address"] = {"type": "str", "operationIds": ["create", "update"]}
    argument_spec["backing"] = {"type": "dict", "operationIds": ["create", "update"]}
    argument_spec["allow_guest_control"] = {
        "type": "bool",
        "operationIds": ["create", "update"],
    }
    return argument_spec


async def get_device_info(params, session, _url, _key):
    async with session.get(((_url + "/") + _key)) as resp:
        _json = await resp.json()
        entry = _json["value"]
        entry["_key"] = _key
        return entry


async def list_devices(params, session):
    existing_entries = []
    _url = url(params)
    async with session.get(_url) as resp:
        _json = await resp.json()
        devices = _json["value"]
    for device in devices:
        _id = list(device.values())[0]
        existing_entries.append((await get_device_info(params, session, _url, _id)))
    return existing_entries


async def exists(params, session):
    unicity_keys = ["bus", "pci_slot_number"]
    devices = await list_devices(params, session)
    for device in devices:
        for k in unicity_keys:
            if (params.get(k) is not None) and (device.get(k) != params.get(k)):
                break
        else:
            return device


async def main():
    module_args = prepare_argument_spec()
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    session = await open_session(
        vcenter_hostname=module.params["vcenter_hostname"],
        vcenter_username=module.params["vcenter_username"],
        vcenter_password=module.params["vcenter_password"],
    )
    result = await entry_point(module, session)
    module.exit_json(**result)


def url(params):
    return "https://{vcenter_hostname}/rest/vcenter/vm/{vm}/hardware/ethernet".format(
        **params
    )


async def entry_point(module, session):
    func = globals()[("_" + module.params["state"])]
    return await func(module.params, session)


async def _create(params, session):
    accepted_fields = [
        "allow_guest_control",
        "backing",
        "mac_address",
        "mac_type",
        "pci_slot_number",
        "start_connected",
        "type",
        "upt_compatibility_enabled",
        "wake_on_lan_enabled",
    ]
    if "create" == "create":
        _exists = await exists(params, session)
        if _exists:
            return await update_changed_flag({"value": _exists}, 200, "get")
    spec = {}
    for i in accepted_fields:
        if params[i]:
            spec[i] = params[i]
    _url = "https://{vcenter_hostname}/rest/vcenter/vm/{vm}/hardware/ethernet".format(
        **params
    )
    async with session.post(_url, json={"spec": spec}) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        if (
            ("create" == "create")
            and (resp.status in [200, 201])
            and ("value" in _json)
        ):
            if type(_json["value"]) == dict:
                _id = list(_json["value"].values())[0]
            else:
                _id = _json["value"]
            _json = {"value": (await get_device_info(params, session, _url, _id))}
        return await update_changed_flag(_json, resp.status, "create")


async def _delete(params, session):
    _url = "https://{vcenter_hostname}/rest/vcenter/vm/{vm}/hardware/ethernet/{nic}".format(
        **params
    ) + gen_args(
        params, IN_QUERY_PARAMETER
    )
    async with session.delete(_url) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        return await update_changed_flag(_json, resp.status, "delete")


async def _update(params, session):
    accepted_fields = [
        "allow_guest_control",
        "backing",
        "mac_address",
        "mac_type",
        "start_connected",
        "upt_compatibility_enabled",
        "wake_on_lan_enabled",
    ]
    if "update" == "create":
        _exists = await exists(params, session)
        if _exists:
            return await update_changed_flag({"value": _exists}, 200, "get")
    spec = {}
    for i in accepted_fields:
        if params[i]:
            spec[i] = params[i]
    _url = "https://{vcenter_hostname}/rest/vcenter/vm/{vm}/hardware/ethernet/{nic}".format(
        **params
    )
    async with session.patch(_url, json={"spec": spec}) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        if (
            ("update" == "create")
            and (resp.status in [200, 201])
            and ("value" in _json)
        ):
            if type(_json["value"]) == dict:
                _id = list(_json["value"].values())[0]
            else:
                _id = _json["value"]
            _json = {"value": (await get_device_info(params, session, _url, _id))}
        return await update_changed_flag(_json, resp.status, "update")


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
