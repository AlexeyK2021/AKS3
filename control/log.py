from datetime import datetime


def log(tag: str, msg: str):
    print(f"{datetime.now()}\t[{tag}]\t{msg}")