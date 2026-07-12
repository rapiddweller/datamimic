DROP TABLE IF EXISTS public.selector_distribution_matrix;

CREATE TABLE public.selector_distribution_matrix (
    id integer PRIMARY KEY,
    text text NOT NULL
);

INSERT INTO public.selector_distribution_matrix (id, text)
SELECT g, 'Name ' || g FROM generate_series(1, 15) AS g;
