from carbon.api import CarbonFlask
from carbon.api import JwtRefreshingHealthApiProvider
from carbon.api import SwaggerApiProvider
from carbon.authorization import JwtAuthorizer
from carbon.logging import logging_formatter
from carbon.requesters import Requester
from carbon.util import SettableValueHolder
from inception.internal import ServiceServletManager
from inception.model import constants
from inception.store import ServiceRetriever
from inception.store import ServiceSaver
from inception.store import ServiceServletEnvironmentRetriever
from inception.store import ServiceServletEnvironmentSaver

from guardian import GuardianClient
from guardian_refreshing import GuardianRefreshingClient
from register import RegisterClient

from inception.api.v0 import InceptionApiV0
from inception.api.v1 import InceptionApiV1
from inception.internal import ServiceManager
from inception.internal import ServiceServletEnvironmentManager

from inception.store import ServiceServletRetriever
from inception.store import ServiceServletSaver
from inception.store import connections

from inception.store import Nothing


def make_app(name, debug, serverName, version, requestIdHolder, sessionIdHolder):
    serviceJwtHolder = SettableValueHolder(value=None)
    requester = Requester(requestIdHolder=requestIdHolder, requestJwtHolder=serviceJwtHolder)
    guardianClient = GuardianClient(requester=requester)
    serviceJwt = guardianClient.login_with_password(userId=constants.SERVICE_ID, password=constants.SERVICE_PASSWORD, maxTokenAge=60 * 60)
    serviceJwtHolder.set_value(value=serviceJwt)

    requestJwtHolder = SettableValueHolder(value=None)
    jwtAuthorizer = JwtAuthorizer(jwtRefreshingClient=GuardianRefreshingClient(requester=Requester(requestIdHolder=requestIdHolder)))
    databaseConnection = connections.get_database()
    userClient = RegisterClient(requester=requester)
    serviceRetriever = ServiceRetriever()
    serviceSaver = ServiceSaver()
    serviceManager = ServiceManager(databaseConnection=databaseConnection, serviceRetriever=serviceRetriever, serviceSaver=serviceSaver, userClient=userClient)
    serviceServletSaver = ServiceServletSaver()
    serviceServletRetriever = ServiceServletRetriever()
    serviceServletManager = ServiceServletManager(databaseConnection=databaseConnection, serviceRetriever=serviceRetriever, serviceServletRetriever=serviceServletRetriever, serviceServletSaver=serviceServletSaver)
    serviceServletEnvironmentSaver = ServiceServletEnvironmentSaver()
    serviceServletEnvironmentRetriever = ServiceServletEnvironmentRetriever() # pylint: disable=invalid-name
    serviceServletEnvironmentManager = ServiceServletEnvironmentManager(databaseConnection=databaseConnection, serviceServletEnvironmentSaver=serviceServletEnvironmentSaver, serviceServletEnvironmentRetriever=serviceServletEnvironmentRetriever)   # pylint: disable=invalid-name
    inceptionApiV0 = InceptionApiV0(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, serviceManager=serviceManager, serviceServletManager=serviceServletManager, serviceServletEnvironmentManager=serviceServletEnvironmentManager)
    inceptionApiV1 = InceptionApiV1(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, serviceManager=serviceManager, serviceServletManager=serviceServletManager, serviceServletEnvironmentManager=serviceServletEnvironmentManager)
    healthApiProvider = JwtRefreshingHealthApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder, serverName=serverName, serverVersion=version, jwtAuthorizer=jwtAuthorizer, jwtToRefreshHolder=serviceJwtHolder)
    swaggerApiProvider = SwaggerApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder)
    application = CarbonFlask(importName=name, debug=debug, serverName=serverName, version=version)

    application.register_providers(carbonApiProviders=[inceptionApiV0, inceptionApiV1, healthApiProvider, swaggerApiProvider], disableTimeLimits=debug)
    return application


REQUEST_ID_HOLDER = SettableValueHolder(value=None)
SESSION_ID_HOLDER = SettableValueHolder(value=None)
logging_formatter.init_logging(serverName=constants.SERVER_NAME, environment=constants.ENVIRONMENT, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)

app = make_app(name=__name__, debug=constants.DEBUG, serverName=constants.SERVER_NAME, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)  # pylint: disable=invalid-name

if __name__ == '__main__':
    app.run()
