# Stock Data Downloader

## This is an django app which can be used to capture live data from nse using websocket.

### Currently this project is under development & supported broker will be shoonya.

## Installation

Installation Guide

```bash
  git clone https://github.com/punhat/stocks_downloader.git
  cd stocks_downloader/stocks
  pip install -r requirements.txt
```

Do migrations
```bash
  python manage.py makemigrations
  python manage.py migrate
```

To run the application
```bash
    python manage.py runserver
```
