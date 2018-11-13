import logging
log = logging.getLogger(__name__)


def clean_docker(project_id, ids_to_remove=(), docker_client=None, dry_run=True):
    """
    Remove 
     - containers
     - volumes
     - networks
    """
    ids_to_remove = ids_to_remove or ('',)
    ids_to_remove = tuple(f'{project_id}{_id}' for _id in ids_to_remove)

    if not docker_client:
        import docker
        docker_client = docker.from_env()

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
