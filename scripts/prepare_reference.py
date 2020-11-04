import csv
import sys
from pathlib import Path
from typing import Dict, List

HEADER_DELIMITER = "|"

sample_info_src = Path(sys.argv[1])
activities_srcs = [Path(src) for src in sys.argv[2:]]


class Disease:
    name: str
    code: str

    def __init__(self, name: str, code: str) -> None:
        self.name = name
        self.code = code


class Sample:
    name: str
    contributions: Dict[str, int]

    def __init__(self, name: str) -> None:
        self.name = name
        self.contributions = {}


def normalize_sample_name(s: str) -> str:
    components = s.rsplit("_", 1)

    if len(components) < 2:
        raise ValueError("invalid sample name '{}'".format(s))

    return components[0]


def read_sample_info(src: Path) -> Dict[str, Disease]:
    sample_name_diseases = {}

    with src.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sample_name = row["sample_name"]
            disease_name = row["sj_long_disease_name"]
            disease_code = row["sj_diseases"]
            sample_name_diseases[sample_name] = Disease(disease_name, disease_code)

    return sample_name_diseases


sample_name_diseases = read_sample_info(sample_info_src)

signatures = set()
samples: Dict[str, Sample] = {}

for activities_src in activities_srcs:
    f = activities_src.open(newline="")
    reader = csv.reader(f, delimiter="\t")
    headers = next(reader)

    sample_names = headers[1:]

    for row in reader:
        signature = row[0]
        contributions = row[1:]

        signatures.add(signature)

        for (sample_name, contribution) in zip(sample_names, contributions):
            if sample_name in samples:
                sample = samples[sample_name]
            else:
                sample = Sample(sample_name)
                samples[sample_name] = sample

            sample.contributions[signature] = int(contribution)

sample_names = list(samples.keys())
sample_names.sort()

activated_signatures = list(signatures)
activated_signatures.sort()

writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")

prepared_headers = []

for raw_sample_name in sample_names:
    sample_name = normalize_sample_name(raw_sample_name)

    if sample_name in sample_name_diseases:
        disease = sample_name_diseases[sample_name]

        header = "{}{}{}{}{}".format(
            sample_name,
            HEADER_DELIMITER,
            disease.code,
            HEADER_DELIMITER,
            disease.name,
        )

        prepared_headers.append(header)
    else:
        print(
            "WARN: unknown sample name '{}'".format(sample_name),
            file=sys.stderr,
        )
        prepared_headers.append(sample_name)

writer.writerow(["Samples"] + prepared_headers)

for signature in activated_signatures:
    row = [signature]

    for sample_name in sample_names:
        sample = samples[sample_name]

        if signature in sample.contributions:
            contribution = sample.contributions[signature]
            row.append(contribution)
        else:
            row.append(0)

    writer.writerow(row)
