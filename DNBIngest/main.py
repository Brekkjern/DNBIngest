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


@click.command()
@click.argument(
    'transaksjonsfil',
    nargs=1,
    type=click.File("r")
)
@click.argument(
    'destinasjonsmappe',
    nargs=1,
    type=click.Path(
        writable=True,
        resolve_path=True,
    )
)
def main(transaksjonsfil: str, destinasjonsmappe: str) -> None:
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

    # Laste inn CSV filen med DNB sitt format
    reader = csv.DictReader(transaksjonsfil, dialect="dnb")

    # Åpner destinasjonsfilene for skriving
    innskudd_fil = open(os.path.join(destinasjonsmappe, "innskudd.txt"), mode="w+", encoding="utf-8", newline="")
    innskudd_writer = csv.DictWriter(
        innskudd_fil,
        ["dato", "sum", "navn", "tag"],
        dialect="spreadsheet",
        extrasaction="ignore"
    )
    uttak_fil = open(os.path.join(destinasjonsmappe, "uttak.txt"), mode="w+", encoding="utf-8", newline="")
    uttak_writer = csv.DictWriter(
        uttak_fil,
        ["dato", "sum", "navn", "tag"],
        dialect="spreadsheet",
        extrasaction="ignore"
    )

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

        if transaksjon["innskudd"]:
            innskudd_writer.writerow(transaksjon)
        elif transaksjon["uttak"]:
            uttak_writer.writerow(transaksjon)
        else:
            print("Transaksjon mangler verdi for innskudd/uttak. {0[dato]} - {0[beskrivelse]}: {0[innskudd]} - {0[uttak]}".format(transaksjon))

    innskudd_fil.close()
    uttak_fil.close()