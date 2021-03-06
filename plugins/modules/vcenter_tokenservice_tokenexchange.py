from __future__ import absolute_import, division, print_function

__metaclass__ = type
import socket
import json

DOCUMENTATION = """
module: vcenter_tokenservice_tokenexchange
short_description: Handle resource of type vcenter_tokenservice_tokenexchange
description: Handle resource of type vcenter_tokenservice_tokenexchange
options:
  actor_token:
    description:
    - A security token that represents the identity of the acting party. Typically,
      this will be the party that is authorized to use the requested security token
      and act on behalf of the subject.
    type: str
  actor_token_type:
    description:
    - An identifier, that indicates the type of the security token in the {@link ExchangeSpec#actor_token}
      parameter.
    type: str
  audience:
    description:
    - The logical name of the target service where the client intends to use the requested
      security token. This serves a purpose similar to the {@link ExchangeSpec#resource}
      parameter, but with the client providing a logical name rather than a location.
    type: str
  grant_type:
    description:
    - The value of {@link TokenExchange#TOKEN_EXCHANGE_GRANT} indicates that a token
      exchange is being performed.
    type: str
  requested_token_type:
    description:
    - An identifier for the type of the requested security token. If the requested
      type is unspecified, the issued token type is at the discretion of the server
      and may be dictated by knowledge of the requirements of the service or resource
      indicated by the {@link ExchangeSpec#resource} or {@link ExchangeSpec#audience}
      parameter.
    type: str
  resource:
    description:
    - Indicates the location of the target service or resource where the client intends
      to use the requested security token.
    type: str
  scope:
    description:
    - A list of space-delimited, case-sensitive strings, that allow the client to
      specify the desired scope of the requested security token in the context of
      the service or resource where the token will be used.
    type: str
  state:
    choices:
    - exchange
    description: []
    type: str
  subject_token:
    description:
    - A security token that represents the identity of the party on behalf of whom
      exchange is being made. Typically, the subject of this token will be the subject
      of the security token issued. Token is base64-encoded.
    type: str
  subject_token_type:
    description:
    - An identifier, that indicates the type of the security token in the {@link ExchangeSpec#subject_token}
      parameter.
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
    argument_spec["subject_token_type"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["subject_token"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["state"] = {"type": "str", "choices": ["exchange"]}
    argument_spec["scope"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["resource"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["requested_token_type"] = {
        "type": "str",
        "operationIds": ["exchange"],
    }
    argument_spec["grant_type"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["audience"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["actor_token_type"] = {"type": "str", "operationIds": ["exchange"]}
    argument_spec["actor_token"] = {"type": "str", "operationIds": ["exchange"]}
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
    return "https://{vcenter_hostname}/rest/vcenter/tokenservice/token-exchange".format(
        **params
    )


async def entry_point(module, session):
    func = globals()[("_" + module.params["state"])]
    return await func(module.params, session)


async def _exchange(params, session):
    accepted_fields = [
        "actor_token",
        "actor_token_type",
        "audience",
        "grant_type",
        "requested_token_type",
        "resource",
        "scope",
        "subject_token",
        "subject_token_type",
    ]
    if "exchange" == "create":
        _exists = await exists(params, session)
        if _exists:
            return await update_changed_flag({"value": _exists}, 200, "get")
    spec = {}
    for i in accepted_fields:
        if params[i]:
            spec[i] = params[i]
    _url = "https://{vcenter_hostname}/rest/vcenter/tokenservice/token-exchange".format(
        **params
    )
    async with session.post(_url, json={"spec": spec}) as resp:
        try:
            if resp.headers["Content-Type"] == "application/json":
                _json = await resp.json()
        except KeyError:
            _json = {}
        if (
            ("exchange" == "create")
            and (resp.status in [200, 201])
            and ("value" in _json)
        ):
            if type(_json["value"]) == dict:
                _id = list(_json["value"].values())[0]
            else:
                _id = _json["value"]
            _json = {"value": (await get_device_info(params, session, _url, _id))}
        return await update_changed_flag(_json, resp.status, "exchange")


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
