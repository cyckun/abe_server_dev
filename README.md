# ABE_Sever

*Trusted Authority for Users to Join.*

Demo: http://127.0.0.1:5000


## Installation

clone:
```
$ git clone https://github.com/cyckun/abe_server.git
$ cd abe_server
```
create & activate virtual env then install dependency:

with venv/virtualenv + pip:
```
$ python -m venv env  # use `virtualenv env` for Python2, use `python3 ...` for Python3 on Linux & macOS
$ source env/bin/activate  # use `env\Scripts\activate` on Windows
$ pip install -r requirements.txt
```
or with Pipenv:
```
$ pipenv install --dev
$ pipenv shell
```
generate fake data then run:
```
$ flask forge
$ flask run
* Running on http://127.0.0.1:5000/
```
Test account:
* email: cyc
* password: 1

## License

This project is licensed under the MIT License (see the
[LICENSE](LICENSE) file for details).
