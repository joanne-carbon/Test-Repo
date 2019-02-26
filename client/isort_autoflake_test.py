from broom import BroomClient
from carbon.api import CarbonFlask
from carbon.api import JwtRefreshingHealthApiProvider
from carbon.api import SwaggerApiProvider
from carbon.authorization import JwtAuthorizer
from carbon.logging import logging_formatter
from carbon.requesters import Requester
from carbon.util import SettableValueHolder
from chad.api.v0 import ChadApiV0
from chad.internal import WebpageProcessor
from chad.model import constants
from guardian import GuardianClient
from guardian_refreshing import GuardianRefreshingClient

DATA_PARSER_LANGUAGES = ['en', 'ar']


def make_app(name, debug, serverName, version, requestIdHolder, sessionIdHolder):
    serviceJwtHolder = SettableValueHolder(value=None)
    requester = Requester(requestIdHolder=requestIdHolder, requestJwtHolder=serviceJwtHolder)
    authorizationClient = GuardianClient(requester=requester)
    serviceJwt = authorizationClient.login_with_password(userId=constants.SERVICE_ID, password=constants.SERVICE_PASSWORD, maxTokenAge=60 * 60)
    serviceJwtHolder.set_value(value=serviceJwt)
    broomClient = BroomClient(requester=requester)
    webpageProcessor = WebpageProcessor(requester=requester, htmlTidyClient=broomClient, dateParserLanguages=DATA_PARSER_LANGUAGES)

    jwtAuthorizer = JwtAuthorizer(jwtRefreshingClient=GuardianRefreshingClient(requester=Requester(requestIdHolder=requestIdHolder)))
    requestJwtHolder = SettableValueHolder(value=None)
    chadApiV0 = ChadApiV0(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, webpageProcessor=webpageProcessor)

    application = CarbonFlask(importName=name, debug=debug, serverName=serverName, version=version)
    healthApiProvider = JwtRefreshingHealthApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder, serverName=serverName, serverVersion=version, jwtToRefreshHolder=serviceJwtHolder, jwtAuthorizer=jwtAuthorizer)
    swaggerApiProvider = SwaggerApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder)
    carbonApiProviders = [healthApiProvider, swaggerApiProvider, chadApiV0]
    application.register_providers(carbonApiProviders=carbonApiProviders)
    return application


REQUEST_ID_HOLDER = SettableValueHolder(value=None)
SESSION_ID_HOLDER = SettableValueHolder(value=None)
logging_formatter.init_logging(serverName=constants.SERVER_NAME, environment=constants.ENVIRONMENT, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)

app = make_app(name=__name__, debug=constants.DEBUG, serverName=constants.SERVER_NAME, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)  # pylint: disable=invalid-name

if __name__ == '__main__':
    app.run()
