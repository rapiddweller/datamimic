# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.literal_generators.domain_generator import DomainGenerator


def test_domain_generator():
    for _ in range(10):
        domain = DomainGenerator().generate()
        assert isinstance(domain, str)
        assert " " not in domain, "Domain should not contain white spaces"
        assert domain.islower(), f"Domain need to be in lower case, got {domain}"
