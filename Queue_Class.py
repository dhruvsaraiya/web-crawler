from json import JSONEncoder, JSONDecoder


class QueueClass:
    url = ""
    id = None
    title = None
    aKey = None
    p = None
    error = 0
    new_rank = 1.0
    old_rank = 0.0

    def __init__(self, url, id):
        self.url = url
        self.id = id
        self.title = None
        self.aKey = None
        self.error = 0
        self.p = None


class LinkClass:
    domain = ""
    link = ""
    cnm = ""
    nop = 0

    def __init__(self, d, l, c, n):
        self.domain = d
        self.link = l
        self.cnm = c
        self.nop = n


class EmployeeClass:
    name = ""
    unm = ""
    pwd = ""

    def __init__(self, n, u, p):
        self.name = n
        self.unm = u
        self.pwd = p


class UrlClass:
    url = ""
    title = ""
    p = ""
    rank = None

    def __init__(self, url, title):
        self.url = url
        self.title = title

    def __init__(self, url, title, p, rank):
        self.url = url
        self.title = title
        self.p = p
        self.rank = rank


class MyEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, UrlClass):
            obj = vars(o)
            return obj
        else:
            JSONEncoder.default(self, o)
