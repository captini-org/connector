# Master repository for the CAPTinI project

The repository uses submodules so you should clone it with `git clone
--recursive`.

## How to run this thing locally

Start by copying [`.env.example`](./.env.example) to `.env` and modifying the
appropriate values. For local development it probably makes sense to change
`ROOT_URL` to `http://localhost:${HTTP_PORT}`.

Next build and run all services:

```
$ docker-compose up --build
```

You can also add the `-d` option to put the running Docker compose deployment
into the background. Doing that allows you to repeatedly call `docker-compose up
-d --build` to only modify and restart containers whose contents has changed.

