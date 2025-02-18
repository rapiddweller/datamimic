DROP TABLE IF EXISTS public.db_postgres_test_variable_source_with_name_only;

CREATE TABLE public.db_postgres_test_variable_source_with_name_only (
    id integer NOT NULL,
    text text NOT NULL,
    number integer NOT NULL
);

INSERT INTO public.db_postgres_test_variable_source_with_name_only (id, text, number) VALUES
    (1, 'Name 1', 1),
    (2, 'Name 2', 2),
    (3, 'Name 3', 3);
