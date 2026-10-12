from datetime import timedelta


class Duration: ...


class ISO8601Error(Exception): ...


def parse_duration(datestring: str) -> timedelta | Duration: ...
