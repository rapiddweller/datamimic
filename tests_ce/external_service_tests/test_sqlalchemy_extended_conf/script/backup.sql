DROP TABLE IF EXISTS public.none_as_null;

CREATE TABLE public.none_as_null (
    my_id integer NOT NULL,
    data_value_json jsonb
--     data_value_text text
);
