DROP TABLE IF EXISTS public.db_postgres_test_variable_with_selector;

CREATE TABLE public.db_postgres_test_variable_with_selector (
    id integer NOT NULL,
    text text NOT NULL,
    number integer NOT NULL
);

INSERT INTO public.db_postgres_test_variable_with_selector (id, text, number) VALUES
    (1, 'Name 1', 1),
    (2, 'Name 2', 2),
    (3, 'Name 3', 3);
