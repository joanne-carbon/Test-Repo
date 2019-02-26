from babel import BabelClient
from bap import BapClient
from carbon.authorization import JwtAuthorizer
from carbon.caching import DictCache
from carbon.caching import RedisCache
from carbon.locking import RedisLockingClient
from carbon.logging import logging_formatter
from carbon.messages.message_queues import MessageQueueProcessor
from carbon.messages.message_queues import SqsMessageQueue
from carbon.requesters import Requester
from carbon.storage import S3StorageClient
from carbon.util import SettableValueHolder
from carbon.util import http_util
from frank import FrankClient
from guardian import GuardianClient
from guardian_refreshing import GuardianRefreshingClient
from journo import JournoClient
from lingo import LingoClient
from monica import MonicaClient
from pam import PamClient
from penguin.internal import ArticleManager
from penguin.internal import ArticleProcessor
from penguin.internal import ArticleQueueMessageClient
from penguin.internal import ArticleRetrievingClient
from penguin.internal import ImageSizeRetriever
from penguin.internal import ImageUrlFilterer
from penguin.model import constants
from penguin.store import ArticleContentRetriever
from penguin.store import ArticleMetadataRetriever
from penguin.store import ArticleSaver
from penguin.store import ArticleSourcesRetriever
from penguin.store import RawArticleStore
from penguin.store import connections
from penguin.store.redis_database import ImageUrlStore
from penguin.store.redis_database import PreCalculatedImageUrlStore
from picasso import PicassoClient
from stitch import StitchClient
from sweep import SweepClient
from valve import ValveClient
from worm import WormClient


def make_worker(requestIdHolder):
    dictCache = DictCache()
    serviceJwtHolder = SettableValueHolder(value=None)
    requester = Requester(requestIdHolder=requestIdHolder, requestJwtHolder=serviceJwtHolder, caches=[dictCache])
    guardianClient = GuardianClient(requester=requester)
    serviceJwt = guardianClient.login_with_password(userId=constants.SERVICE_ID, password=constants.SERVICE_PASSWORD, maxTokenAge=60 * 60)
    serviceJwtHolder.set_value(value=serviceJwt)

    databaseConnection = connections.get_database()
    redisConnection = connections.get_redis_connection()
    storageClient = S3StorageClient()
    rawWebpageStore = RawArticleStore(storageClient=storageClient, mimetype=http_util.MIMETYPE_HTML)
    rawAqmStore = RawArticleStore(storageClient=storageClient, mimetype=http_util.MIMETYPE_JSON)
    redisCache = RedisCache(keyPrefix=constants.SERVER_BASE_NAME, redisConnection=redisConnection)
    redisLockingClient = RedisLockingClient(keyPrefix=constants.SERVER_BASE_NAME, redisConnection=redisConnection)
    imageUrlStore = ImageUrlStore(keyPrefix=constants.SERVER_BASE_NAME)
    preCalculatedImageUrlStore = PreCalculatedImageUrlStore(keyPrefix=constants.SERVER_BASE_NAME)

    articleMetadataRetriever = ArticleMetadataRetriever()
    articleContentRetriever = ArticleContentRetriever()
    articleSourceRetriever = ArticleSourcesRetriever()
    articleSearchIndexClient = WormClient(requester=requester)
    babelClient = BabelClient(requester=requester)
    bapClient = BapClient(requester=requester)
    sweepClient = SweepClient(requester=requester)
    journoClient = JournoClient(requester=requester)
    monicaClient = MonicaClient(requester=requester)
    pamClient = PamClient(requester=requester)
    valveClient = ValveClient(requester=requester)
    stitchClient = StitchClient(requester=requester)
    frankClient = FrankClient(requester=requester)
    lingoClient = LingoClient(requester=requester)
    picassoClient = PicassoClient(requester=requester)
    articleSaver = ArticleSaver()

    imageUrlFilterer = ImageUrlFilterer(imageUrlStore=imageUrlStore, preCalculatedImageUrlStore=preCalculatedImageUrlStore)
    externalRequester = Requester(requestIdHolder=requestIdHolder)
    imageSizeRetriever = ImageSizeRetriever(requester=externalRequester)
    articleRetrievingClient = ArticleRetrievingClient(aqmArticleClient=pamClient, webArticleClient=journoClient)
    articleManager = ArticleManager(databaseConnection=databaseConnection, rawWebpageStore=rawWebpageStore, rawAqmStore=rawAqmStore, articleMetadataRetriever=articleMetadataRetriever, articleContentRetriever=articleContentRetriever, articleSaver=articleSaver, articleTaggingClient=stitchClient, imageUrlStore=imageUrlStore, preCalculatedImageUrlStore=preCalculatedImageUrlStore, frankClient=frankClient, articleSourceRetriever=articleSourceRetriever, redisConnection=redisConnection, articleSearchIndexClient=articleSearchIndexClient, languageClient=lingoClient)
    articleProcessor = ArticleProcessor(requester=externalRequester, redisConnection=redisConnection, cache=redisCache, imageSizeRetriever=imageSizeRetriever, imageUrlFilterer=imageUrlFilterer, imageClient=picassoClient, lockingClient=redisLockingClient, articleRetrievingClient=articleRetrievingClient, htmlCleaningClient=sweepClient, htmlProcessingClient=bapClient, switchClient=valveClient, articleManager=articleManager, languageClient=lingoClient, languageTranslatingClient=babelClient)

    jwtAuthorizer = JwtAuthorizer(jwtRefreshingClient=GuardianRefreshingClient(requester=Requester(requestIdHolder=requestIdHolder)))
    articleQueueMessageClient = ArticleQueueMessageClient(jwtAuthorizer=jwtAuthorizer, jwtToRefreshHolder=serviceJwtHolder, articleProcessor=articleProcessor, articleManager=articleManager, hostClient=monicaClient)
    messageQueue = SqsMessageQueue(name=constants.QUEUE_NAME_ARTICLE_PROCESSING, region=constants.QUEUE_REGION_ARTICLE_PROCESSING, requestIdHolder=requestIdHolder)
    return MessageQueueProcessor(requestIdHolder=requestIdHolder, messageQueue=messageQueue, messageClient=articleQueueMessageClient)


REQUEST_ID_HOLDER = RequestIdHolder(value=None)
logging_formatter.init_logging(serverName=constants.SERVER_NAME, environment=constants.ENVIRONMENT, version=constants.VERSION, requestIdHolder=REQUEST_ID_HOLDER)

worker = make_worker(requestIdHolder=REQUEST_ID_HOLDER)  # pylint: disable=invalid-name

if __name__ == '__main__':
    worker.run()
