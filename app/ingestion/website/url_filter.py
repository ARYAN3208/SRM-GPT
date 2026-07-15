from urllib.parse import urlparse

ALLOWED_DOMAIN = "www.srmist.edu.in"

BLOCKED_EXTENSIONS = [

    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",

    ".mp4",
    ".mp3",

    ".zip",
    ".rar",

    ".pdf"

]

BLOCKED_PATHS = [

    "/andhra-pradesh",
    "/ap/",
    "/delhi-ncr",
    "/ghaziabad",
    "/ramapuram",
    "/vadapalani",
    "/sonepat",

    "srmap.edu.in",
    "srmuap.edu.in",

    "/sports/",
    
]

def is_valid_url(url):

    parsed = urlparse(url)

    if ALLOWED_DOMAIN not in parsed.netloc:
        return False

    lower_url = url.lower()

    for blocked in BLOCKED_PATHS:

        if blocked in lower_url:
            return False

    for ext in BLOCKED_EXTENSIONS:

        if lower_url.endswith(ext):
            return False

    return True