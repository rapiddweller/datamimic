DROP TABLE IF EXISTS public.selector_distribution_matrix;

CREATE TABLE public.selector_distribution_matrix (
    id integer PRIMARY KEY,
    text text NOT NULL
);

INSERT INTO public.selector_distribution_matrix (id, text)
SELECT g, 'Name ' || g FROM generate_series(1, 15) AS g;

-- Deliberately has DUPLICATE rows once id is excluded from the read (3 distinct categories,
-- each repeated 5x) - a unique="true" test against id alone would only prove dedup is a
-- harmless no-op on an already-distinct (PRIMARY KEY) pool, not that it collapses real repeats.
DROP TABLE IF EXISTS public.selector_distribution_matrix_dupes;

CREATE TABLE public.selector_distribution_matrix_dupes (
    id integer PRIMARY KEY,
    category text NOT NULL
);

INSERT INTO public.selector_distribution_matrix_dupes (id, category)
SELECT g, 'Cat' || ((g - 1) % 3 + 1) FROM generate_series(1, 15) AS g;
