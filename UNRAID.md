# Run the SearXNG fork on Unraid

This stack builds the `dev` branch of
`https://github.com/eipox99/searxng.git`, which includes the
`wikipedia-full` engine used by Yonder's deferred sidebar card.

## Network

SearXNG uses:

```yaml
network_mode: "container:binhex-delugevpn"
```

It therefore shares the VPN container's network namespace. Do **not** put a
`ports:` section on the SearXNG service; `binhex-delugevpn` already publishes
port 8080. SearXNG listens on 8080 inside that shared network.

The VPN container must be running before this stack starts. If the VPN
container is recreated or restarted, restart the SearXNG stack too so it joins
the new network namespace.

## Compose Manager setup

1. In Unraid, open the Compose Manager stack for `custom-searxng`.
2. Replace the compose with `docker-compose.yml` from the `dev` branch.
3. Set the stack environment:

   ```dotenv
   SEARXNG_CONFIG=/mnt/user/appdata/searxng
   INSTANCE_NAME=SearXNG
   SEARXNG_BASE_URL=http://YOUR-UNRAID-IP:8080/
   SEARXNG_SECRET=replace-with-a-long-random-secret
   ```

4. Click **Compose Up**/**Update** to rebuild. Do not create the appdata
   folder manually; Docker creates the bind-mount path, and SearXNG creates
   `settings.yml` inside it.

## Config folder

`/mnt/user/appdata/searxng` is mounted at `/etc/searxng`.

If the folder is empty, the container creates `settings.yml` from its template.
If you already have a `settings.yml`, keep `use_default_settings: true` so the
fork's default engine list (including `wikipedia-full`) is loaded. If your
settings replaces the engine list, add:

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

After the stack starts, this should return a full `infobox.content` and an
`img_src`:

```text
http://YOUR-UNRAID-IP:8080/search?q=XQc&format=json&language=en&engines=wikipedia-full
```

Then query `xQc` in Yonder and open the Overview card.
