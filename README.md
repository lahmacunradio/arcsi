# lahmacun_arcsi
Lahmacun's archivator  

# Local setup
## Requirements
 - Docker
 - Python 3.6+

## UNIX-type systems
### Get source code
1. `git clone ` this repository
2. `cd lahmacun_arcsi`

### Create environment
Create following template files:
1. config.template.py -> `config.py`
   * Set your values. Most are keys and secrets that you may get from third parties such as your storage and broadcast server. 
2. app.env.template -> `app.env`
   * Set `FLASK_APP=run.py`
3. db.env.template -> `db.env`
4. srv.env.template -> `srv.env`
   * `Set DOMAIN=localhost`
5. nginx/http_arcsi.conf.template -> `nginx/arcsi.conf`

### Start docker
Run `docker-compose up -d`

### Run app
Hit http://localhost in your browser

### Hints for local setup with [frontend](https://github.com/mmmnmnm/lahmacun)
   * (Docker-compose file) Change port setting to e.g., `2222:80` in the docker-compose file (otherwise the nginx server will conflict with the frontend's nginx server). 
   * (Docker-compose file) Delete `certbot` service in the docker-compose file (otherwise the service with the same name of the frontend project will be in conflict; note that you don't need this service on localhost). 
   * (PHP code) Point the frontend to local arcsi instance in the `content-arcsi.php` file of the frontend project. Note: you may need to use the `http://docker.for.mac.localhost:2222` style notation for Mac. 

## Windows
 - If an entry point fails to execute on Windows (the sh interpreter will tell you that the file doesn't exist, which is probably not true), check if there are Windows-style (CRLF) line endings and change them to Unix-style ones (LF). 

## Further notes
   * You may need to comment out following line in `docker-compose.yml`: `/etc/letsencrypt:/etc/letsencrypt`
   * FOR DEVELOPERS: You may want to add the `--reload` option for Gunicorn on [line]( https://github.com/lahmacunradio/arcsi/blob/master/entrypoint.sh#L3) for "on-the-fly" application of changes to Python files (you don't need to down and up docker for the changes to apply). Use it only during development!

## CI workflow summary
   * We started to use GitHub Actions and develop automatic testcases in order to prevent breaking commits sneaking into our repo.
   * During the [workflow]( https://github.com/lahmacunradio/arcsi/blob/master/.github/workflows/main.yml) we build up a test environment similar to our dev and prod env: 
      * Setup a Postgres DB locally on the VM and run this [migration script]( https://github.com/lahmacunradio/arcsi/blob/master/test/empty_dump.sql)
      * Start the Flask application on localhost with the following [config]( https://github.com/lahmacunradio/arcsi/blob/master/config_ci.py)
      * Run Newman with this Postman [collection]( https://github.com/lahmacunradio/arcsi/blob/master/test/postman/test.postman_collection.json). It contains API requests with real life use cases (adding/editing shows & episodes and getting the data of them) and runs multiple tests on their responses. If any of the requests or tests are failing it will cause an unsuccessful workflow run.
   * Here is a little diagram about the actual steps of the workflow (note that they are running sequentially not parallelly, but it looks better this way:):
   ![](https://github.com/lahmacunradio/arcsi/blob/master/docs/arcsi_ci.jpg)
