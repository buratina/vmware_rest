from __future__ import absolute_import, division, print_function

__metaclass__ = type
import socket
import json

DOCUMENTATION = """
module: vcenter_content_registries_harbor_projects
short_description: Handle resource of type vcenter_content_registries_harbor_projects
description: Handle resource of type vcenter_content_registries_harbor_projects
options:
  action:
    choices:
    - purge
    description:
    - action=purge Required with I(state=['purge'])
    type: str
  name:
    description:
    - 'Name of the Harbor project. Should be between 2-63 characters long alphanumeric
      string and may contain the following characters: a-z,0-9, and ''-''. Must be
      starting with characters or numbers, with the ''-'' character allowed anywhere
      except the first or last character. Required with I(state=[''create''])'
    type: str
  project:
    description:
    - Identifier of the Harbor project. Required with I(state=['delete', 'purge'])
    type: str
  registry:
    description:
    - Identifier of the Registry.
    type: str
  scope:
    choices:
    - PRIVATE
    - PUBLIC
    description:
    - The {@name Scope} in a project defines access levels of the project. Required
      with I(state=['create'])
    type: str
  state:
    choices:
    - create
    - delete
    - purge
    description: []
    type: str
author:
- Ansible VMware team
version_added: 1.0.0
requirements:
- python >= 3.6
"""
IN_QUERY_PARAMETER = ["action"]
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
    argument_spec["state"] = {"type": "str", "choices": ["create", "delete", "purge"]}
    argument_spec["scope"] = {
        "type": "str",
        "choices": ["PRIVATE", "PUBLIC"],
        "operationIds": ["create"],
    }
    argument_spec["registry"] = {
        "type": "str",
        "operationIds": ["create", "delete", "purge"],
    }
    argument_spec["project"] = {"type": "str", "operationIds": ["delete", "purge"]}
    argument_spec["name"] = {"type": "str", "operationIds": ["create"]}
    argument_spec["action"] = {
        "type": "str",
        "choices": ["purge"],
        "operationIds": ["purge"],
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
    return "https://{vcenter_hostname}/rest/vcenter/content/registries/harbor/{registry}/projects".format(
        **params
    )


async def entry_point(module, session):
    func = globals()[("_" + module.params["state"])]
    return await func(module.params, session)


async def _create(params, session):
    accepted_fields = ["name", "scope"]
    if "create" == "create":
        _exists = await exists(params, session)
        if _exists:
            return await update_changed_flag({"value": _exists}, 200, "get")
    spec = {}
    for i in accepted_fields:
        if params[i]:
            spec[i] = params[i]
    _url = "https://{vcenter_hostname}/rest/vcenter/content/registries/harbor/{registry}/projects".format(
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
    _url = "https://{vcenter_hostname}/rest/vcenter/content/registries/harbor/{registry}/projects/{project}".format(
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


async def _purge(params, session):
    _url = "https://{vcenter_hostname}/rest/vcenter/content/registries/harbor/{registry}/projects/{project}".format(
        **params
    ) + gen_args(
        params, IN_QUERY_PARAMETER
    )
    async with session.post(_url) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        return await update_changed_flag(_json, resp.status, "purge")


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
