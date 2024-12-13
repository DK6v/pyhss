### Build docker image
```shell
docker compose build
```

### Start HSS application
```shell
sudo sysctl vm.overcommit_memory=1
cp .secret.template .secret

docker compose up
```

### Swagger API
[http://localhost:8080/docs/](http://localhost:5000/docs/)

### PgAdmin
[http://localhost:5050](http://localhost:5050)

User/Password: admin/admin

Connect to the database, open "Objects Explorer" -> "Servers" -> "Register":
- Host name: pyhss-ds.psql.0
- Maintanance database: HSS
- Username/Password: *see .secrets for details*

### Run PyHSS tools
```shell
docker exec -it -w /pyhss/bin/tools pyhss-ds.pyhss.fe.0 bash
```
