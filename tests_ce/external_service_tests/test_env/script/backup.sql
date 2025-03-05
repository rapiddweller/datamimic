DROP TABLE IF EXISTS public.db_postgres_types4;

CREATE TABLE public.db_postgres_types4 (
    id integer NOT NULL,
    text text NOT NULL
);

INSERT INTO public.db_postgres_types4 (id, text) VALUES
    (1, 'Name 1'),
    (2, 'Name 2'),
    (3, 'Name 3'),
    (4, 'Name 4'),
    (5, 'Name 5');