from src.domains import User
from src.exceptions import NotFound
from src.repositories import UserRepository, user_repo


class UserApp:
    repo: UserRepository = user_repo

    def get(self, user_id: str) -> User | None:
        return self.repo.get(db_id=user_id)

    def bulk_get(self, user_ids: list[str]) -> list[User]:
        return self.repo.bulk_get(db_ids=user_ids)

    def is_exist(self, user_id: str) -> bool:
        return self.repo.is_exist(db_id=user_id)

    def create(self, data: dict[str]) -> User:
        user = User.factory(**data)
        # TODO: we can add business logic here in future
        return self.repo.create(user)

    def update(self, data: dict[str], user: User | None = None) -> User:
        if user is None:
            user = self.get(user_id=data.get('user_id'))
            if not user:
                raise NotFound('User not found', user_id=data.get('user_id'))

        user.model_update(data)

        # TODO: update it only if fields were changed

        return self.repo.update(entity=user)

    def delete(self, user_id: str) -> None:
        return self.repo.delete(db_id=user_id)

    # def get_aggregate(self, user: User, platform: Platform | None = None) -> UserAggregate:
    #     ...


user_app_impl = UserApp()
