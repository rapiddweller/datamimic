DROP TABLE IF EXISTS public.db_postgres_types4;

CREATE TABLE public.db_postgres_types4 (
    id integer NOT NULL,
    text text NOT NULL,
    number integer NOT NULL
);

INSERT INTO public.db_postgres_types4 (id, text, number) VALUES
    (1, 'Name 1', 1),
    (2, 'Name 2', 2),
    (3, 'Name 3', 3);