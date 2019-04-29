from collections import namedtuple

import boto3
import os
import subprocess
from diskcache import Cache
from iterfzf import iterfzf

Config = namedtuple("Config", "template, use_ip, region, ttl")

DEFAULT_TEMPLATE = "{i.name} @ {i.public_ip}"


class Instance:

    def __init__(self, _id, public_dns, public_ip, tags):
        self.id = _id
        self.public_dns = public_dns
        self.public_ip = public_ip
        self.tags = tags

    def __getattr__(self, item):
        if self.__dict__.get(item):
            return self.__dict__[item]
        return self.tag(item)

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __lt__(self, other):
        return self.name.lower() < other.name.lower()

    def tag(self, name, default=""):
        return self.tags.get(name, default)

    @property
    def name(self) -> str:
        return self.tag("Name")

    def serialize(self):
        return self.__dict__

    @classmethod
    def load(cls, data):
        return cls(data["id"], data["public_dns"], data["public_ip"], data["tags"])


def _get_cache():
    from os.path import expanduser, join
    home = expanduser("~")
    cache = Cache(join(home, ".aws-qc-cahce"))
    return cache


def _get_config():
    template = os.environ.get("AWS_QC_TEMPLATE", DEFAULT_TEMPLATE)
    use_ip = os.environ.get("AWS_QC_USE_IP", False)
    region = os.environ.get("AWS_QC_REGION", "us-west-2")
    ttl = os.environ.get("AWS_QC_CACHE_TTL", 3000)
    return Config(template=template, use_ip=use_ip, region=region, ttl=ttl)


def _expand_tags(in_tags):
    tags = {}
    for tag in in_tags:
        tags[tag["Key"]] = tag["Value"]
    return tags


def _get_instances(region, ttl):
    cache = _get_cache()
    instances = cache.get('instances', default=None)
    if instances:
        return [Instance.load(i) for i in instances]
    if not instances:
        instances = _fetch_instances(region)
        cache.set('instances', [i.serialize() for i in instances], expire=ttl)
    return instances


def _fetch_instances(region):
    ec2 = boto3.resource('ec2', region)
    filters = [
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ]

    instances = ec2.instances.filter(Filters=filters)

    def _process_tags(tags):
        ret = {}
        for tag in tags:
            ret[tag["Key"]] = str(tag["Value"])
        return ret

    return [Instance(i.id, i.public_dns_name, i.public_ip_address, _process_tags(i.tags)) for i in instances]


def _format_data(instances, template):
    for i in instances:
        yield template.format(i=i) + " <id:{}>".format(i.id)


def _extract_instance_id(instance_string):
    import re
    match = re.search('<id:(i-[a-zA-Z0-9]+)>', instance_string)

    if match:
        return match.group(1)
    return None


def _ssh(ssh_target):
    subprocess.call("ssh {}".format(ssh_target), shell=True, executable='/bin/bash')


def main():
    config = _get_config()
    instances = _get_instances(config.region, config.ttl)
    instances = sorted(instances, reverse=True)  # instances should be alphabetically sorted
    result = iterfzf(_format_data(instances, config.template), multi=False)
    instance_id = _extract_instance_id(result)
    target_instance = list(filter(lambda i: i.id == instance_id, instances))[0]
    ssh_target = target_instance.public_ip if config.use_ip else target_instance.public_dns
    _ssh(ssh_target)
    exit()


if __name__ == '__main__':
    main()
