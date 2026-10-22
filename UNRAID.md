> The compose builds the public `dev` branch. Push the engine changes to
> `dev` before building; otherwise the image will not contain the custom
> `wikipedia-full` engine.

# Run the SearXNG fork on Unraid

This compose file builds the `dev` branch of
`https://github.com/eipox99/searxng.git`, which includes the
`wikipedia-full` engine used by Yonder's deferred sidebar card.

## Stack setup

1. Create the config folder:

   ```bash
   mkdir -p /mnt/user/appdata/searxng
   ```

2. Put `docker-compose.yml` and a `.env` in a stack folder, for example
   `/mnt/user/appdata/searxng-stack/`. Copy `.env.example` to `.env` and edit:

   ```dotenv
   SEARXNG_PORT=8080
   SEARXNG_CONFIG=/mnt/user/appdata/searxng
   INSTANCE_NAME=SearXNG
   SEARXNG_BASE_URL=http://YOUR-UNRAID-IP:8080/
   SEARXNG_SECRET=replace-with-a-long-random-secret
   ```

   Generate the secret with:

   ```bash
   openssl rand -hex 32
   ```

3. Start and build:

   ```bash
   docker compose up -d --build
   ```

   The build context is the GitHub `dev` branch, so the custom
   `wikipedia-full` engine and its traits data are inside the image.

## Config folder

`/mnt/user/appdata/searxng` is mounted at `/etc/searxng`. If it is empty,
the container creates `settings.yml` from its template. If you already have a
`settings.yml`, keep `use_default_settings: true` so the fork's default engine
list (including `wikipedia-full`) is loaded. If your settings replaces the
engine list, add:

```yaml
engines:
  - name: wikipedia-full
    engine: wikipedia_full
    shortcut: wpf
    display_type: ["infobox"]
    categories: [wikipedia-full]
```

The new engine is in its own category, so normal searches do not run it. Yonder
requests it explicitly only for the deferred sidebar lookup.

## Connect Yonder

In Yonder's `.env`:

```dotenv
SEARXNG_URL=http://YOUR-UNRAID-IP:8080/
SEARXNG_SECRET=the-same-secret-as-the-SearXNG-container
```

Restart Yonder after changing those values.

## Verify

After SearXNG restarts, this should return a full `infobox.content` and an
`img_src`:

```text
http://YOUR-UNRAID-IP:8080/search?q=XQc&format=json&language=en&engines=wikipedia-full
```

Then query `xQc` in Yonder and open the Overview card.

## If Compose Manager cannot build a Git context

Clone the dev branch into the stack folder and change `build.context` from the
Git URL to `.`:

```bash
git clone --branch dev https://github.com/eipox99/searxng.git
```

Then run `docker compose up -d --build` from that folder.
