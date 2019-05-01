import re

from .data import flatten
from .string_tools import substring_in

import logging
log = logging.getLogger(__name__)

try:
    import docker
except ImportError:
    log.error('python docker package not present')


def convert_docker_absolute_windows_path(path):
    """
    >>> convert_docker_absolute_windows_path('/path/linux')
    '/path/linux'
    >>> convert_docker_absolute_windows_path('C:\\\\Users\\\\me')
    '//C//Users/me'
    """
    RE_WINDOWS_PATH_PREFIX = re.compile(r'^(\w):\\')
    if RE_WINDOWS_PATH_PREFIX.match(path):
        path = RE_WINDOWS_PATH_PREFIX.sub(r'//\1//', path)
        path = path.replace('\\', '/')
    return path


def clean_docker_compose_name(value):
    """
    docker-compose names are compacted - we reproduce the same logic here.

    >>> clean_docker_compose_name('company.best_build11')
    'companybestbuild11'
    """
    return re.sub(r'[-_.]', '', value)


def docker_image_in_registry(image_name, docker_client=None):
    """
    https://stackoverflow.com/questions/32113330/check-if-imagetag-combination-already-exists-on-docker-hub
    """
    docker_client = docker_client or docker.from_env()

    try:
        return docker_client.images.get_registry_data(image_name)
    except docker.errors.APIError:
        pass
        # may not have correct docker version to utilise this
    try:
        return docker_client.images.pull(image_name)
    except docker.errors.NotFound:
        pass
    return False


def clean_images(image_prefix, docker_client=None, dry_run=False):
    """
    Remove all docker images managed/created from this project (images prefixed with {IMAGE_PREFIX}).
    """
    docker_client = docker_client or docker.from_env()

    for image in docker_client.images.list():
        if substring_in(image_prefix, flatten(image.tags)):
            log.info(f'remove {image.id}')
            if not dry_run:
                try:
                    docker_client.images.remove(image.id, force=True)
                except Exception as ex:
                    import traceback
                    traceback.print_exc()


def clean_containers(project_id, ids_to_remove=(), docker_client=None, dry_run=True):
    """
    Remove
     - containers
     - volumes
     - networks
    """
    ids_to_remove = ids_to_remove or ('',)
    ids_to_remove = tuple(f'{project_id}{_id}' for _id in ids_to_remove)

    docker_client = docker_client or docker.from_env()

    def remove_items(title, items, ids_to_remove, **kwargs):
        for item in items:
            for _id in ids_to_remove:
                if _id in item.name:
                    log.info(f'Removing {title} -> {item.name}')
                    if not dry_run:
                        item.remove(**kwargs)

    log.info(f"""Removing docker state for {ids_to_remove}""")
    remove_items('containers', docker_client.containers.list(), ids_to_remove, force=True)
    remove_items('volumes', docker_client.volumes.list(), ids_to_remove)
    remove_items('networks', docker_client.networks.list(), ids_to_remove)
