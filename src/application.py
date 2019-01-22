from carbon.api import CarbonFlask
from carbon.api import JwtRefreshingHealthApiProvider
from carbon.api import SwaggerApiProvider
from carbon.authorization import JwtAuthorizer
from carbon.caching import DictCache
from carbon.logging import logging_formatter
from carbon.messages.message_queues import SqsMessageQueue
from carbon.requesters import Requester
from carbon.storage import S3StorageClient
from carbon.util import SettableValueHolder
from carbon.util import http_util
from frank import FrankClient
from guardian import GuardianClient
from guardian_refreshing import GuardianRefreshingClient
from lingo import LingoClient
from stitch import StitchClient
from worm import WormClient

from penguin.api.v0 import PenguinApiV0
from penguin.api.v1 import PenguinApiV1
from penguin.api.v2 import PenguinApiV2
from penguin.api.v3 import PenguinApiV3
from penguin.api.v4 import PenguinApiV4
from penguin.internal import ArticleManager
from penguin.model import constants
from penguin.store import ArticleMetadataRetriever
from penguin.store import ArticleSaver
from penguin.store import ArticleSourcesRetriever
from penguin.store import ArticleContentRetriever
from penguin.store import RawArticleStore
from penguin.store import connections
from penguin.store.redis_database import ImageUrlStore
from penguin.store.redis_database import PreCalculatedImageUrlStore


def make_app(name, debug, serverName, version, requestIdHolder, sessionIdHolder):
    dictCache = DictCache()
    serviceJwtHolder = SettableValueHolder(value=None)
    requester = Requester(requestIdHolder=requestIdHolder, requestJwtHolder=serviceJwtHolder, caches=[dictCache])
    guardianClient = GuardianClient(requester=requester)
    serviceJwt = guardianClient.login_with_password(userId=constants.SERVICE_ID, password=constants.SERVICE_PASSWORD, maxTokenAge=60 * 60)
    serviceJwtHolder.set_value(value=serviceJwt)

    databaseConnection = connections.get_database()
    redisConnection = connections.get_redis_connection()
    storageClient = S3StorageClient()
    imageUrlStore = ImageUrlStore(keyPrefix=constants.SERVER_BASE_NAME)
    preCalculatedImageUrlStore = PreCalculatedImageUrlStore(keyPrefix=constants.SERVER_BASE_NAME)

    rawWebpageStore = RawArticleStore(storageClient=storageClient, mimetype=http_util.MIMETYPE_HTML)
    rawAqmStore = RawArticleStore(storageClient=storageClient, mimetype=http_util.MIMETYPE_JSON)
    articleContentRetriever = ArticleContentRetriever()
    articleMetadataRetriever = ArticleMetadataRetriever()
    articleSourceRetriever = ArticleSourcesRetriever()
    wormClient = WormClient(requester=requester)
    stitchClient = StitchClient(requester=requester)
    frankClient = FrankClient(requester=requester)
    lingoClient = LingoClient(requester=requester)
    articleSaver = ArticleSaver()
    articleManager = ArticleManager(databaseConnection=databaseConnection, rawWebpageStore=rawWebpageStore, rawAqmStore=rawAqmStore, articleMetadataRetriever=articleMetadataRetriever, articleContentRetriever=articleContentRetriever, articleSaver=articleSaver, articleTaggingClient=stitchClient, imageUrlStore=imageUrlStore, preCalculatedImageUrlStore=preCalculatedImageUrlStore, frankClient=frankClient, articleSourceRetriever=articleSourceRetriever, redisConnection=redisConnection, articleSearchIndexClient=wormClient, languageClient=lingoClient)

    penguinQueue = SqsMessageQueue(requestIdHolder=requestIdHolder, region=constants.QUEUE_REGION_ARTICLE_PROCESSING, name=constants.QUEUE_NAME_ARTICLE_PROCESSING, messageDelay=constants.MAX_REPLICA_LAG)

    requestJwtHolder = SettableValueHolder(value=None)
    jwtAuthorizer = JwtAuthorizer(jwtRefreshingClient=GuardianRefreshingClient(requester=Requester(requestIdHolder=requestIdHolder)))
    penguinApiV0 = PenguinApiV0(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, penguinQueue=penguinQueue, articleManager=articleManager)
    penguinApiV1 = PenguinApiV1(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, penguinQueue=penguinQueue, articleManager=articleManager)
    penguinApiV2 = PenguinApiV2(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, penguinQueue=penguinQueue, articleManager=articleManager)
    penguinApiV3 = PenguinApiV3(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, penguinQueue=penguinQueue, articleManager=articleManager)
    penguinApiV4 = PenguinApiV4(requestIdHolder=requestIdHolder, requestJwtHolder=requestJwtHolder, jwtAuthorizer=jwtAuthorizer, sessionIdHolder=sessionIdHolder, penguinQueue=penguinQueue, articleManager=articleManager)

    healthApiProvider = JwtRefreshingHealthApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder, serverName=serverName, serverVersion=version, jwtAuthorizer=jwtAuthorizer, jwtToRefreshHolder=serviceJwtHolder)
    swaggerApiProvider = SwaggerApiProvider(requestIdHolder=requestIdHolder, sessionIdHolder=sessionIdHolder)
    application = CarbonFlask(importName=name, debug=debug, serverName=serverName, version=version)
    carbonApiProviders = [healthApiProvider, swaggerApiProvider, penguinApiV0, penguinApiV1, penguinApiV2, penguinApiV3, penguinApiV4]
    application.register_providers(carbonApiProviders=carbonApiProviders)

    return application


REQUEST_ID_HOLDER = SettableValueHolder(value=None)
SESSION_ID_HOLDER = SettableValueHolder(value=None)
logging_formatter.init_logging(serverName=constants.SERVER_NAME, environment=constants.ENVIRONMENT, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)

app = make_app(name=__name__, debug=constants.DEBUG, serverName=constants.SERVER_NAME, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER, sessionIdHolder=SESSION_ID_HOLDER)  # pylint: disable=invalid-name

if __name__ == '__main__':
    app.run()
