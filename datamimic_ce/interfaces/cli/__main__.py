from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    load_dotenv(Path.cwd() / ".env", override=False)
    from datamimic_ce.interfaces.cli._app import app

    app(prog_name="DATAMIMIC")


if __name__ == "__main__":
    main()
