--
-- PostgreSQL database dump
--

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 17.0

-- Started on 2026-05-01 10:34:27

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'SQL_ASCII';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 227 (class 1259 OID 16477)
-- Name: action; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.action (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying
);


--
-- TOC entry 226 (class 1259 OID 16476)
-- Name: action_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3496 (class 0 OID 0)
-- Dependencies: 226
-- Name: action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_id_seq OWNED BY public.action.id;


--
-- TOC entry 225 (class 1259 OID 16456)
-- Name: bucket; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bucket (
    id integer NOT NULL,
    name character varying NOT NULL
);


--
-- TOC entry 224 (class 1259 OID 16455)
-- Name: bucket_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.bucket ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.bucket_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 219 (class 1259 OID 16408)
-- Name: chunk; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chunk (
    id character varying NOT NULL,
    file_id integer NOT NULL,
    chunk_index integer NOT NULL,
    chunk_status integer NOT NULL
);


--
-- TOC entry 223 (class 1259 OID 16440)
-- Name: chunk_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chunk_status (
    id integer NOT NULL,
    name character varying NOT NULL
);


--
-- TOC entry 221 (class 1259 OID 16421)
-- Name: chunk_storage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chunk_storage (
    id integer NOT NULL,
    storage_id integer NOT NULL,
    chunk_id character varying NOT NULL
);


--
-- TOC entry 220 (class 1259 OID 16420)
-- Name: chunk_storage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chunk_storage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3497 (class 0 OID 0)
-- Dependencies: 220
-- Name: chunk_storage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chunk_storage_id_seq OWNED BY public.chunk_storage.id;


--
-- TOC entry 231 (class 1259 OID 16495)
-- Name: entity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity (
    id integer NOT NULL,
    name character varying NOT NULL,
    type_id integer NOT NULL
);


--
-- TOC entry 230 (class 1259 OID 16494)
-- Name: entity_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3498 (class 0 OID 0)
-- Dependencies: 230
-- Name: entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_id_seq OWNED BY public.entity.id;


--
-- TOC entry 229 (class 1259 OID 16486)
-- Name: entity_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_type (
    id integer NOT NULL,
    name character varying NOT NULL
);


--
-- TOC entry 228 (class 1259 OID 16485)
-- Name: entity_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3499 (class 0 OID 0)
-- Dependencies: 228
-- Name: entity_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_type_id_seq OWNED BY public.entity_type.id;


--
-- TOC entry 216 (class 1259 OID 16391)
-- Name: file; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file (
    id integer NOT NULL,
    filename character varying NOT NULL,
    bucket_id integer NOT NULL
);


--
-- TOC entry 215 (class 1259 OID 16390)
-- Name: file_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.file_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3500 (class 0 OID 0)
-- Dependencies: 215
-- Name: file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.file_id_seq OWNED BY public.file.id;


--
-- TOC entry 222 (class 1259 OID 16439)
-- Name: file_status_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.file_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3501 (class 0 OID 0)
-- Dependencies: 222
-- Name: file_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.file_status_id_seq OWNED BY public.chunk_status.id;


--
-- TOC entry 233 (class 1259 OID 16509)
-- Name: log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.log (
    id integer NOT NULL,
    action_id integer NOT NULL,
    entity_id integer NOT NULL,
    description character varying NOT NULL,
    datetime timestamp without time zone DEFAULT now() NOT NULL,
    success boolean DEFAULT true NOT NULL
);


--
-- TOC entry 232 (class 1259 OID 16508)
-- Name: log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3502 (class 0 OID 0)
-- Dependencies: 232
-- Name: log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.log_id_seq OWNED BY public.log.id;


--
-- TOC entry 218 (class 1259 OID 16400)
-- Name: storage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage (
    id integer NOT NULL,
    ip character varying NOT NULL,
    port integer NOT NULL,
    access_key character varying NOT NULL,
    secret_key character varying NOT NULL
);


--
-- TOC entry 217 (class 1259 OID 16399)
-- Name: storage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.storage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3503 (class 0 OID 0)
-- Dependencies: 217
-- Name: storage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.storage_id_seq OWNED BY public.storage.id;


--
-- TOC entry 3295 (class 2604 OID 16480)
-- Name: action id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action ALTER COLUMN id SET DEFAULT nextval('public.action_id_seq'::regclass);


--
-- TOC entry 3294 (class 2604 OID 16443)
-- Name: chunk_status id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_status ALTER COLUMN id SET DEFAULT nextval('public.file_status_id_seq'::regclass);


--
-- TOC entry 3293 (class 2604 OID 16424)
-- Name: chunk_storage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_storage ALTER COLUMN id SET DEFAULT nextval('public.chunk_storage_id_seq'::regclass);


--
-- TOC entry 3297 (class 2604 OID 16498)
-- Name: entity id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity ALTER COLUMN id SET DEFAULT nextval('public.entity_id_seq'::regclass);


--
-- TOC entry 3296 (class 2604 OID 16489)
-- Name: entity_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_type ALTER COLUMN id SET DEFAULT nextval('public.entity_type_id_seq'::regclass);


--
-- TOC entry 3291 (class 2604 OID 16394)
-- Name: file id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file ALTER COLUMN id SET DEFAULT nextval('public.file_id_seq'::regclass);


--
-- TOC entry 3298 (class 2604 OID 16512)
-- Name: log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log ALTER COLUMN id SET DEFAULT nextval('public.log_id_seq'::regclass);


--
-- TOC entry 3292 (class 2604 OID 16403)
-- Name: storage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage ALTER COLUMN id SET DEFAULT nextval('public.storage_id_seq'::regclass);


--
-- TOC entry 3484 (class 0 OID 16477)
-- Dependencies: 227
-- Data for Name: action; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.action VALUES (1, 'add', 'Добавлено');
INSERT INTO public.action VALUES (2, 'remove', 'Удалено');
INSERT INTO public.action VALUES (3, 'upload', 'Загружено');
INSERT INTO public.action VALUES (4, 'download', 'Скачано');
INSERT INTO public.action VALUES (5, 'init', 'Инициализировано');
INSERT INTO public.action VALUES (6, 'stop', 'Остановлено');
INSERT INTO public.action VALUES (7, 'mark_delete', 'Помечено к удалению');


--
-- TOC entry 3482 (class 0 OID 16456)
-- Dependencies: 225
-- Data for Name: bucket; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3476 (class 0 OID 16408)
-- Dependencies: 219
-- Data for Name: chunk; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3480 (class 0 OID 16440)
-- Dependencies: 223
-- Data for Name: chunk_status; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.chunk_status VALUES (1, 'uploading');
INSERT INTO public.chunk_status VALUES (3, 'active');
INSERT INTO public.chunk_status VALUES (2, 'error');
INSERT INTO public.chunk_status VALUES (4, 'delete');


--
-- TOC entry 3478 (class 0 OID 16421)
-- Dependencies: 221
-- Data for Name: chunk_storage; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3488 (class 0 OID 16495)
-- Dependencies: 231
-- Data for Name: entity; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3486 (class 0 OID 16486)
-- Dependencies: 229
-- Data for Name: entity_type; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.entity_type VALUES (1, 'file');
INSERT INTO public.entity_type VALUES (2, 'chunk');
INSERT INTO public.entity_type VALUES (3, 'storage');
INSERT INTO public.entity_type VALUES (4, 'system');
INSERT INTO public.entity_type VALUES (5, 'bucket');


--
-- TOC entry 3473 (class 0 OID 16391)
-- Dependencies: 216
-- Data for Name: file; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3490 (class 0 OID 16509)
-- Dependencies: 233
-- Data for Name: log; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3475 (class 0 OID 16400)
-- Dependencies: 218
-- Data for Name: storage; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3504 (class 0 OID 0)
-- Dependencies: 226
-- Name: action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.action_id_seq', 7, true);


--
-- TOC entry 3505 (class 0 OID 0)
-- Dependencies: 224
-- Name: bucket_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bucket_id_seq', 8, true);


--
-- TOC entry 3506 (class 0 OID 0)
-- Dependencies: 220
-- Name: chunk_storage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chunk_storage_id_seq', 700, true);


--
-- TOC entry 3507 (class 0 OID 0)
-- Dependencies: 230
-- Name: entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.entity_id_seq', 167, true);


--
-- TOC entry 3508 (class 0 OID 0)
-- Dependencies: 228
-- Name: entity_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.entity_type_id_seq', 5, true);


--
-- TOC entry 3509 (class 0 OID 0)
-- Dependencies: 215
-- Name: file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.file_id_seq', 49, true);


--
-- TOC entry 3510 (class 0 OID 0)
-- Dependencies: 222
-- Name: file_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.file_status_id_seq', 4, true);


--
-- TOC entry 3511 (class 0 OID 0)
-- Dependencies: 232
-- Name: log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.log_id_seq', 166, true);


--
-- TOC entry 3512 (class 0 OID 0)
-- Dependencies: 217
-- Name: storage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.storage_id_seq', 12, true);


--
-- TOC entry 3314 (class 2606 OID 16484)
-- Name: action action_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action
    ADD CONSTRAINT action_pkey PRIMARY KEY (id);


--
-- TOC entry 3312 (class 2606 OID 16462)
-- Name: bucket bucket_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bucket
    ADD CONSTRAINT bucket_pk PRIMARY KEY (id);


--
-- TOC entry 3306 (class 2606 OID 16414)
-- Name: chunk chunk_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk
    ADD CONSTRAINT chunk_pkey PRIMARY KEY (id);


--
-- TOC entry 3308 (class 2606 OID 16428)
-- Name: chunk_storage chunk_storage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_storage
    ADD CONSTRAINT chunk_storage_pkey PRIMARY KEY (id);


--
-- TOC entry 3318 (class 2606 OID 16502)
-- Name: entity entity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (id);


--
-- TOC entry 3316 (class 2606 OID 16493)
-- Name: entity_type entity_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_type
    ADD CONSTRAINT entity_type_pkey PRIMARY KEY (id);


--
-- TOC entry 3302 (class 2606 OID 16398)
-- Name: file file_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file
    ADD CONSTRAINT file_pkey PRIMARY KEY (id);


--
-- TOC entry 3310 (class 2606 OID 16447)
-- Name: chunk_status file_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_status
    ADD CONSTRAINT file_status_pkey PRIMARY KEY (id);


--
-- TOC entry 3320 (class 2606 OID 16516)
-- Name: log log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_pkey PRIMARY KEY (id);


--
-- TOC entry 3304 (class 2606 OID 16407)
-- Name: storage storage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage
    ADD CONSTRAINT storage_pkey PRIMARY KEY (id);


--
-- TOC entry 3322 (class 2606 OID 16557)
-- Name: chunk chunk_chunk_status_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk
    ADD CONSTRAINT chunk_chunk_status_fk FOREIGN KEY (chunk_status) REFERENCES public.chunk_status(id);


--
-- TOC entry 3323 (class 2606 OID 16415)
-- Name: chunk chunk_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk
    ADD CONSTRAINT chunk_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.file(id);


--
-- TOC entry 3324 (class 2606 OID 16434)
-- Name: chunk_storage chunk_storage_chunk_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_storage
    ADD CONSTRAINT chunk_storage_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunk(id);


--
-- TOC entry 3325 (class 2606 OID 16429)
-- Name: chunk_storage chunk_storage_storage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunk_storage
    ADD CONSTRAINT chunk_storage_storage_id_fkey FOREIGN KEY (storage_id) REFERENCES public.storage(id);


--
-- TOC entry 3326 (class 2606 OID 16503)
-- Name: entity entity_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity
    ADD CONSTRAINT entity_type_id_fkey FOREIGN KEY (type_id) REFERENCES public.entity_type(id);


--
-- TOC entry 3321 (class 2606 OID 16463)
-- Name: file file_bucket_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file
    ADD CONSTRAINT file_bucket_fk FOREIGN KEY (bucket_id) REFERENCES public.bucket(id);


--
-- TOC entry 3327 (class 2606 OID 16517)
-- Name: log log_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.action(id);


--
-- TOC entry 3328 (class 2606 OID 16522)
-- Name: log log_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entity(id);


-- Completed on 2026-05-01 10:34:27

--
-- PostgreSQL database dump complete
--

