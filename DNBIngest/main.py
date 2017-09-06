import click
import os.path
import csv
import datetime
import re
import json

__location__ = os.path.realpath(
    os.path.join(os.getcwd(),
                 os.path.dirname(__file__)
                 ))


@click.command()
@click.argument(
    'input-file',
    nargs=1,
    type=click.File("r")
)
@click.argument(
    'destination-folder',
    nargs=1,
    type=click.Path(
        writable=True,
        resolve_path=True,
    )
)
def main(input_file, destination_folder):
    # Registrere DNB sin CSV dialekt
    csv.register_dialect("dnb", delimiter=";")

    parsers = list()

    # Laste inn transaction paresere fra parser fil
    with open(os.path.join(__location__, "parsers.json"), encoding="utf-8", newline="") as parserfile:
        jsondata = json.load(parserfile)

        for parser in jsondata:
            parsers.append(Parser(parser))

    transaksjoner = list()

    # Laste inn CSV filen med DNB sitt format
    reader = csv.DictReader(input_file, dialect="dnb")

    # Parse transaksjonslisten
    for row in reader:
        transaksjon = dict()

        transaksjon["dato"] = datetime.datetime.strptime(row["Dato"], "%d.%m.%Y").date()
        transaksjon["beskrivelse"] = row["Forklaring"]
        transaksjon["navn"] = transaksjon["beskrivelse"]

        try:
            transaksjon["rentedato"] = datetime.datetime.strptime(row["Rentedato"], "%d.%m.%Y").date()
        except ValueError:
            transaksjon["rentedato"] = None

        try:
            transaksjon["uttak"] = float(row["Uttak"].strip(".").replace(",", "."))
        except ValueError:
            transaksjon["uttak"] = float()

        try:
            transaksjon["innskudd"] = float(row["Innskudd"].strip(".").replace(",", "."))
        except ValueError:
            transaksjon["innskudd"] = float()

        transaksjon["sum"] = transaksjon["uttak"] + transaksjon["innskudd"]

        transaksjoner.append(transaksjon)

        for parser in parsers:
            if parser.parse_transaction(transaksjon):
                break

    csvsekvens = ["dato", "sum", "navn", "tag"]

    innskudd = [transaksjon for transaksjon in transaksjoner if transaksjon["innskudd"]]
    uttak = [transaksjon for transaksjon in transaksjoner if transaksjon["uttak"]]

    # Skriv ut innskuddene denne måneden
    eksporter_transaksjoner(destination_folder, "innskudd.csv", innskudd, csvsekvens)
    eksporter_transaksjoner(destination_folder, "uttak.csv", uttak, csvsekvens)


def eksporter_transaksjoner(destinasjonsmappe, filnavn, transaksjoner, csvsekvens):
    with open(os.path.join(destinasjonsmappe, filnavn), mode="w+", encoding="utf-8", newline="") as fil:
        writer = csv.DictWriter(fil, csvsekvens, dialect="dnb", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(transaksjoner)


class Parser(object):
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)

        self.regex = re.compile(self.regex)

    def parse_transaction(self, transaksjon: dict) -> bool:
        if not transaksjon["uttak"] and not self.uttak:
            return False

        if not transaksjon["innskudd"] and not self.innskudd:
            return False

        regex_result = self.regex.match(transaksjon["beskrivelse"])

        if regex_result:
            transaksjon["tag"] = self.tag
            transaksjon["navn"] = self.navn
            return True

        return False
