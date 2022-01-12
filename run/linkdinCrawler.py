import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
import csv,json
import pandas as pd
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters, RemoteFilters
from linkedin_jobs_scraper.exceptions.exceptions import InvalidCookieException
from datetime import datetime
import boto3


# Change root logger level (default is WARN)
logging.basicConfig(level=logging.INFO)
accountID=boto3.client('sts').get_caller_identity().get('Account')
print("Account ID :",accountID)
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
table = dynamodb.Table('AwsCustomerProfilingStack-JobDeduplicationTableC0D070C1-DUGZT7CDPFM8')
ssm = boto3.client('ssm',region_name='ap-southeast-1')
cookie = ssm.get_parameter(Name='LinkedinCookie', WithDecryption=True)['Parameter']['Value']


def uploadRecord(record):
    res=table.put_item(
        Item=record
    )
    return res

def forfind(s,l):
    for a in l:
        if s.find(a) != -1:
            return True
    return False

def on_data(data: EventData):
    # print(data)
    cloud = ['cloud']
    cloud = [each_string.lower() for each_string in cloud]
    isCloud = False

    aws_list = ["Amazon", "aws"]
    aws_list = [each_string.lower() for each_string in aws_list]
    isAWS=False

    cloudV = ["Azure", "gcp", "Google Cloud", 'Alibaba Cloud', 'AliCloud']
    isCloudV = False
    cloudV = [each_string.lower() for each_string in cloudV]

    ml = ['ML', 'Machine Learning''machine learning', 'TensorFlow', 'PyTorch', 'MxNet Caffe', 'Keras', 'scikit-learn',
          'machine-learning', 'Machine-learning']
    isML = False
    ml = [each_string.lower() for each_string in ml]

    Devops = ['Kubernetes', 'k8s', 'K8S', 'Docker', 'docker', 'CI/CD', 'DevOps', 'devops', 'Container']
    isDevops = False
    Devops = [each_string.lower() for each_string in Devops]

    ai = ['ai']
    isAI = False

    Data = ['Flink', 'Spark', 'Sqoop', 'Flume', 'Kafka', 'data analysts', 'Big Data', ]
    isData = False
    Data = [each_string.lower() for each_string in Data]

    description=data.description.lower().replace('"',"'")

    descriptionList = description.split(' ')
    descriptionList = [each_string for each_string in descriptionList]

    if set(cloud) & set(descriptionList) != set() or  forfind(description, cloud):
        isCloud = True

    if set(aws_list) & set(descriptionList) != set() or forfind(description, aws_list):
        isAWS = True

    if set(cloudV) & set(descriptionList) != set() or  forfind(description, cloudV):
        isCloudV = True

    if set(ml) & set(descriptionList) != set() or  forfind(description, ml):
        isML = True

    if set(Devops) & set(descriptionList) != set()or  forfind(description, Devops):
        isDevops = True

    if set(ai) & set(descriptionList) != set() :
        isAI = True

    if set(Data) & set(descriptionList) != set() or  forfind(description, Data):
        isData = True


    data={"id": data.job_id,"source":'Linkeddin', "link": data.link, "title": data.title, "company": data.company,
                     "location": data.place, "description": description,"slug":data.job_id,
                      'postedOn': data.date,'companyOverview':data.companyOverview, 'isCloud': isCloud,
                     'isCloudV': isCloudV, 'isaws': isAWS,'isML': isML, 'isDevops': isDevops, 'isAI': isAI,
                     'isBigData': isData,"crawlDate":datetime.now().strftime("%d/%m/%Y")}
    uploadRecord(data)
    # print('[ON_DATA]', data.title, data.company, data.date, data.link, len(data.description))


def on_error(error):
    print('[ON_ERROR]', error)


def on_end():
    print('[ON_END]')


proxy_ips = ['51.15.227.220:3128', '81.162.56.154:8081', '106.14.43.86:8080', '106.15.8.56:8080',
             '118.185.38.153:35101', '106.14.249.0:8080', '121.36.17.97:808', '113.100.209.98:3128',
             '220.163.129.150:808', '121.4.82.250:8090']


def addition(n):
    return "https://" + n


scraper = LinkedinScraper(
    chrome_executable_path='/usr/local/bin/chromedriver',
    # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
    chrome_options=None,  # Custom Chrome options here
    headless=True,  # Overrides headless mode only if chrome_options is None
    max_workers=1,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
    slow_mo=3,  # Slow down the scraper to avoid 'Too many requests (429)' errors,
    proxies=list(map(addition, proxy_ips)),
    li_at_cookie=cookie

)

# Add event listeners
scraper.on(Events.DATA, on_data)
scraper.on(Events.ERROR, on_error)
scraper.on(Events.END, on_end)

queries = [
    Query(
        query='it',
        options=QueryOptions(
            locations=['Hong Kong SAR'],
            optimize=False,
            limit=1000,
            filters=QueryFilters(
            #     company_jobs_url='https://www.linkedin.com/jobs/search/?f_C=1441%2C17876832%2C791962%2C2374003%2C18950635%2C16140%2C10440912&geoId=92000000',  # Filter by companies
            #     relevance=RelevanceFilters.RECENT,
                time=TimeFilters.DAY,
            #     type=[TypeFilters.FULL_TIME, TypeFilters.INTERNSHIP],
            #     experience=None,
            )
        )
    ),
]


def toCSV(info, csv_file):
    # field_name = ['JobID', 'Link', 'Title', 'Company', 'Place',
    #               'Description', 'Seniority Level', 'Employment Type', 'Job Function', 'Date', 'Cloud',
    #               'Cloud Providers', 'ML', 'Devops', 'AI', 'Big Data', ]
    # try:
    df = pd.DataFrame(info)
    # df.set_index('JobID',inplace=True)
    df=df.drop_duplicates(subset='JobID',keep='first')
    print(df.count())
    print(df)
    df.to_csv(csv_file,index=False, encoding="utf_8_sig",mode='w+')
    # except Exception as e:
    #     print(e)


def read_csv(name):
    csv_job_info = []
    try:
        with open(name+'result.csv', newline='') as f:
            dict_reader = csv.DictReader(f)
            for row in dict_reader:
                # row['JobID']=row[f'\ufeffJobID']
                # del row[f'\ufeffJobID']
                csv_job_info.append(row)
        return csv_job_info
    except Exception as e:
        print(e)
        print('No CSV file')
        return []
def publish_text_message(phone_number, message):
    """
    Publishes a text message directly to a phone number without need for a
    subscription.

    :param phone_number: The phone number that receives the message.
    :param message: The message to send.
    :return: The ID of the message.
    """
    sns = boto3.resource("sns")
    response = sns.meta.client.publish(
        PhoneNumber=phone_number, Message=message)
    message_id = response['MessageId']
    return message_id


def publish_multi_message(Error):
    """
    Publishes a multi-format message to a topic. A multi-format message takes
    different forms based on the protocol of the subscriber.

    :param topic: The topic to publish to.
    :param Error: The context of the message.
    :return: The ID of the message.
    """
    sns = boto3.resource("sns")
    topic=sns.Topic('arn:aws:sns:ap-southeast-1:677640965046:linkedinError')
    message = {
        'default': Error,
        'sms': Error,
        'email': Error
    }
    response = topic.publish(
        Message=json.dumps(message), Subject="Linkedin Crawler Error", MessageStructure='json')
    message_id = response['MessageId']
    return message_id

try:
    scraper.run(queries)
except Exception as Error:
    publish_multi_message(str(Error))




