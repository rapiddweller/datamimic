import logging
from functools import lru_cache

from datamimic_ce.domains.api import Converter, CustomConverter
from datamimic_ce.engine.runtime.api import Context, SetupContext

logger = logging.getLogger("DATAMIMIC")


class CustomBusinessMappingConverter(CustomConverter):
    _initialized: bool = False
    _client_id: str = "mapping"
    _database_client = None

    def __init__(self, context: SetupContext | Context):
        if not isinstance(context, SetupContext):
            raise ValueError("Context must be of type SetupContext")

        if not self.__class__._initialized:
            # Get client (Database) from context
            client = context.get_client_by_id(self._client_id)

            from datamimic_ce.engine.io.api import DatabaseClient

            if client is None:
                raise ValueError("Client with id 'mapping' not found")
            elif not isinstance(client, DatabaseClient):
                raise ValueError(f"Client with id 'mapping' is not a DatabaseClient, but a {type(client)}")
            elif isinstance(client, DatabaseClient):
                self.__class__._database_client = client
                logger.debug(f"The table has {client.count_table_length('business_mapping')} rows")
                self.__class__._initialized = True

    @staticmethod
    def create_sql_query(parsed_data: dict[str, str | int | list[str]]) -> str:
        # logger.debug(f"Parsed data: {parsed_data}, start creating SQL query...")

        # Extract the columns to be selected
        selected_columns = parsed_data["output_columns"]
        if isinstance(selected_columns, str | list):
            output_columns = ", ".join(selected_columns)
        else:
            raise TypeError("can only join an iterable")

        # logger.debug(f"Output columns: {output_columns}, start creating WHERE clause...")

        # Construct the WHERE clause by combining all key-value pairs with AND, excluding 'output_columns'
        filters = [
            f"{key} = {value}" if isinstance(value, int) else f"{key} = '{value}'"
            for key, value in parsed_data.items()
            if key != "output_columns"
        ]

        # Join filters with ' AND ' only if there are more than one filter
        where_clause = " AND ".join(filters) if filters else ""
        # logger.debug(f"WHERE clause: {where_clause}")

        # Construct the final SQL query
        sql_query = f"SELECT {output_columns} FROM business_mapping WHERE {where_clause} LIMIT 1"
        # logger.debug(f"SQL query: {sql_query}")
        return sql_query

    @lru_cache(maxsize=1000)  # noqa: B019
    def convert(self, value: str):
        """
        Generate data and set this value to current product
        :param value:
        :return:
        """
        if self.__class__._database_client is None:
            raise ValueError("Database client is not initialized")

        # Regular expression pattern to match the key-value pairs
        import re

        pattern = re.compile(r"(\w+)=\[([^\]]*)\]|(\w+)=([^,]+)")

        # Initialize the dictionary to hold the parsed values
        parsed_data: dict[str, str | int | list[str]] = {}

        # Iterate over all matches in the input string
        last_value: str | int | list[str] = value
        for match in pattern.finditer(value):
            if match.group(1):
                # Match for list values (e.g., output_column=['idTop','idSub'])
                key = match.group(1)
                last_value = [
                    item.strip().strip("'") for item in match.group(2).split(",")
                ]
            else:
                # Match for single values (e.g., countryCode=234, city='Hamburg')
                key = match.group(3)
                scalar_value = match.group(4).strip().strip("'")
                # Convert value to integer if it is a digit
                last_value = int(scalar_value) if scalar_value.isdigit() else scalar_value

            # Add the key-value pair to the parsed_data dictionary
            if key is not None:
                parsed_data[key] = last_value

        sql_query = self.create_sql_query(parsed_data)
        result = self.__class__._database_client.get_by_page_with_query(sql_query)
        # Return the first row of the result as a dictionary
        if result:
            return result[0]
        else:
            raise ValueError(f"Mapping not found for value: {last_value}")


def create_mapping_cmd(city) -> str:
    return f"output_columns=['idTop', 'idSub'], city='{city}'"


class TransactionTypeConverter(Converter):
    def convert(self, value: object) -> str:
        transaction_types: dict[object, str] = {
            "Completed": "DONE",
            "Pending": "WAITING",
            "Failed": "ERROR",
        }
        return transaction_types.get(value, "OTHER")


class CurrencySymbolConverter(Converter):
    def convert(self, value: object) -> str:
        currency_symbols: dict[object, str] = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
        return currency_symbols.get(value, "Unknown currency code")
