#!/usr/bin/env python

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import time
import sys
import logging
import json


def wait(delay=1):
    time.sleep(delay)


def launch_browser():
    PATH_TO_CHROME_DRIVER = "/usr/bin/chromedriver"
    ASNB_URL = "https://www.myasnb.com.my/uhsessionexpired"
    browser = webdriver.Chrome(PATH_TO_CHROME_DRIVER)
    browser.get(ASNB_URL)
    return browser


def log_in(browser, asnb_username, asnb_password):
    logging.info('🔑 Logging in')
    browser.find_element_by_class_name("btn-login").click()
    browser.find_element_by_id("username").send_keys(asnb_username)
    browser.find_element_by_id("username").send_keys(Keys.ENTER)

    wait()
    browser.find_element_by_id("yes").click()
    browser.find_element_by_id("j_password_user").send_keys(asnb_password)
    browser.find_element_by_id("j_password_user").send_keys(Keys.ENTER)
    logging.info('🔓 Successfully logged in')

    browser.set_window_size(1600, 900)


def log_out(browser):
    wait()
    browser.find_element_by_link_text('LOG KELUAR').click()
    logging.info('🔒 Logged out gracefully')
    logging.info('💻 Closing browser in a second')
    wait()
    browser.close()


def main_page(browser, investment_amount):
    with open('funds.json', 'r') as f:
        fund_data = json.load(f)

    for fund in fund_data:
        if fund['skip']:
            continue

        fund_id = fund['elements']['id']
        initial_investment_xpath = fund['elements']['initial_investment_xpath']
        additional_investment_xpath = fund['elements']['additional_investment_xpath']

        logging.info(
            f"💲 Attempting to buy {fund['name']} ({fund['alternate_name']})")

        try:
            # Navigate to 'Produk' page
            browser.find_element_by_link_text('Produk').click()

            # Click 'Transaksi' drop down
            browser.find_element_by_xpath('//div[@class="faq-title1 accordionTitle glyphicon glyphicon-plus-sign"]').click()

        except NoSuchElementException:
            logging.warning('⛔️ User has uncleared session')
            if browser.current_url == "https://www.myasnb.com.my/uh/uhlogin/authfail":
                return True

        wait()
        browser.find_element_by_xpath('/html/body/div[3]/div[2]/div[1]/div[1]').click  # TODO: check what does this do

        try:
            # Figure out if the current attempt is an initial/additional investment
            try:
                wait()
                browser.find_element_by_xpath(initial_investment_xpath).click()
                logging.info('🤑 Initial Investment')

            except NoSuchElementException:
                wait()
                browser.find_element_by_xpath(additional_investment_xpath).click()
                wait()
                browser.find_element_by_id(fund_id).click()
                logging.info('💵 Additional Investment')

        except NoSuchElementException:
            try:
                browser.find_element_by_xpath(
                    "//*[contains(text(), 'MASA PELABURAN TAMAT')]")
                logging.error('⛔️ Investment time closed')
                log_out(browser)
                sys.exit()
            except NoSuchElementException:
                logging.error(
                    '⛔️ Unexpected error')
            continue

        wait()
        try:
            # PEP declaration
            logging.info(
                '📜 PEP declaration')
            wait()
            browser.find_element_by_id('NEXT').click()

        except NoSuchElementException:

            try:
                browser.find_element_by_xpath(
                    "//*[contains(text(), 'Tutup')]").click()
                logging.error(
                    '⛔️ Exceeded maximum attempt, please retry for 5 minutes')
                continue
            except Exception:
                logging.warning(
                    '💬 You do not need to declare PEP again')
                pass

        # Start purchasing loop
        logging.info(
            f"💸 Start purchasing loop for {fund['alternate_name']}...")
        purchase_unit(browser, investment_amount)

    # End of loop
    log_out(browser)


def purchase_unit(browser, investment_amount):
    browser.find_element_by_xpath(
        '/html/body/div[3]/form/div/div[1]/div[4]/label/p').click()
    browser.find_element_by_id('btn-unit-fund').click()
    wait()
    browser.find_element_by_xpath("//input[@placeholder='0.00']").send_keys(investment_amount)
    browser.find_element_by_xpath("//input[@placeholder='0.00']").send_keys(Keys.ENTER)

    for attempt in range(10):
        try:
            browser.find_element_by_xpath("//input[@placeholder='0.00']").send_keys(Keys.ENTER)
            logging.info(f"🎰 Attempt {attempt+1}")
            wait()
        except NoSuchElementException:
            browser.maximize_window()
            browser.set_window_position(0, 0)
            logging.info(
                f"🥳 Success! Please make your payment within the next 5 minutes")
            time.sleep(300)

        try:
            browser.find_element_by_xpath(
                "//*[contains(text(), 'Transaksi tidak berjaya. Sila hubungi Pusat Khidmat Pelanggan ASNB di talian 03-7730 8899. Kod Rujukan Gagal: 1001')]")
            browser.find_element_by_xpath(
                '/html/body/div[3]/form/div/div[1]/div[2]/div/div/input').send_keys(Keys.ENTER)
            return

        except NoSuchElementException:
            continue

    else:
        logging.info(f"🔚 End of loop")


if __name__ == "__main__":

    logging.getLogger().setLevel(logging.INFO)

    # Loads user info
    with open('users.json', 'r') as u:
        user_data = json.load(u)

    # Loop through all active user in users.json
    for user in user_data:
        if not user['is_active']:
            continue
        logging.info(f"{user['photo']} {user['uid']}")
        asnb_username = user['credentials']['username']
        asnb_password = user['credentials']['password']
        investment_amount = user['investment_amount']

        # Login
        browser = launch_browser()
        if log_in(browser, asnb_username, asnb_password):
            browser.close()
            logging.info('💡 Did you forget to logout somewhere else?')
            logging.info(
                '💡 Please always remember to logout to prevent uncleared session')
            continue

        # Main loop
        main_page(browser, investment_amount)

    else:
        sys.exit()
