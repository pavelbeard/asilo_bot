import json

import requests as req
from bs4 import BeautifulSoup


def get_asylum_options(test: bool) -> BeautifulSoup:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.",
    }
    url = "https://www.policia.es/_es/extranjeria_asilo_y_refugio.php"

    if test:
        with open("asilo.php", "r") as file:
            asilo = file.read()

    else:
        asilo = req.get(url=url, headers=headers).text

    soup = BeautifulSoup(asilo, "lxml")

    provinces = soup.find_all("div", class_="col-12")[-2].find("ul")

    return provinces


def check_a_tags(tag):
    value = ""
    a_tags = tag.find_all("td")[1].find_all("a")
    if len(a_tags) > 1:
        for a in a_tags:
            value += a.text + " "
    else:
        value = tag.find_all("td")[1].text

    return value.strip()


def get_full_information(options: BeautifulSoup):
    tbodys = options.find_all("tbody")
    province_list = []
    for trs in tbodys:

        for tr in trs.find_all("tr"):
            options = {}
            province = ""
            try:
                attrs = tr.find("th").attrs
                options.update({
                    str(tr.find_all("td")[0].text).lower().strip().replace(" ", "_"): check_a_tags(tr)
                })
                province = tr.find("th").text
            except AttributeError:
                options.update({
                    str(tr.find_all("td")[0].text).lower().strip().replace(" ", "_"): check_a_tags(tr)
                })

            province_list.append({
                "province": province,
                "options": options
            })

    new_data = []
    for item in province_list:
        if item["province"] == "":
            prev_item = new_data[-1]
            prev_item["options"].update(item["options"])
        else:
            new_data.append(item)

    return new_data


def main():
    options = get_asylum_options(test=True)
    test = get_full_information(options=options)
    print(json.dumps(test, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
