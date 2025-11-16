from fastapi import APIRouter


# TODO: док строку
def build_router(module_name: str, root_prefix: str = "/api") -> APIRouter:
    """
    module_name: например 'src.api.admin.user.audit'

    → prefix: '/api/admin/user'
    """
    # отрезаем 'src.' и всё до 'api.'
    _, _, tail = module_name.partition("api.")
    # tail: 'admin.user.audit'

    parts = tail.split(".")[:-1]   # ['admin', 'user']
    prefix = root_prefix + "/" + "/".join(parts) if parts else root_prefix
    return APIRouter(prefix=prefix)
