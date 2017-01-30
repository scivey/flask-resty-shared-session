from __future__ import print_function
import requests
import requests.cookies
from copy import deepcopy
import urllib
import json
import unittest
from pprint import pprint
from app_server.config import CONFIG
from app_server.user import USER_FIXTURES_BY_EMAIL


APP_BASE = '/app'
API_BASE = '%s/api/v1' % APP_BASE


def api_url(href):
    return API_BASE + href

def app_url(href):
    return APP_BASE + href



class TestHTTPClient(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._session = None

    @staticmethod
    def _url(href):
        return urllib.basejoin(CONFIG.CACHE_PROXY_URL, href)

    def _method(self, method, href, *args, **kwargs):
        url = self._url(href)
        fn = getattr(requests, method)
        kwargs = dict(kwargs)
        session_cookie = CONFIG.SESSION_COOKIE_NAME
        if self._session is not None:
            cookies = deepcopy(kwargs.get('cookies', {}))
            cookies[session_cookie] = self._session
            kwargs['cookies'] = cookies
        response = fn(url, *args, **kwargs)
        if session_cookie in response.cookies:
            self._session = response.cookies.get(session_cookie)
        return response

    def get(self, href, *args, **kwargs):
        return self._method('get', href, *args, **kwargs)

    def put(self, href, *args, **kwargs):
        return self._method('put', href, *args, **kwargs)

    def post(self, href, *args, **kwargs):
        return self._method('post', href, *args, **kwargs)



class TestAPIClient(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.http = TestHTTPClient()

    def login(self, email, password):
        return self.http.post(app_url('/login'), data={
            'email': email,
            'password': password
        })

    def logout(self):
        return self.http.post(app_url('/logout'))

    def get_myself(self):
        return self.http.get(api_url('/myself'))

    def get_cacheable_group_resource(self, group_id, resource_id):
        url = api_url('/group/%s/cacheable/%s' % (group_id, resource_id))
        return self.http.get(url)

    def get_uncacheable_group_resource(self, group_id, resource_id):
        url = api_url('/group/%s/uncacheable/%s' % (group_id, resource_id))
        return self.http.get(url)



def pprint_res(res):
    content = res.content
    if '/json' in res.headers.get('Content-Type', ''):
        content = json.loads(content)
    pprint(dict(
        headers=dict(res.headers),
        content=content,
        status_code=res.status_code
    ))
    

def say(msg, *args):
    print_args = [msg]
    if args:
        print_args.extend(list(args))
    print_args.append("\n")
    print("\n\t", *print_args)





class TestLogin(unittest.TestCase):
    def setUp(self):
        self.client = TestAPIClient()

    def test_good_login(self):
        res = self.client.get_myself()
        self.assertEqual(401, res.status_code)
        login_res = self.client.login('sam@gmail.com', 'itssam')
        assert login_res.status_code < 400
        res = self.client.get_myself()
        self.assertEqual(200, res.status_code)

    def test_bad_login_1(self):
        res = self.client.get_myself()
        self.assertEqual(401, res.status_code)
        login_res = self.client.login('sam@gmail.com', 'bad')
        assert login_res.status_code > 400 and login_res.status_code < 500
        res = self.client.get_myself()
        self.assertEqual(401, res.status_code)

    def test_bad_login_2(self):
        res = self.client.get_myself()
        self.assertEqual(401, res.status_code)
        login_res = self.client.login('nonexistent@gmail.com', 'itssam')
        assert login_res.status_code > 400 and login_res.status_code < 500
        res = self.client.get_myself()
        self.assertEqual(401, res.status_code)



class TestGroupResources(unittest.TestCase):
    def setUp(self):
        self.assertEqual(
            set(['one', 'three']),
            set(USER_FIXTURES_BY_EMAIL['joe@gmail.com']['groups'])
        )
        self.assertEqual(
            set(['two']),
            set(USER_FIXTURES_BY_EMAIL['sam@gmail.com']['groups'])
        )
        self.assertEqual(
            set(['one', 'four']),
            set(USER_FIXTURES_BY_EMAIL['esteban@gmail.com']['groups'])
        )

        self.samc = TestAPIClient()
        self.joec = TestAPIClient()
        self.estebanc = TestAPIClient()
        response = self.samc.login('sam@gmail.com', 'itssam')
        self.assertTrue(response.status_code < 400)
        response = self.joec.login('joe@gmail.com', 'itsjoe')
        self.assertTrue(response.status_code < 400)
        response = self.estebanc.login('esteban@gmail.com', 'itsesteban')
        self.assertTrue(response.status_code < 400)

    def test_uncacheable(self):
        one_foo_1 = self.joec.get_uncacheable_group_resource('one', 'foo')
        self.assertTrue(one_foo_1.status_code < 300)
        one_foo_2 = self.joec.get_uncacheable_group_resource('one', 'foo')
        self.assertTrue(one_foo_2.status_code < 300)
        one_foo_1_data = one_foo_1.json()
        one_foo_2_data = one_foo_2.json()
        for item in (one_foo_1_data, one_foo_2_data):
            self.assertEqual('foo', item['resource_id'])
            self.assertEqual('one', item['group_id'])

        # since the origin generates a UUID for `response_id`,
        # inequality means we got an uncached response each time
        self.assertNotEqual(
            one_foo_1_data['response_id'],
            one_foo_2_data['response_id']
        )

        sam_attempt = self.samc.get_uncacheable_group_resource('one', 'foo')
        self.assertEqual(403, sam_attempt.status_code)


    def test_cacheable__response_cached_and_permissions_checked(self):
        sam_bar_1 = self.samc.get_cacheable_group_resource('two', 'bar')
        self.assertTrue(sam_bar_1.status_code < 300)

        joe_bar_1 = self.joec.get_cacheable_group_resource('two', 'bar')
        # despite sam's first request having made a cache entry,
        # joe is still denied access.
        self.assertEqual(403, joe_bar_1.status_code)


        sam_bar_2 = self.samc.get_cacheable_group_resource('two', 'bar')
        self.assertTrue(sam_bar_2.status_code < 300, "status code: %r" % sam_bar_2.status_code)
        sam_bar_1_data = sam_bar_1.json()
        sam_bar_2_data = sam_bar_2.json()

        for item in (sam_bar_1_data, sam_bar_2_data):
            self.assertEqual('bar', item['resource_id'])
            self.assertEqual('two', item['group_id'])

        # since the origin generates a UUID for `response_id`,
        # equality means we got the same (cached) response
        self.assertEqual(
            sam_bar_1_data['response_id'],
            sam_bar_2_data['response_id']
        )


    def test_cacheable__cache_shared_between_group_members(self):
        joe_baz_1 = self.joec.get_cacheable_group_resource('one', 'baz')
        self.assertTrue(joe_baz_1.status_code < 300)

        esteban_baz_1 = self.estebanc.get_cacheable_group_resource('one', 'baz')
        self.assertTrue(esteban_baz_1.status_code < 300)

        joe_baz_2 = self.joec.get_cacheable_group_resource('one', 'baz')
        self.assertTrue(joe_baz_2.status_code < 300, "status=%r" % joe_baz_2.status_code)

        esteban_baz_2 = self.estebanc.get_cacheable_group_resource('one', 'baz')
        self.assertTrue(esteban_baz_2.status_code < 300)

        response_id_set = set()
        for response in (joe_baz_1, esteban_baz_1, joe_baz_2, esteban_baz_2):
            data = response.json()
            self.assertEqual('one', data['group_id'])
            self.assertEqual('baz', data['resource_id'])
            response_id_set.add(data['response_id'])

        # number of distinct response_ids == number of requests to origin
        self.assertEqual(1, len(response_id_set))

