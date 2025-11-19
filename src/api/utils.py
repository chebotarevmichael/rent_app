from fastapi import APIRouter


def build_router(module_name: str, root_prefix: str = '/api') -> APIRouter:
    """
    Add handler to list of endpoints.
    Swagger path is equal of path in project

    Example:
        in project: 'src/api/admin/user/audit.py'
        in swagger: 'POST /api/admin/user/audit'
    """

    _, _, tail = module_name.partition('api.')
    parts = tail.split('.')[:-1]
    prefix = root_prefix + '/' + '/'.join(parts) if parts else root_prefix
    return APIRouter(prefix=prefix)
