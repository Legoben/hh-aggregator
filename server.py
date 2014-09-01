from tornado import ioloop, web, escape, gen, httpclient, httpserver #install
import json
import time
import datetime
import dateutil.parser as parser #install
from multiprocessing.pool import ThreadPool

_workers = ThreadPool(3) #We should only need one of these, but it doesn't hurt

token = open("token.txt", "r").read().strip() #FB Graph Access Token
#print(token)
print "restarted"

def checkGroup(id, name):
    client = httpclient.HTTPClient()
    resp = client.fetch("https://graph.facebook.com/"+id+"/feed?access_token="+token+"&format=json&method=get&pretty=0&suppress_http_code=1").body #Get group posts
    j = json.loads(resp)['data']
    print(name)

    for post in j:
        post['datetime'] = parser.parse(post['updated_time'])

    return j


@gen.engine
def crawlGroups():
    print("here")
    j = []
    for group in groups:
        j.extend(checkGroup(group['id'], group['name'])) #Add all posts to array

    print("done fetching")

    newlist = sorted(j, key=lambda k: k['datetime'], reverse=True) #Sort by datetimes
    #print("BAM", newlist)
    for post in newlist: #Remove the datetimes so JSON doesn't screw up.
        del post['datetime']

    open("feed.json", "w").write(json.dumps(newlist))
    #Do stuff


    print "waiting"
    time.sleep(300) #Time to wait before refreshing Feeds
    crawlGroups()


class APIHandler(web.RequestHandler):
    def get(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        j = open("feed.json", "r").read()

        if self.get_argument("pretty", None) != None:
            pretty = json.dumps(json.loads(j), indent=4, separators=(',', ': '))
            self.write(pretty)
        else:
            self.write(j)

class IndexHandler(web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render("templates/index.html")

groups = json.loads(open("groups.json", "r").read())

app = web.Application([
     (r'/', IndexHandler),
    (r'', IndexHandler),
    (r'/api', APIHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': "static"}),
], debug=True)

if __name__ == '__main__':
    _workers.apply_async(crawlGroups)
    #crawlGroups()
    httpserver.HTTPServer(app).listen(9009)
    ioloop.IOLoop.instance().start()


