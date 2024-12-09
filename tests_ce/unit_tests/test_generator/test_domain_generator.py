# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from datamimic_ce.generators.domain_generator import DomainGenerator


def test_domain_generator():
    for _ in range(10):
        domain = DomainGenerator(generated_count=1).generate()
        assert isinstance(domain, str)
        assert " " not in domain, "Domain should not contain white spaces"
        assert domain.islower(), f"Domain need to be in lower case, got {domain}"
