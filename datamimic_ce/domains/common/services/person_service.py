# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.models.person import Person


class PersonService(BaseDomainService[Person]):
    """Service for managing person data.

    This class provides methods for creating, retrieving, and managing person data.
    """

    def __init__(self):
        super().__init__(PersonGenerator(), Person)
