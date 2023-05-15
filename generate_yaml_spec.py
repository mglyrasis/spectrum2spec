import logging
from typing import Any
from typing import Dict
from typing import List

import bs4
import requests_cache

from spectrum import SpectrumInformationGroup
from spectrum import SpectrumInformationGroupType
from spectrum import SpectrumUnit

# How to find attributes on the pages
normal_dict: Dict[str, str] = {
    "definition": "div#unit-definition",
    "how_to_record": "div#unit-recording",
    "examples": "div#unit-examples",
    "use": "div#unit-use",
    "information_group": "div#unit-required",
}

# How to find attributes for pages that are incorrectly formatted
fixing_dict: Dict[str, Dict[str, str]] = {
    "object-name-note": {
        "definition": "div#unit-recording :first-child",
        "how_to_record": "div#unit-recording > h3 + p",
    },
    "legal-licence-requirements-held": {
        "use": "div#unit-examples + div#unit-recording > p",
    },
}

fix_examples: List[str] = ["; however", "instrument;"]

session = requests_cache.CachedSession("spectrum_cache")


def to_python_identifier(string: str) -> str:
    matrix = str.maketrans(" -/'", "____")
    return string.translate(matrix).lower()


def de_unicode(string: str) -> str:
    matrix = str.maketrans("\u2013\u2018\u2019\u201C\u201D", "-''\"\"")
    return string.translate(matrix)


def request_url(url: str) -> bs4.BeautifulSoup:
    global session
    if not url.startswith("https") and url.startswith("/"):
        url = f"https://collectionstrust.org.uk{url}"
    # The site generates some URLs without trailing slashes, but those requests are redirected
    # This requests the redirected URL which will have been cached.
    if not url.endswith("/"):
        url += "/"
    r = session.get(url)
    return bs4.BeautifulSoup(r.text, features="html.parser")


def get_field(url: str) -> SpectrumUnit:
    global normal_dict
    global fixing_dict
    global fix_examples

    soup = request_url(url)
    main = soup.find("main", class_="site-main")
    su: SpectrumUnit = SpectrumUnit(name=main.find("h1").text, url=url)
    contents = main.find("div", class_="entry-content")

    for k, v in normal_dict.items():
        element: bs4.element.Tag = contents.select_one(v)

        if element is not None:
            text: str = element.text.strip()
            # Remove the first line if it's the same length as the title
            if "\n" in text and len(text.split("\n")[0]) == len(k):
                text = text.split("\n", 1)[1]
            setattr(su, k, de_unicode(text))
        else:
            logging.warning(f"Could not find {k} for {url}")

    # If attributes are missing/erroneous because this object has a fixing_dict entry, replace them.
    for url_key, attr_dict in fixing_dict.items():
        if url_key in url:
            for attr, value in attr_dict.items():
                try:
                    setattr(su, attr, de_unicode(contents.select_one(value).text.strip()))
                except AttributeError as ae:
                    logging.warning(f"Error setting attribute {attr} for {url_key} from {value}")
                    logging.warning(contents)

    # Convert examples to a list where possible.
    if isinstance(su.examples, str):
        # Detect a couple manual exceptions...
        if ";" in su.examples and not any(x in su.examples for x in fix_examples):
            su.examples = [x.strip() for x in su.examples.split(";")]
        elif "\n" in su.examples:
            su.examples = [x.strip() for x in su.examples.split("\n")]
        else:
            su.examples = [su.examples]

    return su


def get_group_fields(url: str) -> List[SpectrumUnit]:
    soup = request_url(url)
    unit_list = soup.find("div", id="unitlist")
    if not unit_list:
        return []

    units = unit_list.find_all("li")
    spectrum_units: List[SpectrumUnit] = []
    for unit in units:
        unit_name = unit.find("a").text.strip()
        unit_url = unit.find("a")["href"]

        su: SpectrumUnit = get_field(unit_url)
        su.name = de_unicode(unit_name)
        su.url = unit_url

        if unit.find("ul"):
            # There are subfields...
            subfields = unit.find("ul").find_all("li")
            for subfield in subfields:
                subfield_name = de_unicode(subfield.find("a").text.strip())
                subfield_url = subfield.find("a")["href"]
                subfield_su: SpectrumUnit = get_field(subfield_url)
                subfield_su.name = de_unicode(subfield_name)
                subfield_su.url = subfield_url
                su.members[to_python_identifier(subfield_name)] = subfield_su

        spectrum_units.append(su)

    return spectrum_units


def get_information_group_type(url: str) -> SpectrumInformationGroupType:
    soup = request_url(url)
    # Clean up URL for output since for some reason, these are the only ones with domain included.
    url = url.replace("https://collectionstrust.org.uk", "")
    main = soup.find("main", class_="site-main")
    desc = main.find("div", class_="further-description")
    information_groups = desc.select("p > a[href]")
    igt: SpectrumInformationGroupType = SpectrumInformationGroupType(
        name=main.find("h1").text, description=de_unicode(desc.find("p").text), url=url
    )
    for information_group in information_groups:
        group = information_group.parent
        group_name = de_unicode(information_group.text.strip())
        group_url = information_group["href"]
        group_description = de_unicode(group.text.replace(group_name, "", 1).strip())

        sig: SpectrumInformationGroup = SpectrumInformationGroup(
            name=group_name, description=group_description, url=group_url
        )
        for field in get_group_fields(group_url):
            sig.members[to_python_identifier(field.name)] = field
        igt.members[to_python_identifier(group_name)] = sig

    return igt


def get_appendices() -> Dict[str, SpectrumInformationGroupType]:
    soup = request_url("https://collectionstrust.org.uk/spectrum/information-requirements/")
    main = soup.find("main", class_="site-main")
    appendices = main.find_all("li", class_="untranslated")
    group_types: Dict[str, SpectrumInformationGroupType] = {}
    for appendix in appendices:
        url = appendix.find("a")["href"]
        category = de_unicode(appendix.find("a").text)
        if url:
            group_types[to_python_identifier(category)] = get_information_group_type(url)

    return group_types


if __name__ == "__main__":
    appendix_list: Dict[str, SpectrumInformationGroupType] = get_appendices()

    # Flatten to a dictionary
    d: Dict[str, Any] = {}
    for group_type in appendix_list.values():
        group_type_name: str = to_python_identifier(group_type.name)
        d[group_type_name] = group_type.model_dump(exclude_defaults=True)

    import datetime

    import yaml

    now = datetime.datetime.now()
    with open(f"spectrum-{now.strftime('%Y%m%d')}.yaml", "w") as stream:
        yaml.dump(d, stream)
