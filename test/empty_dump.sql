--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5 (Debian 12.5-1.pgdg100+1)
-- Dumped by pg_dump version 12.5 (Debian 12.5-1.pgdg100+1)

SET session_replication_role = 'replica';
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    id integer NOT NULL,
    archive_lahmastore boolean,
    archive_lahmastore_canonical_url character varying,
    archive_mixcloud boolean,
    archive_mixcloud_canonical_url character varying,
    archived boolean,
    description character varying,
    image_url character varying,
    name character varying NOT NULL,
    number integer,
    play_date date NOT NULL,
    play_file_name character varying,
    uploaded_at timestamp without time zone NOT NULL,
    uploader character varying NOT NULL,
    download_count integer,
    length integer,
    live boolean,
    broadcast boolean,
    airing boolean,
    language character varying(5)
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.items_id_seq OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.items_id_seq OWNED BY public.items.id;


--
-- Name: items_shows; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items_shows (
    show_id integer,
    item_id integer
);


ALTER TABLE public.items_shows OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: roles_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles_users (
    user_id integer,
    role_id integer
);


ALTER TABLE public.roles_users OWNER TO postgres;

--
-- Name: shows; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shows (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    cover_image_url character varying,
    playlist_name character varying,
    week integer NOT NULL,
    day integer NOT NULL,
    start time without time zone NOT NULL,
    "end" time without time zone NOT NULL,
    archive_lahmastore boolean,
    archive_lahmastore_base_url character varying,
    archive_mixcloud boolean,
    archive_mixcloud_base_url character varying,
    frequency integer NOT NULL,
    language character varying(5),
    active boolean NOT NULL
);


ALTER TABLE public.shows OWNER TO postgres;

--
-- Name: shows_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shows_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.shows_id_seq OWNER TO postgres;

--
-- Name: shows_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shows_id_seq OWNED BY public.shows.id;


--
-- Name: shows_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shows_users (
    user_id integer,
    show_id integer
);


ALTER TABLE public.shows_users OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying,
    email character varying NOT NULL,
    butt_user character varying,
    butt_pw character varying(128),
    password character varying(128) NOT NULL,
    active boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN id SET DEFAULT nextval('public.items_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: shows id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows ALTER COLUMN id SET DEFAULT nextval('public.shows_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name, description) FROM stdin;
1	admin	Radio staff
2	host	Show host
3	guest	Episode guest
\.


--
-- Data for Name: roles_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles_users (user_id, role_id) FROM stdin;
1	1
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, name, email, butt_user, butt_pw, password, active) FROM stdin;
1	testuser	testuser@lahmacun.hu	buttuser	buttpw	testpassword	t
\.


--
-- Name: items items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: shows shows_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows
    ADD CONSTRAINT shows_name_key UNIQUE (name);


--
-- Name: shows shows_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows
    ADD CONSTRAINT shows_pkey PRIMARY KEY (id);


--
-- Name: shows shows_playlist_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows
    ADD CONSTRAINT shows_playlist_name_key UNIQUE (playlist_name);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: items_shows items_shows_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items_shows
    ADD CONSTRAINT items_shows_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: items_shows items_shows_show_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items_shows
    ADD CONSTRAINT items_shows_show_id_fkey FOREIGN KEY (show_id) REFERENCES public.shows(id);


--
-- Name: roles_users roles_users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles_users
    ADD CONSTRAINT roles_users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: roles_users roles_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles_users
    ADD CONSTRAINT roles_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: shows_users shows_users_show_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows_users
    ADD CONSTRAINT shows_users_show_id_fkey FOREIGN KEY (show_id) REFERENCES public.shows(id);


--
-- Name: shows_users shows_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shows_users
    ADD CONSTRAINT shows_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--
SET session_replication_role = 'origin';
