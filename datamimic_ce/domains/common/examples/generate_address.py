from datamimic_ce.domains.common.services.address_service import AddressService


def generate_address():
    """
    Generate a single address
    """
    address_service = AddressService()
    address = address_service.generate()
    print(address.to_dict())


def generate_batch_address():
    """
    Generate a batch of addresses
    """
    address_service = AddressService()
    addresses = address_service.generate_batch(10)
    for address in addresses:
        print(address.to_dict())


if __name__ == "__main__":
    print("Generating single address:")
    generate_address()
    print("\nGenerating batch of addresses:")
    generate_batch_address()
