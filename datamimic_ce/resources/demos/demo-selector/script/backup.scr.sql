DROP TABLE IF EXISTS public.db_postgres_demo;

CREATE TABLE public.db_postgres_demo (
    id integer NOT NULL,
    name text NOT NULL
);

INSERT INTO public.db_postgres_demo (id, name) VALUES
    (1, 'Name 1'),
    (2, 'Name 2'),
    (3, 'Name 3'),
    (4, 'Name 4'),
    (5, 'Name 5'),
    (6, 'Name 6'),
    (7, 'Name 7'),
    (8, 'Name 8'),
    (9, 'Name 9'),
    (10, 'Name 10');
