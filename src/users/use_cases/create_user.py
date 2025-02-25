import re
from typing import Any

import structlog
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from sentry_sdk import start_transaction

from core.base_model import Model
from core.use_case import UseCase, UseCaseRequest, UseCaseResponse
from event_log.models import EventLogRecord
from users.models import User

logger = structlog.get_logger(__name__)


class UserCreated(Model):
    email: str
    first_name: str
    last_name: str


class CreateUserRequest(UseCaseRequest):
    email: str
    first_name: str = ''
    last_name: str = ''


class CreateUserResponse(UseCaseResponse):
    result: User | None = None
    error: str = ''


class CreateUser(UseCase):
    def _get_context_vars(self, request: UseCaseRequest) -> dict[str, Any]:
        return {
            'email': request.email,
            'first_name': request.first_name,
            'last_name': request.last_name,
        }

    def _execute(self, request: CreateUserRequest) -> CreateUserResponse:
        with start_transaction(op="user_creation", name="CreateUser"):
            logger.info('creating a new user')

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=request.email,
                    defaults={
                        'first_name': request.first_name, 'last_name': request.last_name,
                    },
                )

                if created:
                    logger.info('user has been created')
                    self._log(user)
                    return CreateUserResponse(result=user)

            logger.error('unable to create a new user')
            return CreateUserResponse(error='User with this email already exists')

    def _log(self, user: User) -> None:
        EventLogRecord.objects.create(
            event_data=self._convert_data(
                UserCreated(
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                ),
            ),
        )

    def _convert_data(self, data: Model) -> tuple[Any]:
        return (
                self._to_snake_case(data.__class__.__name__),
                timezone.now().isoformat(),
                settings.ENVIRONMENT,
                data.model_dump_json(),
            )

    def _to_snake_case(self, event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
