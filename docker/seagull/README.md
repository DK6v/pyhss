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
### Acclumulate CPU stats
stdbuf -oL grep -E '(h)ssService.py|(%)CPU' <(top -bc -w 300 -d 2 ) | \
    awk '{ if ($9 == "%CPU") {print s; s=0;} else { s+=$9; } }'