from dotenv import load_dotenv


_loaded = False


def load_environment():
    global _loaded
    if not _loaded:
        load_dotenv()
        _loaded = True
