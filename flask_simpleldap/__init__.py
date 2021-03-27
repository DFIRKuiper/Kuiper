import re
from functools import wraps
import ldap
from ldap import filter as ldap_filter
from flask import abort, current_app, g, make_response, redirect, url_for, \
    request

__all__ = ['LDAP']


class LDAPException(RuntimeError):
    message = None

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class LDAP(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    @staticmethod
    def init_app(app):
        """Initialize the `app` for use with this :class:`~LDAP`. This is
        called automatically if `app` is passed to :meth:`~LDAP.__init__`.

        :param flask.Flask app: the application to configure for use with
           this :class:`~LDAP`
        """
        app.config.setdefault('LDAP_HOST', 'localhost')
        app.config.setdefault('LDAP_PORT', 389)
        app.config.setdefault('LDAP_SCHEMA', 'ldap')
        app.config.setdefault('LDAP_USERNAME', None)
        app.config.setdefault('LDAP_PASSWORD', None)
        app.config.setdefault('LDAP_TIMEOUT', 10)
        app.config.setdefault('LDAP_USE_SSL', False)
        app.config.setdefault('LDAP_USE_TLS', False)
        app.config.setdefault('LDAP_REQUIRE_CERT', False)
        app.config.setdefault('LDAP_CERT_PATH', '/path/to/cert')
        app.config.setdefault('LDAP_BASE_DN', None)
        app.config.setdefault('LDAP_OBJECTS_DN', 'distinguishedName')
        app.config.setdefault('LDAP_USER_FIELDS', [])
        app.config.setdefault('LDAP_USER_OBJECT_FILTER',
                              '(&(objectclass=Person)(userPrincipalName=%s))')
        app.config.setdefault('LDAP_USER_GROUPS_FIELD', 'memberOf')
        app.config.setdefault('LDAP_GROUP_FIELDS', [])
        app.config.setdefault('LDAP_GROUP_OBJECT_FILTER',
                              '(&(objectclass=Group)(userPrincipalName=%s))')
        app.config.setdefault('LDAP_GROUP_MEMBERS_FIELD', 'member')
        app.config.setdefault('LDAP_LOGIN_VIEW', 'login')
        app.config.setdefault('LDAP_REALM_NAME', 'LDAP authentication')
        app.config.setdefault('LDAP_OPENLDAP', False)
        app.config.setdefault('LDAP_GROUP_MEMBER_FILTER', '*')
        app.config.setdefault('LDAP_GROUP_MEMBER_FILTER_FIELD', '*')
        app.config.setdefault('LDAP_CUSTOM_OPTIONS', None)

        if app.config['LDAP_USE_SSL'] or app.config['LDAP_USE_TLS']:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,
                            ldap.OPT_X_TLS_NEVER)

        if app.config['LDAP_REQUIRE_CERT']:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,
                            ldap.OPT_X_TLS_DEMAND)
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,
                            current_app.config['LDAP_CERT_PATH'])

        for option in ['USERNAME', 'PASSWORD', 'BASE_DN']:
            if app.config['LDAP_{0}'.format(option)] is None:
                raise LDAPException('LDAP_{0} cannot be None!'.format(option))

    @staticmethod
    def _set_custom_options(conn):
        options = current_app.config['LDAP_CUSTOM_OPTIONS']
        if options:
            for k, v in options.items():
                conn.set_option(k, v)
        return conn

    @property
    def initialize(self):
        """Initialize a connection to the LDAP server.

        :return: LDAP connection object.
        """

        try:
            conn = ldap.initialize('{0}://{1}:{2}'.format(
                current_app.config['LDAP_SCHEMA'],
                current_app.config['LDAP_HOST'],
                current_app.config['LDAP_PORT']))
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT,
                            current_app.config['LDAP_TIMEOUT'])
            conn = self._set_custom_options(conn)
            conn.protocol_version = ldap.VERSION3
            if current_app.config['LDAP_USE_TLS']:
                conn.start_tls_s()
            return conn
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args))

    @property
    def bind(self):
        """Attempts to bind to the LDAP server using the credentials of the
        service account.

        :return: Bound LDAP connection object if successful or ``None`` if
            unsuccessful.
        """

        conn = self.initialize
        try:
            conn.simple_bind_s(
                current_app.config['LDAP_USERNAME'],
                current_app.config['LDAP_PASSWORD'])
            return conn
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args))

    def bind_user(self, username, password):
        """Attempts to bind a user to the LDAP server using the credentials
        supplied.

        .. note::

            Many LDAP servers will grant anonymous access if ``password`` is
            the empty string, causing this method to return :obj:`True` no
            matter what username is given. If you want to use this method to
            validate a username and password, rather than actually connecting
            to the LDAP server as a particular user, make sure ``password`` is
            not empty.

        :param str username: The username to attempt to bind with.
        :param str password: The password of the username we're attempting to
            bind with.
        :return: Returns ``True`` if successful or ``None`` if the credentials
            are invalid.
        """
        user_dn = self.get_object_details(user=username, dn_only=True)
        if user_dn is None:
            return
        try:
            conn = self.initialize
            _user_dn = user_dn.decode('utf-8') \
                if isinstance(user_dn, bytes) else user_dn
            conn.simple_bind_s(_user_dn, password)
            return True
        except ldap.LDAPError:
            return

    def get_object_details(self, user=None, group=None, query_filter=None,
                           dn_only=False):
        """Returns a ``dict`` with the object's (user or group) details.

        :param str user: Username of the user object you want details for.
        :param str group: Name of the group object you want details for.
        :param str query_filter: If included, will be used to query object.
        :param bool dn_only: If we should only retrieve the object's
            distinguished name or not. Default: ``False``.
        """
        query = None
        fields = None
        if user is not None:
            if not dn_only:
                fields = current_app.config['LDAP_USER_FIELDS']
            query_filter = query_filter or \
                           current_app.config['LDAP_USER_OBJECT_FILTER']
            query = ldap_filter.filter_format(query_filter, (user,))
        elif group is not None:
            if not dn_only:
                fields = current_app.config['LDAP_GROUP_FIELDS']
            query_filter = query_filter or \
                           current_app.config['LDAP_GROUP_OBJECT_FILTER']
            query = ldap_filter.filter_format(query_filter, (group,))
        conn = self.bind
        try:
            records = conn.search_s(current_app.config['LDAP_BASE_DN'],
                                    ldap.SCOPE_SUBTREE, query, fields)
            conn.unbind_s()
            result = {}
            if records:
                if dn_only:
                    if current_app.config['LDAP_OPENLDAP']:
                        if records:
                            return records[0][0]
                    else:
                        if current_app.config['LDAP_OBJECTS_DN'] \
                                in records[0][1]:
                            dn = records[0][1][
                                current_app.config['LDAP_OBJECTS_DN']]
                            return dn[0]
                for k, v in list(records[0][1].items()):
                    result[k] = v
                return result
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args))

    def get_user_groups(self, user):
        """Returns a ``list`` with the user's groups or ``None`` if
        unsuccessful.

        :param str user: User we want groups for.
        """

        conn = self.bind
        try:
            if current_app.config['LDAP_OPENLDAP']:
                fields = \
                    [str(current_app.config['LDAP_GROUP_MEMBER_FILTER_FIELD'])]
                records = conn.search_s(
                    current_app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                    ldap_filter.filter_format(
                        current_app.config['LDAP_GROUP_MEMBER_FILTER'],
                        (self.get_object_details(user, dn_only=True),)),
                    fields)
            else:
                records = conn.search_s(
                    current_app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                    ldap_filter.filter_format(
                        current_app.config['LDAP_USER_OBJECT_FILTER'],
                        (user,)),
                    [current_app.config['LDAP_USER_GROUPS_FIELD']])

            conn.unbind_s()
            if records:
                if current_app.config['LDAP_OPENLDAP']:
                    group_member_filter = \
                        current_app.config['LDAP_GROUP_MEMBER_FILTER_FIELD']
                    groups = [record[1][group_member_filter][0].decode(
                        'utf-8') for record in records]
                    return groups
                else:
                    if current_app.config['LDAP_USER_GROUPS_FIELD'] in \
                            records[0][1]:
                        groups = records[0][1][
                            current_app.config['LDAP_USER_GROUPS_FIELD']]
                        result = [re.findall(b'(?:cn=|CN=)(.*?),', group)[0]
                                  for group in groups]
                        result = [r.decode('utf-8') for r in result]
                        return result
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args))

    def get_group_members(self, group):
        """Returns a ``list`` with the group's members or ``None`` if
        unsuccessful.

        :param str group: Group we want users for.
        """

        conn = self.bind
        try:
            records = conn.search_s(
                current_app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                ldap_filter.filter_format(
                    current_app.config['LDAP_GROUP_OBJECT_FILTER'], (group,)),
                [current_app.config['LDAP_GROUP_MEMBERS_FIELD']])
            conn.unbind_s()
            if records:
                if current_app.config['LDAP_GROUP_MEMBERS_FIELD'] in \
                        records[0][1]:
                    members = records[0][1][
                        current_app.config['LDAP_GROUP_MEMBERS_FIELD']]
                    members = [m.decode('utf-8') for m in members]
                    return members
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args))

    @staticmethod
    def error(e):
        e = e[0]
        if 'desc' in e:
            return e['desc']
        else:
            return e

    @staticmethod
    def login_required(func):
        """When applied to a view function, any unauthenticated requests will
        be redirected to the view named in LDAP_LOGIN_VIEW. Authenticated
        requests do NOT require membership from a specific group.

        The login view is responsible for asking for credentials, checking
        them, and setting ``flask.g.user`` to the name of the authenticated
        user if the credentials are acceptable.

        :param func: The view function to decorate.
        """

        @wraps(func)
        def wrapped(*args, **kwargs):
            if g.user is None:
                next_path=request.full_path or request.path
                if next_path == '/?':
                    return redirect(
                        url_for(current_app.config['LDAP_LOGIN_VIEW']))
                return redirect(url_for(current_app.config['LDAP_LOGIN_VIEW'],
                                        next=next_path))
            return func(*args, **kwargs)

        return wrapped

    @staticmethod
    def group_required(groups=None):
        """When applied to a view function, any unauthenticated requests will
        be redirected to the view named in LDAP_LOGIN_VIEW. Authenticated
        requests are only permitted if they belong to one of the listed groups.

        The login view is responsible for asking for credentials, checking
        them, and setting ``flask.g.user`` to the name of the authenticated
        user and ``flask.g.ldap_groups`` to the authenticated user's groups
        if the credentials are acceptable.

        :param list groups: List of groups that should be able to access the
            view function.
        """

        def wrapper(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                if g.user is None:
                    return redirect(
                        url_for(current_app.config['LDAP_LOGIN_VIEW'],
                                next=request.full_path or request.path))
                match = [group for group in groups if group in g.ldap_groups]
                if not match:
                    abort(401)

                return func(*args, **kwargs)

            return wrapped

        return wrapper

    def basic_auth_required(self, func):
        """When applied to a view function, any unauthenticated requests are
        asked to authenticate via HTTP's standard Basic Authentication system.
        Requests with credentials are checked with :meth:`.bind_user()`.

        The user's browser will typically show them the contents of
        LDAP_REALM_NAME as a prompt for which username and password to enter.

        If the request's credentials are accepted by the LDAP server, the
        username is stored in ``flask.g.ldap_username`` and the password in
        ``flask.g.ldap_password``.

        :param func: The view function to decorate.
        """

        def make_auth_required_response():
            response = make_response('Unauthorized', 401)
            response.www_authenticate.set_basic(
                current_app.config['LDAP_REALM_NAME'])
            return response

        @wraps(func)
        def wrapped(*args, **kwargs):
            if request.authorization is None:
                req_username = None
                req_password = None
            else:
                req_username = request.authorization.username
                req_password = request.authorization.password
            # Many LDAP servers will grant you anonymous access if you log in
            # with an empty password, even if you supply a non-anonymous user
            # ID, causing .bind_user() to return True. Therefore, only accept
            # non-empty passwords.
            if req_username in ['', None] or req_password in ['', None]:
                current_app.logger.debug('Got a request without auth data')
                return make_auth_required_response()

            if not self.bind_user(req_username, req_password):
                current_app.logger.debug('User {0!r} gave wrong '
                                         'password'.format(req_username))
                return make_auth_required_response()

            g.ldap_username = req_username
            g.ldap_password = req_password

            return func(*args, **kwargs)

        return wrapped
