import psycopg
from pydantic import SecretStr

BRAIN_READ_VIEWS: tuple[str, ...] = (
    "brain_read.eligible_items_v1",
    "brain_read.eligible_relationships_v1",
    "brain_read.adopted_rules_v1",
)
"""The read-only eligibility views owned by busmora-api (BTD §7.5, BTD-ADR-08)."""

AI_RUNTIME_SCHEMA = "ai_runtime"
"""Where the LangGraph checkpointer keeps its tables (BTD-ADR-09)."""


class MissingDatabaseObjectError(Exception):
    """A view or schema this role depends on does not exist or is not visible to it."""


class PostgresProbe:
    name = "postgres"

    def __init__(
        self,
        dsn: SecretStr,
        *,
        required_relations: tuple[str, ...] = (),
        required_schemas: tuple[str, ...] = (),
        connect_timeout_seconds: int = 2,
    ) -> None:
        self._dsn = dsn
        self._relations = required_relations
        self._schemas = required_schemas
        self._connect_timeout = connect_timeout_seconds

    async def check(self) -> None:
        async with await psycopg.AsyncConnection.connect(
            self._dsn.get_secret_value(), connect_timeout=self._connect_timeout
        ) as conn:
            await conn.execute("SELECT 1")
            for relation in self._relations:
                cur = await conn.execute(
                    "SELECT has_table_privilege(to_regclass(%s), 'SELECT')", (relation,)
                )
                row = await cur.fetchone()
                if row is None or row[0] is not True:
                    raise MissingDatabaseObjectError(relation)
            for schema in self._schemas:
                cur = await conn.execute(
                    "SELECT has_schema_privilege(to_regnamespace(%s), 'USAGE')", (schema,)
                )
                row = await cur.fetchone()
                if row is None or row[0] is not True:
                    raise MissingDatabaseObjectError(schema)
