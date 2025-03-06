from datamimic_ce.domains.common.generators.address_generator import AddressGenerator


def generate_address():
    address_generator = AddressGenerator()
    address = address_generator.generate()
    print(address.to_dict())

def generate_batch_address():
    address_generator = AddressGenerator()
    addresses = address_generator.generate_batch(10)
    for address in addresses:
        print(address.to_dict())

if __name__ == "__main__":
    print("Generating single address:")
    generate_address()
    print("\nGenerating batch of addresses:")
    generate_batch_address()