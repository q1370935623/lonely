import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import time

start_time = time.perf_counter()

URL = 'https://bj.lianjia.com/zufang/pg{page}/#contentList'    # 链家租房信息的基本链接

HEADERS = {
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
           }    # 伪装头，防止网页查出是爬虫

def get_html(url):
    """
    下载当前url的网页源码
    当前未获得源码时，暂停2s，再去请求下载
    :param url: 当前网页链接
    :return: 网页源码
    """
    try:
        response = requests.get(url, headers = HEADERS)   # 请求url
        if response.status_code == 200:     # 请求状态码为200时表示请求成功，请求成功时，返回html
            response.encoding = response.apparent_encoding
            return response.text
        else:     # 当请求失败时，暂停2s再次请求
            time.sleep(2)   # 休眠2s
            get_html(url)   # 再次请求
    except Exception as e:  # 当程序执行发生异常时，抛出异常
        print('执行下载时发生异常:', e)

def parse_page(html):
    """
    对网页进行解析，获取我们需要的信息
    :param html: 网页源码
    :return 当前页面的所有租房信息列表
    """
    houses = []  # 存储当前页的所有出租房信息列表
    soup = BeautifulSoup(html, 'html.parser')  # 初始化
    divs = soup.find_all('div', attrs = {'class':'content__list--item'})   # 所有租房信息的节点
    for div in divs:    # 遍历所有租房节点
        house = {}        # 用于存放单个租房信息的字典
        try:
            house['title'] = div.find('a', attrs = {'class': 'content__list--item--aside'}).attrs['title']   # 获取租房标题
        except:
            house['title'] = ''
        try:
            house['pic_url'] = div.select('a.content__list--item--aside img')[0].attrs['src']   # 获取图片url
        except:
            house['pic_url'] = ''
        try:
            house_info = div.find('p', attrs = {'class': 'content__list--item--des'}).text.split('/')
            house['position'] = house_info[0].replace('\n', '').strip()  # 租房位置
            house['area'] = house_info[1].replace('\n', '').strip()  # 租房面积
            house['orientation'] = house_info[2].replace('\n', '').strip() # 租房朝向
            house['type'] = house_info[3].replace('\n', '').strip() # 租房户型
        except:
            house['position'] = ''
            house['area'] = ''
            house['orientation'] = ''
            house['type'] = ''
        if house['title'] == '' or house['pic_url'] == '':  # 对于没有标题或者没有图片的信息不保存
            continue
        houses.append(house)  # 添加到结果列表中
        
    return houses

def spider(url):
    """
    进程池目标函数
    :param url: 需要抓取的url
    :return 当前页面的所有租房信息列表
    """
    response = get_html(url)     # 获取每一页的html文本
    houses = parse_page(response)
    return houses

def main():
    """
    爬虫入口
    """
    all_houses = []  
    all_urls = [URL.format(page = page) for page in range(1, 11)]   # 构造所有请求URL
    pool = Pool()  # 使用进程池来进行下载
    res = [pool.apply_async(spider, (url,)) for url in all_urls]
    house_res = [item.get() for item in res]
    for items in house_res:
        all_houses.extend(items)
    pool.close()
    pool.join()

    print('总共抓取数据 %s 条' % (len(all_houses)))
    print('程序运行 %s s' % (time.perf_counter() - start_time))

if __name__ == '__main__':
    main()