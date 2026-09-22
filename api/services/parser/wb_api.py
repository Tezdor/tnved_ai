import re
import requests

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED


class WildberriesAPI:

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    TIMEOUT = 2
    MAX_WORKERS = 8

    HOSTS = [
        f"https://basket-{i:02d}.wbcontent.net"
        for i in range(1, 61)
    ]

    @staticmethod
    def extract_nm_id(url: str) -> int:

        m = re.search(r"/catalog/(\d+)", url)

        if not m:
            raise ValueError("Не удалось определить артикул.")

        return int(m.group(1))

    @staticmethod
    def build_card_url(host, nm_id):

        vol = nm_id // 100000
        part = nm_id // 1000

        return (
            f"{host}"
            f"/vol{vol}"
            f"/part{part}"
            f"/{nm_id}"
            f"/info/ru/card.json"
        )
    
    @staticmethod
    def build_detail_url(nm_id):
        return (
            f"https://card.wb.ru/cards/v4/detail"
            f"?appType=1"
            f"&curr=rub"
            f"&dest=-1257786"
            f"&spp=30"
            f"&nm={nm_id}"
        )

    @classmethod
    def _try_host(cls, host, nm_id):

        url = cls.build_card_url(host, nm_id)

        try:

            r = requests.get(
                url,
                headers=cls.HEADERS,
                timeout=cls.TIMEOUT,
            )

            if r.status_code == 200:
                print("FOUND:", host)
                return r.json()

        except Exception:
            pass

        return None

    @classmethod
    def get_card(cls, product_url):

        nm_id = cls.extract_nm_id(product_url)

        executor = ThreadPoolExecutor(max_workers=cls.MAX_WORKERS)

        pending = []

        hosts = iter(cls.HOSTS)

        try:

            # запускаем первые 8 запросов
            for _ in range(cls.MAX_WORKERS):

                try:
                    host = next(hosts)
                except StopIteration:
                    break

                pending.append(
                    executor.submit(cls._try_host, host, nm_id)
                )

            while pending:

                done, pending = wait(
                    pending,
                    return_when=FIRST_COMPLETED
                )

                for future in done:

                    result = future.result()

                    if result is not None:

                        executor.shutdown(
                            wait=False,
                            cancel_futures=True,
                        )

                        return result

                    try:
                        host = next(hosts)

                        pending.add(
                            executor.submit(
                                cls._try_host,
                                host,
                                nm_id,
                            )
                        )

                    except StopIteration:
                        pass

        finally:
            executor.shutdown(wait=False)

        raise Exception("card.json не найден")

    @classmethod
    def get_detail(cls, nm_id):
        url = cls.build_detail_url(nm_id)

        print("\n========== WB DETAIL API ==========")
        print("URL:", url)

        try:
            response = requests.get(
                url,
                headers=cls.HEADERS,
                timeout=10
            )

            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text[:5000])

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print("DETAIL ERROR:", e)

        return None

    @classmethod
    def test_image_hosts(cls, nm_id):
        vol = nm_id // 100000
        part = nm_id // 1000

        print("\n========== TEST WB IMAGE HOSTS ==========")
        print("NM ID:", nm_id)
        print("VOL:", vol)
        print("PART:", part)

        for host in cls.HOSTS:

            image_url = (
                f"{host}/"
                f"vol{vol}/"
                f"part{part}/"
                f"{nm_id}/"
                f"images/c516x688/1.webp"
            )

            try:

                response = requests.get(
                    image_url,
                    headers=cls.HEADERS,
                    timeout=3
                )

                print(
                    host,
                    "=>",
                    response.status_code
                )

                if response.status_code == 200:

                    print(
                        "\n!!! IMAGE FOUND !!!"
                    )

                    print(
                        image_url
                    )

                    return image_url

            except Exception as e:

                print(
                    host,
                    "=> ERROR:",
                    type(e).__name__
                )

        print(
            "IMAGE NOT FOUND ON ANY HOST"
        )

        return None