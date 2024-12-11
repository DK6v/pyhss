### Build docker image
```shell
docker compose build
```

### Start traffic generator
```shell
docker compose run seagull bash
cd ./pyhss-env/run
./start_client.ksh
```
