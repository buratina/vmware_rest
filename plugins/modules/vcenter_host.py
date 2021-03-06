from __future__ import absolute_import, division, print_function

__metaclass__ = type
import socket
import json

DOCUMENTATION = """
module: vcenter_host
short_description: Handle resource of type vcenter_host
description: Handle resource of type vcenter_host
options:
  folder:
    description:
    - Host and cluster folder in which the new standalone host should be created.
    - This field is currently required. In the future, if this field is unset, the
      system will attempt to choose a suitable folder for the host; if a folder cannot
      be chosen, the host creation operation will fail.
    - 'When clients pass a value of this structure as a parameter, the field must
      be an identifier for the resource type: Folder. When operations return a value
      of this structure as a result, the field will be an identifier for the resource
      type: Folder.'
    type: str
  force_add:
    description:
    - Whether host should be added to the vCenter Server even if it is being managed
      by another vCenter Server. The original vCenterServer loses connection to the
      host.
    - If unset, forceAdd is default to false.
    type: bool
  host:
    description:
    - Identifier of the host to be deleted.
    - 'The parameter must be an identifier for the resource type: HostSystem. Required
      with I(state=[''delete''])'
    type: str
  hostname:
    description:
    - The IP address or DNS resolvable name of the host. Required with I(state=['create'])
    type: str
  password:
    description:
    - The password for the administrator account on the host. Required with I(state=['create'])
    type: str
  port:
    description:
    - The port of the host.
    - If unset, port 443 will be used.
    type: int
  state:
    choices:
    - create
    - delete
    description: []
    type: str
  thumbprint:
    description:
    - 'The thumbprint of the SSL certificate, which the host is expected to have.
      The thumbprint is always computed using the SHA1 hash and is the string representation
      of that hash in the format: xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
      where, ''x'' represents a hexadecimal digit.'
    - This field is optional and it is only relevant when the value of Host.CreateSpec.thumbprint-verification
      is THUMBPRINT.
    type: str
  thumbprint_verification:
    choices:
    - NONE
    - THUMBPRINT
    description:
    - The Host.CreateSpec.ThumbprintVerification enumerated type defines the thumbprint
      verification schemes for a host's SSL certificate. Required with I(state=['create'])
    type: str
  user_name:
    description:
    - The administrator account on the host. Required with I(state=['create'])
    type: str
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
    argument_spec["user_name"] = {
        "nolog": True,
        "type": "str",
        "operationIds": ["create"],
    }
    argument_spec["thumbprint_verification"] = {
        "type": "str",
        "choices": ["NONE", "THUMBPRINT"],
        "operationIds": ["create"],
    }
    argument_spec["thumbprint"] = {"type": "str", "operationIds": ["create"]}
    argument_spec["state"] = {"type": "str", "choices": ["create", "delete"]}
    argument_spec["port"] = {"type": "int", "operationIds": ["create"]}
    argument_spec["password"] = {
        "nolog": True,
        "type": "str",
        "operationIds": ["create"],
    }
    argument_spec["hostname"] = {"type": "str", "operationIds": ["create"]}
    argument_spec["host"] = {"type": "str", "operationIds": ["delete"]}
    argument_spec["force_add"] = {"type": "bool", "operationIds": ["create"]}
    argument_spec["folder"] = {"type": "str", "operationIds": ["create"]}
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
    return "https://{vcenter_hostname}/rest/vcenter/host".format(**params)


async def entry_point(module, session):
    func = globals()[("_" + module.params["state"])]
    return await func(module.params, session)


async def _create(params, session):
    accepted_fields = [
        "folder",
        "force_add",
        "hostname",
        "password",
        "port",
        "thumbprint",
        "thumbprint_verification",
        "user_name",
    ]
    if "create" == "create":
        _exists = await exists(params, session)
        if _exists:
            return await update_changed_flag({"value": _exists}, 200, "get")
    spec = {}
    for i in accepted_fields:
        if params[i]:
            spec[i] = params[i]
    _url = "https://{vcenter_hostname}/rest/vcenter/host".format(**params)
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
    _url = "https://{vcenter_hostname}/rest/vcenter/host/{host}".format(
        **params
    ) + gen_args(params, IN_QUERY_PARAMETER)
    async with session.delete(_url) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        return await update_changed_flag(_json, resp.status, "delete")


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
