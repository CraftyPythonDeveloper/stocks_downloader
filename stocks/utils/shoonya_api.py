from stocks_data_downloader.shoonya.custom_api import ShoonyaAPI

sapi = ShoonyaAPI()


def shoonya_refresh(ops="login"):
    try:
        sapi.close_websocket()
        sapi.logout()
    except AttributeError:
        pass
    if ops == "login":
        sapi.login()
        sapi.open_websocket()
        return True
    elif ops == "logout":
        sapi.login()
        return True
