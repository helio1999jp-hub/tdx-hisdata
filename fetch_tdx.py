import requests
from bs4 import BeautifulSoup
import datetime
import os
import sys

# --- 配置区 ---
TARGET_URL = "https://www.tdx.com.cn/article/vipdata.html"
CALLBACK_URL = ""  # 填写你的回调URL
SAVE_PATH = "tdx_data.zip"

def is_in_time_window():
    """判断当前北京时间是否在 15:30 - 17:10 之间"""
    # GitHub Action 使用的是 UTC 时间，北京时间 = UTC + 8
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_beijing = now_utc + datetime.timedelta(hours=8)
    current_time = now_beijing.strftime("%H:%M")
    
    print(f"当前北京时间: {current_time}")
    return "15:30" <= current_time <= "17:10"

def check_and_download():
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.tdx.com.cn/"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 逻辑：寻找页面中包含“盘后行情”或“当日数据”且以 .zip 结尾的链接
        target_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text()
            # 根据通达信页面特征，通常文件名或描述包含日期
            if href.endswith('.zip') and (today_str in href or today_str in text):
                target_link = href
                if not target_link.startswith('http'):
                    target_link = "https://www.tdx.com.cn" + target_link
                break
        
        if not target_link:
            print(f"尚未检测到 {today_str} 的数据更新...")
            return False

        print(f"发现更新! 开始下载: {target_link}")
        with requests.get(target_link, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(SAVE_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print("下载成功并已保存。")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

def trigger_callback(status):
    if CALLBACK_URL:
        try:
            requests.post(CALLBACK_URL, json={"status": status, "msg": "TDX Data Updated"}, timeout=10)
        except:
            pass

if __name__ == "__main__":
    if not is_in_time_window():
        print("不在设定的 15:30-17:00 时间窗口内，跳过执行。")
        sys.exit(0)

    if check_and_download():
        trigger_callback("success")
    else:
        # 如果没找到数据，以非零状态退出，可以让 Action 显示“跳过”或失败
        # 但为了不收到烦人的失败报警，这里建议直接 exit(0)
        sys.exit(0)
