# Dokku Hosting

These are just some notes for myself, since I host this with Dokku.

## Rebuilding the Database

```sh
dokku mysql:create bible_api_2024
dokku mysql:link bible_api_2024 bible-api.com

dokku enter bible-api.com
DATABASE_URL="$DOKKU_MYSQL_AQUA_URL" ruby import.rb # or whatever env var Dokku gave you
exit

dokku mysql:promote bible_api_2024 bible-api.com
# verify nothing broken

dokku mysql:unlink bible_api_2023 bible-api.com
dokku mysql:stop bible_api_2023
dokku mysql:destroy bible_api_2023
```
