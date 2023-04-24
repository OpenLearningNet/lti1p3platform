<!-- @format -->

# Example of usage LTI1P3Platform library within Django framework

Running server:

    $ virtualenv venv
    $ source venv/bin/activate
    $ poetry install
    $ export PYTHONPATH="$PWD:$PYTHONPATH"
    $ cd examples/django_platform
    $ python manage.py migration # running at the first time to create tables
    $ python manage.py runserver 127.0.0.1:9002

Tool running [server](https://github.com/dmitry-viskov/pylti1.3-django-example), you could follow instructions to start the tool server.

You also need to add platform config to the tool config file [game.json](https://github.com/dmitry-viskov/pylti1.3-django-example/blob/master/configs/game.json):

    {
        "https://example.com": [{
            "default": true,
            "client_id": "12345",
            "auth_login_url": "http://127.0.0.1:9002/authorization",
            "auth_token_url": "http://127.0.0.1:9002/access_token",
            "auth_audience": null,
            "key_set_url": "http://127.0.0.1:9002/jwks",
            "key_set": null,
            "private_key_file": "private.key",
            "public_key_file": "public.key",
            "deployment_ids": ["1"]
        }]
    }

Now there is game example tool you can launch into on the port 9001:

    Initial Login URL: http://127.0.0.1:9002/login
    LTI Launch URL: http://127.0.0.1:9002/launch
    JWKS URL: http://127.0.0.1:9002/jwks

Now you could go to `http://127.0.0.1:9002/login` to start to play.
