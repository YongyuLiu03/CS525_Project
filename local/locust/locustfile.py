from locust import task, run_single_user, between
from locust import FastHttpUser


class recording(FastHttpUser):
    wait_time = between(1, 3)
    
    host = "http://172.22.151.23:32556"
    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "172.22.151.23:32556",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    @task
    def t(self):
        with self.client.request(
            "POST",
            "/setCurrency",
            headers={
                "Content-Length": "17",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/",
            },
            data="currency_code=USD",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/",
            headers={"Referer": "http://172.22.151.23:32556/"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/setCurrency",
            headers={
                "Content-Length": "17",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/",
            },
            data="currency_code=GBP",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/",
            headers={"Referer": "http://172.22.151.23:32556/"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/OLJCESPC7Z",
            headers={"Referer": "http://172.22.151.23:32556/"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart",
            headers={
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/product/OLJCESPC7Z",
            },
            data="product_id=OLJCESPC7Z&quantity=4",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/cart",
            headers={"Referer": "http://172.22.151.23:32556/product/OLJCESPC7Z"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/OLJCESPC7Z",
            headers={"Referer": "http://172.22.151.23:32556/cart"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/2ZYFJ3GM2N",
            headers={"Referer": "http://172.22.151.23:32556/product/OLJCESPC7Z"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart",
            headers={
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/product/2ZYFJ3GM2N",
            },
            data="product_id=2ZYFJ3GM2N&quantity=1",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/cart",
            headers={"Referer": "http://172.22.151.23:32556/product/2ZYFJ3GM2N"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/",
            headers={"Referer": "http://172.22.151.23:32556/cart"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/L9ECAV7KIM",
            headers={"Referer": "http://172.22.151.23:32556/"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/6E92ZMYYFZ",
            headers={"Referer": "http://172.22.151.23:32556/product/L9ECAV7KIM"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/cart",
            headers={"Referer": "http://172.22.151.23:32556/product/6E92ZMYYFZ"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart/checkout",
            headers={
                "Content-Length": "253",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/cart",
            },
            data="email=someone%40example.com&street_address=1600+Amphitheatre+Parkway&zip_code=94043&city=Mountain+View&state=CA&country=United+States&credit_card_number=4432801561520454&credit_card_expiration_month=1&credit_card_expiration_year=2026&credit_card_cvv=672",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/",
            headers={"Referer": "http://172.22.151.23:32556/cart/checkout"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/66VCHSJNUP",
            headers={"Referer": "http://172.22.151.23:32556/"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart",
            headers={
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/product/66VCHSJNUP",
            },
            data="product_id=66VCHSJNUP&quantity=1",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/cart",
            headers={"Referer": "http://172.22.151.23:32556/product/66VCHSJNUP"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/product/LS4PSXUNUM",
            headers={"Referer": "http://172.22.151.23:32556/cart"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart",
            headers={
                "Content-Length": "32",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/product/LS4PSXUNUM",
            },
            data="product_id=LS4PSXUNUM&quantity=1",
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/cart",
            headers={"Referer": "http://172.22.151.23:32556/product/LS4PSXUNUM"},
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "POST",
            "/cart/empty",
            headers={
                "Content-Length": "0",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "http://172.22.151.23:32556",
                "Referer": "http://172.22.151.23:32556/cart",
            },
            catch_response=True,
        ) as resp:
            pass
        with self.client.request(
            "GET",
            "/",
            headers={"Referer": "http://172.22.151.23:32556/cart"},
            catch_response=True,
        ) as resp:
            pass


if __name__ == "__main__":
    run_single_user(recording)
