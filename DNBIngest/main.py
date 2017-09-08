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
    'transaksjonsfil',
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
def main(transaksjonsfil: str, destination_folder: str) -> None:
    # Registrere DNB sin CSV dialekt
    csv.register_dialect("dnb", delimiter=";")

    # Registrere resultatdialekten
    csv.register_dialect("spreadsheet", delimiter="\t")

    regler = list()

    # Laste inn transaksjonsregler fra regel fil
    with open(os.path.join(__location__, "regler.json"), encoding="utf-8", newline="") as parserfile:
        jsondata = json.load(parserfile)

        for regel in jsondata:
            regler.append(Regel(regel))

    transaksjoner = list()

    # Laste inn CSV filen med DNB sitt format
    reader = csv.DictReader(transaksjonsfil, dialect="dnb")

    # Parse transaksjonslisten
    for row in reader:

        # Lag transaksjonsdictionary
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

        # Forsøk reglene på transaksjonen til den får et treff
        for regel in regler:
            if regel.parse_transaction(transaksjon):
                break

    # Liste over hvilke kolonner som skal brukes i filen som spyttes ut
    csvsekvens = ["dato", "sum", "navn", "tag"]

    innskudd = [transaksjon for transaksjon in transaksjoner if transaksjon["innskudd"]]
    uttak = [transaksjon for transaksjon in transaksjoner if transaksjon["uttak"]]

    # Skriv ut innskuddene denne måneden
    eksporter_transaksjoner(destination_folder, "innskudd.txt", innskudd, csvsekvens)
    eksporter_transaksjoner(destination_folder, "uttak.txt", uttak, csvsekvens)


def eksporter_transaksjoner(destinasjonsmappe: str, filnavn: str, transaksjoner: list, csvsekvens: list):
    with open(os.path.join(destinasjonsmappe, filnavn), mode="w+", encoding="utf-8", newline="") as fil:
        writer = csv.DictWriter(fil, csvsekvens, dialect="spreadsheet", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(transaksjoner)


class Regel(object):
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
