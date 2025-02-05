
def generate_mock_data(total_records=3000, title="Mock Title", year=2020):
    """Generate mock data for testing."""
    return [{"id": f"movie_{i + 1}", "title": f"{title} {i + 1}", "year": year} for i in range(total_records)]


class MockSetupContext:
    def __init__(self, task_id, descriptor_dir):
        self.task_id = task_id
        self.descriptor_dir = descriptor_dir
        self.default_separator = ","
        self.default_line_separator = "\n"
        self.default_encoding = "utf-8"
        self.use_mp = False

    def get_client_by_id(self, client_id):
        # Return a dummy client or data, replace MagicMock dependency
        return {"id": client_id, "data": "mock_client_data"}
