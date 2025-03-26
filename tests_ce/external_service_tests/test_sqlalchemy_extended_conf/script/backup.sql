DROP TABLE IF EXISTS public.none_as_null;

CREATE TABLE public.none_as_null (
    my_id integer NOT NULL,
    data_null jsonb,
    data_none jsonb,
    data_text text
);
