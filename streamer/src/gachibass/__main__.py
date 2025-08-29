from argparse import ArgumentParser
from .settings import get_settings

parser = ArgumentParser()
parser.add_argument("--test", default="aboba")
args = parser.parse_args()

settings = get_settings()
