
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import time
import os
import sys

def do_tplink_reboot():
    driver = webdriver.Chrome()

    # 192.168.1.1 にアクセス。
    driver.get('https://192.168.1.1')
    time.sleep(5)

    # ウィンドウを最大化。
    driver.maximize_window()
    time.sleep(5)

    # SSL Handsake のページで Advanced をクリックする。
    details_button = driver.find_element(By.ID, "details-button")
    details_button.click()
    time.sleep(1)

    # Proceed link をクリックする。
    proceed_link = driver.find_element(By.ID, "proceed-link")
    proceed_link.click()
    time.sleep(15)

    # パスワード入力
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.send_keys("VMware123!!!")
    time.sleep(1)

    # Log In ボタンをクリック。
    login_button = driver.find_element(By.CSS_SELECTOR, "a.button-button[title='LOG IN']")
    login_button.click()
    time.sleep(10)

    # Advanced をクリック。
    advanced_menu = driver.find_element(By.CSS_SELECTOR, "li[navi-value='advanced']")
    advanced_menu.click()
    time.sleep(3)

    # System をクリック。
    system = driver.find_element(By.CSS_SELECTOR, "li[navi-value='system']")
    system.click()
    time.sleep(3)

    # Reboot をクリック。
    reboot = driver.find_element(By.CSS_SELECTOR, "li[navi-value='reboot']")
    reboot.click()
    time.sleep(3)

    # Reboot All をクリック。
    reboot_all_button = driver.find_element(By.CSS_SELECTOR, "a[title='REBOOT ALL']")
    reboot_all_button.click()
    time.sleep(3)

    # OK をクリックする。
    ok = driver.find_element(By.ID, "global-confirm-btn-ok")
    ok.click()
    time.sleep(10)
    driver.close()


# 指定したホストに Ping  を送信し、成功した場合は True を返す。
def ping_and_sleep(logger, host):
    try:
        response = os.system(f"ping -n 1 -w 2000 {host} > C:\\gomi.txt")
        time.sleep(1)

        if response == 0:
            logger.debug(f"ping to {host} seikou.")
            return True
        else:
            logger.error(f"ping to {host} shippai!!!")
            return False
    except Exception as e:
        logger.error(f"Execute ping failed. {e}")
        return True


# hostname に Ping を送る。
# 戻り値:
#   応答があれば True を返す。
#   応答がない場合は False を返す。
def monitor_host(logger, hostname):
    for i in range(5):
        if ping_and_sleep(logger, hostname):
            return True
    return False

def monitor_network(logger):
    logger.info('Start tplink router monitoring.')

    while True:
        time.sleep(5)

        # 1. 1.1.1.1 に Ping
        if monitor_host(logger, "1.1.1.1"):
            continue
        logger.warning("1.1.1.1 is down.")

        # 2. 1.1.1.1 に Ping が途絶えた場合、8.8.8.8 に Ping
        if monitor_host(logger, "8.8.8.8"):
            logger.info("8.8.8.8 is reachable. Returning to monitor 1.1.1.1.")
            continue
        logger.warning("8.8.8.8 is down.")

        # 3. 8.8.8.8 も応答しない場合、192.168.1.1 に Ping
        if not ping_and_sleep(logger, "192.168.1.1"):
            logger.warning("192.168.1.1 is unreachable. Assuming VM networking is down.")
            continue
        if not ping_and_sleep(logger, "192.168.1.1"):
            logger.warning("192.168.1.1 is unreachable. Assuming VM networking is down.")
            continue
        if not ping_and_sleep(logger, "192.168.1.1"):
            logger.warning("192.168.1.1 is unreachable. Assuming VM networking is down.")
            continue
        logger.error("Got 3 pongs from 192.168.1.1. LAN is alive. Assuming the Internet is down.")

        # 4. 192.168.1.1 が Ping 応答する場合、最後にもう一度 8.8.8.8 に Ping する。
        # ルーター再起動後に運良く 8.8.8.8 ping なし、192.168.1.1 応答ありの状態となる状況を回避する。
        if monitor_host(logger, "8.8.8.8"):
            logger.info("8.8.8.8 is reachable. Returning to monitor 1.1.1.1.")
            continue
        logger.warning("8.8.8.8 is down.")

        logger.error("Assuming router is down. Issuing reset.")
        os.system(f"date /t >> C:\\reboot_hist.txt")

        try:
            do_tplink_reboot()
        except Exception as e:
            logger.error(f"do_tplink_reboot() error. {e}")

# モニタリング開始
if __name__ == "__main__":
    # Setup for logger.
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] [%(funcName)s] %(message)s")

    log_file_handler = logging.FileHandler("tplink_monitor.log", encoding="utf-8")
    log_stdout_handler = logging.StreamHandler()

    log_file_handler.setFormatter(formatter)
    log_stdout_handler.setFormatter(formatter)

    logger.addHandler(log_file_handler)
    logger.addHandler(log_stdout_handler)

    logger.debug("Logger setup done.")

    if len(sys.argv) == 2 and sys.argv[1] == "reboot":
        # Do router reboot and exit.
        logger.info("Rebooting router.")
        try:
            do_tplink_reboot()
        except Exception as e:
            logger.error(f"do_tplink_reboot() error. {e}")
        sys.exit(0)

    monitor_network(logger)
