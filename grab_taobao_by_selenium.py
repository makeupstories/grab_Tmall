from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from lxml import etree
import pymongo

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)
KEYWORD = 'ipad'

MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_COLLECTION = 'products'
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def index_page(page):
    print(f'正在爬取第{page}页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        browser.get(url)
        if page > 1:
            input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager div.form > input')))
            submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager div.form > span.btn.J_Submit')))
            input.clear()
            input.send_keys(page)
            submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager li.item.active > span'), str(page)))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.m-itemlist .items .item')))
        get_products()
    except TimeoutException:
        index_page(page)


def get_products():
    html = browser.page_source
    html = etree.HTML(html)
    results = html.xpath('//div[@class="item J_MouserOnverReq  "]')
    length = len(results)

    image = html.xpath('//div[@class="item J_MouserOnverReq  "]//div[@class="pic"]/a/img/@data-src')
    # title = html.xpath('//div[@class="item J_MouserOnverReq  "]//div[@class="row row-2 title"]/a//text()')
    title = html.xpath('//div[@class="item J_MouserOnverReq  "]//div[@class="pic"]/a/img/@alt')
    price = html.xpath(
        '//div[@class="item J_MouserOnverReq  "]//div[@class="price g_price g_price-highlight"]/strong/text()')
    shop = html.xpath('//div[@class="item J_MouserOnverReq  "]//div[@class="shop"]/a')

    for i in range(0, length):
        product = {
            'image': 'https:' + image[i],
            'title': title[i].strip(),
            'price': '¥' + price[i],
            'shop': shop[i].xpath('string(.)').strip(),
        }
        print(product)
        save_to_mongo(product, i)


def save_to_mongo(product, i):
    try:
        result = db[MONGO_COLLECTION].insert_one(product)
        if result:
            print('存储%s成功' % i)
            print(result.inserted_id)
    except Exception:
        print('存储失败')


def main():
    for i in range(1, 3):
        index_page(i)
    browser.close()


if __name__ == '__main__':
    main()
