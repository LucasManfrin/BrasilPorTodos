"""Bounded official OFSS workbook; functional execution is independent from RTN totals."""

import codecs
import hashlib
import io
import json
import re
import stat
import time
import zipfile
import zlib
from collections import defaultdict
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from uuid import UUID
from xml.etree import ElementTree as ET

from app.integrations.bcb import NoRedirect

PARSER_VERSION = "1.0.0"
PRECISION_VERSION = "row-half-even-cent-v1"
DATASET_ID = "8675a0a4-31c5-4593-a24d-fb8e17376eca"
SOURCE_URL = "https://www.tesourotransparente.gov.br/ckan/dataset/despesas-e-transferencias-totais"
CATALOG_URL = (
    "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show"
    "?id=despesas-e-transferencias-totais"
)
SOURCE = {
    "title": "Despesas e Transferências Totais da União (critério valor pago)",
    "institution": "Secretaria do Tesouro Nacional",
    "url": SOURCE_URL,
    "license": "ODbL 1.0",
    "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
}
SCOPE = "GOVERNMENT_CENTRAL_OFSS_SOURCE"
STAGES = ("PAID", "RAP_PAID", "TOTAL_PAID")
NATURES = {"PRIMARY": "Primária", "FINANCIAL": "Despesa Financeira", "EXTRA_SIAFI": "Extra-Siafi"}
ABSENCE_POLICY = (
    "Apenas combinações observadas são apresentadas; ausência de função/natureza/mês não é zero. "
    "Totais anuais somam os registros observados, com meses e número de linhas explícitos."
)
SUBSET_SCOPE = (
    "Categorias exatas da tabela dinâmica RTN da própria fonte; não é o total das funções "
    "nem o primário acima da linha. Inclui transferências, financeiras selecionadas e Extra-Siafi."
)
HEADERS = (
    "ID_ANO ID_MES MES_LANCAMENTO ORGAO_CODIGO ORGAO_DESCRICAO "
    "UNIDADE_ORCAMENTARIA_CODIGO UNIDADE_ORCAMENTARIA_DESCRICAO CO_FONTE_RECURSO "
    "NO_FONTE_RECURSO ID_GRUPO_DESPESA_NADE NO_GRUPO_DESPESA_NADE CO_MOAP_NADE "
    "NO_MOAP_NADE ID_IN_RESULTADO_EOF NO_IN_RESULTADO_EOF ID_IN_TP_CREDITO_CEOR "
    "NO_IN_TP_CREDITO_CEOR ID_FUNCAO_PT NO_FUNCAO_PT ID_SUBFUNCAO_PT NO_SUBFUNCAO_PT "
    "ID_PROGRAMA_PT NO_PROGRAMA_PT ACAO NO_ACAO SALDO_PLOA DOTACAO_INICIAL "
    "DOTACAO_ATUALIZADA DESPESAS_EMPENHADAS DESPESAS_LIQUIDADAS DESPESAS_PAGAS "
    "RESTOS_A_PAGAR_PAGOS PAGAMENTOS_TOTAIS PODER PRIMARIA_FINANCEIRA CATEGORIA_LC200 "
    "CATEGORIA_RTN"
).split()
FUNCTION_LABELS = dict(
    zip(
        [f"{i:02}" for i in range(1, 29)] + ["99"],
        (
            "LEGISLATIVA|JUDICIARIA|ESSENCIAL A JUSTICA|ADMINISTRACAO|DEFESA NACIONAL|"
            "SEGURANCA PUBLICA|RELACOES EXTERIORES|ASSISTENCIA SOCIAL|PREVIDENCIA SOCIAL|"
            "SAUDE|TRABALHO|EDUCACAO|CULTURA|DIREITOS DA CIDADANIA|URBANISMO|HABITACAO|"
            "SANEAMENTO|GESTAO AMBIENTAL|CIENCIA E TECNOLOGIA|AGRICULTURA|ORGANIZACAO AGRARIA|"
            "INDUSTRIA|COMERCIO E SERVICOS|COMUNICACOES|ENERGIA|TRANSPORTE|DESPORTO E LAZER|"
            "ENCARGOS ESPECIAIS|RESERVA DE CONTINGENCIA"
        ).split("|"),
        strict=True,
    )
)
MAX_DOWNLOAD = 40_000_000
MAX_EXPANDED = 350_000_000
MAX_SHEET = 220_000_000
MAX_STRINGS = 1_000_000
MAX_ROWS = 200_000
CENT = Decimal("0.01")
MONEY_LIMIT = Decimal("100000000000000")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_DECIMAL = re.compile(r"[+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d{1,2})?\Z")
_CELL = re.compile(r"([A-Z]{1,3})([1-9]\d{0,5})\Z")


def _closed_year(year, as_of):
    if type(year) is not int or type(as_of) is not date or not 2008 <= year < as_of.year:
        raise ValueError("Choose a closed calendar year from the reviewed source.")


def _resource_url(url, resource_id):
    try:
        if str(UUID(resource_id)) != resource_id:
            raise ValueError("Invalid resource identity.")
        parts = urlsplit(url)
        prefix = f"/ckan/dataset/{DATASET_ID}/resource/{resource_id}/download/"
        if (
            parts.scheme != "https"
            or parts.hostname != "www.tesourotransparente.gov.br"
            or parts.port not in (None, 443)
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or not parts.path.startswith(prefix)
            or not re.fullmatch(r"[A-Za-z0-9_-]+\.xlsx", parts.path[len(prefix) :])
        ):
            raise ValueError("Unapproved official workbook URL.")
    except (TypeError, AttributeError) as exc:
        raise ValueError("Invalid official resource.") from exc


def _download(url, limit):
    if url != CATALOG_URL:
        match = re.search(r"/resource/([0-9a-f-]{36})/download/", url)
        if not match:
            raise ValueError("Unapproved source URL.")
        _resource_url(url, match[1])
    request = Request(
        url, headers={"Accept-Encoding": "identity", "User-Agent": "BrasilPorTodos/0.1"}
    )
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=20) as response:
        if response.geturl() != url or response.headers.get("Content-Encoding", "identity") not in (
            "identity",
            "",
        ):
            raise ValueError("Redirects and HTTP content encodings are not accepted.")
        length = response.headers.get("Content-Length")
        if length is not None and (not length.isdigit() or int(length) > limit):
            raise ValueError("Official download exceeds its limit.")
        chunks, size = [], 0
        while chunk := response.read(min(65536, limit - size + 1)):
            size += len(chunk)
            if size > limit or time.monotonic() - started > 120:
                raise ValueError("Official download exceeds size/time budget.")
            chunks.append(chunk)
        if length is not None and size != int(length):
            raise ValueError("Truncated official download.")
    return b"".join(chunks)


def _unique_object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("Duplicate metadata key.")
        output[key] = value
    return output


def _metadata(payload, year):
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ValueError("Unexpected official catalog response.")
    dataset = payload.get("result")
    if (
        not isinstance(dataset, dict)
        or dataset.get("id") != DATASET_ID
        or dataset.get("name") != "despesas-e-transferencias-totais"
        or dataset.get("license_id") != "odc-odbl"
        or not isinstance(dataset.get("resources"), list)
    ):
        raise ValueError("Official dataset or license differs from reviewed catalog.")
    resources = [
        r
        for r in dataset["resources"]
        if isinstance(r, dict) and r.get("name") == (f"Despesas e Transferências da União - {year}")
    ]
    if len(resources) != 1:
        raise ValueError("Expected exactly one annual official resource.")
    item = resources[0]
    _resource_url(item.get("url"), item.get("id"))
    size = item.get("size")
    if isinstance(size, str) and re.fullmatch(r"[1-9]\d{0,7}", size):
        size = int(size)
    if (
        item.get("format", "").upper() != "XLSX"
        or type(size) is not int
        or not 0 < size <= MAX_DOWNLOAD
        or not isinstance(item.get("last_modified"), str)
    ):
        raise ValueError("Unbounded or unversioned official resource.")
    try:
        datetime.fromisoformat(item["last_modified"])
    except ValueError as exc:
        raise ValueError("Invalid official resource modification date.") from exc
    return {**{key: item[key] for key in ("id", "url", "last_modified")}, "size": size}


def _xml(raw):
    _scan_xml(raw)
    return ET.fromstring(raw)


def _scan_xml(raw):
    if b"\x00" in raw or re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, re.I):
        raise ValueError("XML entities, DTD and non-UTF8 encodings are forbidden.")


class _SafeStream:
    """Scan streamed XML across chunk boundaries before handing it to ElementTree."""

    def __init__(self, source, limit, *, allow_ignored_utf16=False):
        self.source, self.limit, self.size, self.tail = source, limit, 0, b""
        self.allow_ignored_utf16 = allow_ignored_utf16
        self.first = True
        self.decoder = None

    def read(self, size=-1):
        chunk = self.source.read(min(size if size >= 0 else 65536, 65536))
        self.size += len(chunk)
        if self.size > self.limit:
            raise ValueError("Expanded XML exceeds its bound.")
        if self.first and chunk:
            self.first = False
            if self.allow_ignored_utf16 and chunk.startswith((b"\xff\xfe", b"\xfe\xff")):
                self.decoder = codecs.getincrementaldecoder("utf-16")("strict")
        scanned = (
            self.decoder.decode(chunk, final=not chunk).encode("utf-8") if self.decoder else chunk
        )
        _scan_xml(self.tail + scanned)
        self.tail = (self.tail + scanned)[-64:]
        return chunk


def _zip(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_DOWNLOAD:
        raise ValueError("Unbounded official workbook.")
    z = zipfile.ZipFile(io.BytesIO(raw))
    names = set()
    expanded = 0
    if not 1 <= len(z.infolist()) <= 256:
        raise ValueError("Unexpected ZIP entry count.")
    for item in z.infolist():
        if (
            item.orig_filename != item.filename
            or item.filename in names
            or item.filename.startswith("/")
            or "\\" in item.orig_filename
            or any(part in ("..", ".") or ":" in part for part in item.filename.split("/"))
            or item.flag_bits & 1
            or stat.S_ISLNK(item.external_attr >> 16)
            or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            or item.file_size > MAX_SHEET
        ):
            raise ValueError("Unsafe or duplicate ZIP entry.")
        names.add(item.filename)
        expanded += item.file_size
    if expanded > MAX_EXPANDED:
        raise ValueError("Expanded workbook exceeds its limit.")
    # Consume each bounded member to check CRC. Scan even ignored XML caches/connections;
    # they are never parsed as executable content, extracted, or followed over the network.
    started = time.monotonic()
    for item in z.infolist():
        with z.open(item) as source:
            stream = (
                _SafeStream(source, item.file_size, allow_ignored_utf16=True)
                if item.filename.endswith((".xml", ".rels"))
                else source
            )
            while stream.read(65536):
                if time.monotonic() - started > 180:
                    raise ValueError("Workbook validation exceeds its time budget.")
    return z


def _small_xml(z, path, limit):
    if z.getinfo(path).file_size > limit:
        raise ValueError("Workbook metadata exceeds its bound.")
    return _xml(z.read(path))


def _sheets(z, year):
    workbook = _small_xml(z, "xl/workbook.xml", 100_000)
    relationships = _small_xml(z, "xl/_rels/workbook.xml.rels", 100_000)
    mapping = {}
    for row in relationships.findall(PKG + "Relationship"):
        key = row.attrib.get("Id")
        if key in mapping:
            raise ValueError("Duplicate workbook relationship.")
        mapping[key] = row.attrib
    output = {}
    for row in workbook.findall(NS + "sheets/" + NS + "sheet"):
        name = row.attrib.get("name")
        if name not in (str(year), "Resumo Pagamento Total"):
            continue
        relation = mapping.get(row.attrib.get(REL + "id"), {})
        target = relation.get("Target", "")
        if (
            name in output
            or relation.get("TargetMode") == "External"
            or not relation.get("Type", "").endswith("/worksheet")
            or not re.fullmatch(r"worksheets/sheet[1-9]\d*\.xml", target)
        ):
            raise ValueError("Unexpected annual worksheet relationship.")
        output[name] = "xl/" + target
    if len(output) != 2:
        raise ValueError("Annual data and independent published summary are required.")
    return output


def _strings(z):
    root = _small_xml(z, "xl/sharedStrings.xml", MAX_STRINGS)
    if root.tag != NS + "sst":
        raise ValueError("Unexpected shared strings namespace.")
    strings = ["".join(t.text or "" for t in row.iter(NS + "t")) for row in root.findall(NS + "si")]
    if len(strings) > 50_000 or any(len(item) > 5000 for item in strings):
        raise ValueError("Workbook strings exceed bounds.")
    return strings


def _rows(z, path, strings, *, summary=False):
    with z.open(path) as source:
        stream = _SafeStream(source, MAX_SHEET if not summary else 1_000_000)
        data = None
        previous = 0
        dimension = None
        for event, element in ET.iterparse(stream, events=("start", "end")):
            if event == "start":
                if element.tag == NS + "dimension":
                    dimension = element.attrib.get("ref")
                elif element.tag == NS + "sheetData":
                    data = element
                continue
            if element.tag != NS + "row":
                continue
            index = element.attrib.get("r", "")
            if not index.isdigit() or not previous < int(index) <= MAX_ROWS + 1:
                raise ValueError("Duplicate, unordered or unbounded worksheet row.")
            number = int(index)
            if not summary and number != previous + 1:
                raise ValueError("Missing annual worksheet row.")
            previous = number
            cells = {}
            seen_cells = set()
            for cell in element.findall(NS + "c"):
                match = _CELL.fullmatch(cell.attrib.get("r", ""))
                if not match or int(match[2]) != number or match[1] in seen_cells:
                    raise ValueError("Invalid or duplicate worksheet cell.")
                column = match[1]
                seen_cells.add(column)
                if summary and column not in (
                    "O",
                    "P",
                    "Q",
                    "R",
                    "S",
                    "T",
                    "U",
                    "V",
                    "W",
                    "X",
                    "Y",
                    "Z",
                    "AA",
                    "AB",
                ):
                    continue
                if cell.find(NS + "f") is not None:
                    raise ValueError("Formulas cannot supply source observations.")
                kind = cell.attrib.get("t", "n")
                if not summary and number > 1 and column in ("AE", "AF", "AG") and kind != "n":
                    raise ValueError("Money must be numeric source cells, not text or boolean.")
                values = cell.findall(NS + "v")
                if summary and not values and kind != "inlineStr":
                    continue  # Styled blank summary cells are absent, never monetary zero.
                if kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(NS + "t"))
                elif len(values) == 1 and values[0].text is not None:
                    value = values[0].text
                    if kind == "s":
                        if not value.isdigit() or not 0 <= int(value) < len(strings):
                            raise ValueError("Invalid shared string index.")
                        value = strings[int(value)]
                    elif kind != "n":
                        raise ValueError("Unexpected worksheet cell type.")
                else:
                    raise ValueError("Missing or duplicate worksheet value.")
                if len(value) > 5000:
                    raise ValueError("Oversized worksheet value.")
                cells[column] = value
            element.clear()
            if data is not None:
                data.remove(element)
            yield number, cells
        if not summary and dimension != f"A1:AK{previous}":
            raise ValueError("Annual worksheet dimension does not match parsed rows.")


def _number(value):
    if not isinstance(value, str) or len(value) > 64 or not _DECIMAL.fullmatch(value):
        raise ValueError("Invalid source monetary value.")
    number = Decimal(value)
    if not number.is_finite() or abs(number) >= MONEY_LIMIT or number.as_tuple().exponent < -24:
        raise ValueError("Nonfinite, excessive or unsupported monetary precision.")
    return number


def _money(value):
    return _number(value).quantize(CENT, rounding=ROUND_HALF_EVEN)


def _amounts(values):
    return {stage: format(values.get(stage, Decimal(0)), ".2f") for stage in STAGES}


def _classification(code, label, nature):
    if not isinstance(code, str) or not re.fullmatch(r"\d{1,2}", code):
        raise ValueError("Invalid published function code.")
    normalized = code.zfill(2)
    if normalized == "99" and label in ("N/A", "OUTRAS"):
        if nature != "EXTRA_SIAFI":
            raise ValueError("Unclassified adjustments must remain Extra-Siafi.")
        return "UNCLASSIFIED_NA" if label == "N/A" else "UNCLASSIFIED_OTHER", "UNCLASSIFIED"
    if FUNCTION_LABELS.get(normalized) != label:
        raise ValueError("Function identity differs from reviewed catalog.")
    return "FUNCTION_" + normalized, "BUDGET_FUNCTION"


def _published(z, path, strings):
    labels, total, header = set(), None, False
    cols = ("P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA")
    for _, cells in _rows(z, path, strings, summary=True):
        name = cells.get("O")
        if name == "Rótulos de Linha":
            if [cells.get(col) for col in cols] != [str(m) for m in range(1, 13)]:
                raise ValueError("Published monthly summary columns differ.")
            header = True
        elif name == "Total Geral":
            if total is not None or not header:
                raise ValueError("Duplicate or unordered published total.")
            total = {month: _money(cells.get(col)) for month, col in enumerate(cols, 1)}
            total["annual"] = _money(cells.get("AB"))
        elif name and header and total is None:
            if not re.match(r"[12]\.\d", name) or name in labels:
                raise ValueError("Unknown or duplicate published summary category.")
            labels.add(name)
    if not labels or total is None:
        raise ValueError("Missing independent published payment summary.")
    return labels, total


def fingerprint(payload):
    canonical = {key: value for key, value in payload.items() if key != "fingerprint"}
    return hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def parse_workbook(raw, year, resource):
    try:
        return _parse_workbook(raw, year, resource)
    except (
        zipfile.BadZipFile,
        zlib.error,
        ET.ParseError,
        KeyError,
        TypeError,
        InvalidOperation,
    ) as exc:
        raise ValueError("Invalid or incomplete official functional workbook.") from exc


def _parse_workbook(raw, year, resource):
    """Pure parser: complete file is validated before a JSON-safe cohort is returned."""
    _closed_year(year, date.today())
    _resource_url(resource.get("url"), resource.get("id"))
    if resource.get("size") != len(raw):
        raise ValueError("Workbook size differs from official metadata.")
    with localcontext() as context:
        context.prec = 50
        with _zip(raw) as z:
            sheets, strings = _sheets(z, year), _strings(z)
            labels, published = _published(z, sheets["Resumo Pagamento Total"], strings)
            monthly = defaultdict(lambda: defaultdict(Decimal))
            groups, identities, counts, month_counts = {}, {}, defaultdict(int), defaultdict(int)
            raw_totals, rounded_totals = defaultdict(Decimal), defaultdict(Decimal)
            subset, raw_subset, seen_categories = defaultdict(Decimal), defaultdict(Decimal), set()
            row_count, max_diff = 0, Decimal(0)
            columns = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(11)]
            for number, cells in _rows(z, sheets[str(year)], strings):
                if set(cells) != set(columns):
                    raise ValueError("All 37 declared source fields are required.")
                if number == 1:
                    if [cells[col] for col in columns] != HEADERS:
                        raise ValueError("Source headers differ from reviewed catalog.")
                    continue
                if cells["A"] != str(year) or cells["B"] not in {str(m) for m in range(1, 13)}:
                    raise ValueError("Wrong or invalid source reference period.")
                month = int(cells["B"])
                nature = next((key for key, label in NATURES.items() if cells["AI"] == label), None)
                if nature is None:
                    raise ValueError("Unknown source nature; update reviewed catalog first.")
                function_key, classification = _classification(cells["R"], cells["S"], nature)
                identity = {
                    "nature": nature,
                    "nature_label": cells["AI"],
                    "function_key": function_key,
                    "function_code": cells["R"].zfill(2),
                    "source_function_code": cells["R"],
                    "function_label": cells["S"],
                    "classification": classification,
                }
                key = (nature, function_key)
                if key in identities and identities[key] != identity:
                    raise ValueError("Inconsistent function identity.")
                identities[key] = identity
                original = {
                    stage: _number(cells[col])
                    for stage, col in zip(STAGES, ("AE", "AF", "AG"), strict=True)
                }
                money = {
                    stage: value.quantize(CENT, rounding=ROUND_HALF_EVEN)
                    for stage, value in original.items()
                }
                difference = money["PAID"] + money["RAP_PAID"] - money["TOTAL_PAID"]
                if difference != 0:
                    raise ValueError("Published payment identity does not reconcile per row.")
                max_diff = max(max_diff, abs(difference))
                row_count += 1
                if row_count > MAX_ROWS:
                    raise ValueError("Source rows exceed bound.")
                month_counts[month] += 1
                counts[(month, key)] += 1
                if (month, key) not in groups:
                    groups[(month, key)] = defaultdict(Decimal)
                for stage, value in money.items():
                    groups[(month, key)][stage] += value
                    monthly[month][stage] += value
                    rounded_totals[stage] += value
                    raw_totals[stage] += original[stage]
                seen_categories.add(cells["AK"])
                if cells["AK"] in labels:
                    subset[month] += money["TOTAL_PAID"]
                    raw_subset[month] += original["TOTAL_PAID"]
            if set(monthly) != set(range(1, 13)) or not labels.issubset(seen_categories):
                raise ValueError("Incomplete months or published categories in source rows.")
            summary_months = []
            for month in range(1, 13):
                difference = subset[month] - published[month]
                if difference != 0:
                    raise ValueError("Monthly independent source summary does not reconcile.")
                summary_months.append(
                    {
                        "month": month,
                        "published_total": format(published[month], ".2f"),
                        "calculated_total": format(subset[month], ".2f"),
                        "difference": "0.00",
                    }
                )
            raw_annual = sum(raw_subset.values(), Decimal(0)).quantize(
                CENT, rounding=ROUND_HALF_EVEN
            )
            if abs(raw_annual - published["annual"]) > CENT:
                raise ValueError("Raw annual summary differs beyond cent rounding.")
            functions, natures, months = [], [], []
            for key, identity in sorted(identities.items()):
                observed = [month for month in range(1, 13) if (month, key) in groups]
                values = {
                    stage: sum((groups[(m, key)][stage] for m in observed), Decimal(0))
                    for stage in STAGES
                }
                functions.append(
                    {
                        **identity,
                        "row_count": sum(counts[(m, key)] for m in observed),
                        "observed_months": observed,
                        "amounts": _amounts(values),
                    }
                )
            for nature, label in NATURES.items():
                selected = [f for f in functions if f["nature"] == nature]
                if selected:
                    natures.append(
                        {
                            "nature": nature,
                            "nature_label": label,
                            "row_count": sum(f["row_count"] for f in selected),
                            "observed_months": sorted(
                                {m for f in selected for m in f["observed_months"]}
                            ),
                            "amounts": _amounts(
                                {
                                    stage: sum(
                                        (Decimal(f["amounts"][stage]) for f in selected), Decimal(0)
                                    )
                                    for stage in STAGES
                                }
                            ),
                        }
                    )
            for month in range(1, 13):
                months.append(
                    {
                        "month": month,
                        "row_count": month_counts[month],
                        "totals": _amounts(monthly[month]),
                        "groups": [
                            {
                                **identities[key],
                                "row_count": counts[(m, key)],
                                "amounts": _amounts(values),
                            }
                            for (m, key), values in sorted(groups.items())
                            if m == month
                        ],
                    }
                )
            payload = {
                "year": year,
                "scope": SCOPE,
                "currency": "BRL",
                "price_basis": "CURRENT",
                "accounting_basis": "OB_ISSUANCE_VALUE_PAID",
                "periodicity": "MONTHLY_MOVEMENT",
                "parser_version": PARSER_VERSION,
                "precision_version": PRECISION_VERSION,
                "source": dict(SOURCE),
                "resource": {**resource, "sha256": hashlib.sha256(raw).hexdigest()},
                "row_count": row_count,
                "stages": list(STAGES),
                "months": months,
                "totals": _amounts(rounded_totals),
                "natures": natures,
                "functions": functions,
                "absence_policy": ABSENCE_POLICY,
                "reconciliation": {
                    "row_payment_difference_max": format(max_diff, ".2f"),
                    "group_total_differences": _amounts(
                        {
                            stage: rounded_totals[stage]
                            - sum((Decimal(f["amounts"][stage]) for f in functions), Decimal(0))
                            for stage in STAGES
                        }
                    ),
                    "raw_minus_rounded_totals": {
                        stage: str(raw_totals[stage] - rounded_totals[stage]) for stage in STAGES
                    },
                    "published_subset": {
                        "scope": SUBSET_SCOPE,
                        "labels": sorted(labels),
                        "months": summary_months,
                        "annual_published_total": format(published["annual"], ".2f"),
                        "annual_calculated_total": format(sum(subset.values(), Decimal(0)), ".2f"),
                        "annual_difference": format(
                            sum(subset.values(), Decimal(0)) - published["annual"], ".2f"
                        ),
                    },
                },
            }
            payload["fingerprint"] = fingerprint(payload)
            validate_payload(payload)
            return payload


def validate_payload(payload):
    """Check immutable JSON snapshots, identity and independent reconciliation before use."""
    try:
        _validate_payload(payload)
    except (KeyError, TypeError, AttributeError, InvalidOperation, OverflowError) as exc:
        raise ValueError("Incomplete or incompatible functional spending cohort.") from exc


def _validate_payload(p):
    allowed = {
        "year",
        "scope",
        "currency",
        "price_basis",
        "accounting_basis",
        "periodicity",
        "parser_version",
        "precision_version",
        "source",
        "resource",
        "row_count",
        "stages",
        "months",
        "totals",
        "natures",
        "functions",
        "absence_policy",
        "reconciliation",
        "fingerprint",
    }
    expected = {
        "scope": SCOPE,
        "currency": "BRL",
        "price_basis": "CURRENT",
        "accounting_basis": "OB_ISSUANCE_VALUE_PAID",
        "periodicity": "MONTHLY_MOVEMENT",
        "parser_version": PARSER_VERSION,
        "precision_version": PRECISION_VERSION,
        "source": SOURCE,
        "stages": list(STAGES),
        "absence_policy": ABSENCE_POLICY,
    }
    if (
        not isinstance(p, dict)
        or set(p) != allowed
        or any(p.get(k) != v for k, v in expected.items())
    ):
        raise ValueError("Cohort definition differs from reviewed source contract.")
    _closed_year(p["year"], date.today())
    if not isinstance(p["resource"], dict) or set(p["resource"]) != {
        "id",
        "url",
        "last_modified",
        "size",
        "sha256",
    }:
        raise ValueError("Invalid or unexpected source metadata fields.")
    if not re.fullmatch(r"[0-9a-f]{64}", p["resource"]["sha256"]) or p[
        "fingerprint"
    ] != fingerprint(p):
        raise ValueError("Invalid source or canonical cohort hash.")
    _resource_url(p["resource"]["url"], p["resource"]["id"])
    if type(p["resource"]["size"]) is not int or not 0 < p["resource"]["size"] <= MAX_DOWNLOAD:
        raise ValueError("Invalid cohort source size.")
    datetime.fromisoformat(p["resource"]["last_modified"])
    if type(p["row_count"]) is not int or not 12 <= p["row_count"] <= MAX_ROWS:
        raise ValueError("Invalid cohort row count.")

    def cents(raw):
        if not isinstance(raw, str) or not re.fullmatch(r"-?\d+\.\d{2}", raw):
            raise ValueError("Monetary snapshots require exact signed cent strings.")
        return _number(raw)

    def amounts(value):
        if not isinstance(value, dict) or set(value) != set(STAGES):
            raise ValueError("All three explicit payment stages are required.")
        result = {}
        for stage, raw in value.items():
            result[stage] = cents(raw)
        if result["PAID"] + result["RAP_PAID"] != result["TOTAL_PAID"]:
            raise ValueError("Stage payment identity differs.")
        return result

    monthly_functions, monthly_counts = defaultdict(lambda: defaultdict(Decimal)), defaultdict(int)
    observed, identities = defaultdict(list), {}
    total = defaultdict(Decimal)
    rows = 0
    if not isinstance(p["months"], list) or len(p["months"]) != 12:
        raise ValueError("A complete closed-year cohort requires twelve months.")
    for number, month in enumerate(p["months"], 1):
        if (
            not isinstance(month, dict)
            or set(month) != {"month", "row_count", "totals", "groups"}
            or type(month["month"]) is not int
            or month["month"] != number
            or type(month["row_count"]) is not int
            or month["row_count"] < 1
        ):
            raise ValueError("Invalid or missing source months.")
        group_total, group_rows, seen = defaultdict(Decimal), 0, set()
        if not isinstance(month["groups"], list) or not 1 <= len(month["groups"]) <= 93:
            raise ValueError("Unbounded monthly functional groups.")
        for group in month["groups"]:
            if not isinstance(group, dict) or set(group) != {
                "nature",
                "nature_label",
                "function_key",
                "function_code",
                "source_function_code",
                "function_label",
                "classification",
                "row_count",
                "amounts",
            }:
                raise ValueError("Unknown fields in a source functional group.")
            nature, function = group["nature"], group["function_key"]
            identity = {
                k: group[k]
                for k in (
                    "nature",
                    "nature_label",
                    "function_key",
                    "function_code",
                    "source_function_code",
                    "function_label",
                    "classification",
                )
            }
            key = (nature, function)
            if (
                NATURES.get(nature) != group["nature_label"]
                or key in seen
                or group["function_code"] != group["source_function_code"].zfill(2)
                or _classification(group["source_function_code"], group["function_label"], nature)
                != (function, group["classification"])
                or (key in identities and identities[key] != identity)
                or type(group["row_count"]) is not int
                or group["row_count"] < 1
            ):
                raise ValueError("Invalid or duplicate functional identity.")
            seen.add(key)
            identities[key] = identity
            observed[key].append(number)
            monthly_counts[key] += group["row_count"]
            group_rows += group["row_count"]
            for stage, value in amounts(group["amounts"]).items():
                group_total[stage] += value
                monthly_functions[key][stage] += value
        if group_rows != month["row_count"] or group_total != amounts(month["totals"]):
            raise ValueError("Monthly function totals or row coverage differ.")
        rows += group_rows
        for stage, value in group_total.items():
            total[stage] += value
    if rows != p["row_count"] or total != amounts(p["totals"]):
        raise ValueError("Annual totals do not equal twelve monthly cohorts.")
    if not isinstance(p["functions"], list) or len(p["functions"]) != len(identities):
        raise ValueError("Annual functional coverage differs.")
    seen = set()
    for group in p["functions"]:
        if (
            not isinstance(group, dict)
            or set(group)
            != {
                "nature",
                "nature_label",
                "function_key",
                "function_code",
                "source_function_code",
                "function_label",
                "classification",
                "row_count",
                "amounts",
                "observed_months",
            }
            or not isinstance(group["observed_months"], list)
            or any(type(m) is not int for m in group["observed_months"])
            or type(group["row_count"]) is not int
        ):
            raise ValueError("Invalid annual function types or fields.")
        key = (group["nature"], group["function_key"])
        if (
            key in seen
            or key not in identities
            or any(group.get(k) != v for k, v in identities[key].items())
            or group["observed_months"] != observed[key]
            or group["row_count"] != monthly_counts[key]
            or amounts(group["amounts"]) != monthly_functions[key]
        ):
            raise ValueError("Annual group differs from observed monthly amounts.")
        seen.add(key)
    seen_natures = set()
    if not isinstance(p["natures"], list) or not 1 <= len(p["natures"]) <= 3:
        raise ValueError("Invalid nature list.")
    for group in p["natures"]:
        if (
            not isinstance(group, dict)
            or set(group) != {"nature", "nature_label", "row_count", "observed_months", "amounts"}
            or type(group["row_count"]) is not int
            or not isinstance(group["observed_months"], list)
            or any(type(m) is not int for m in group["observed_months"])
        ):
            raise ValueError("Invalid nature types or fields.")
        nature = group["nature"]
        selected = [key for key in identities if key[0] == nature]
        expected_totals = {
            stage: sum((monthly_functions[key][stage] for key in selected), Decimal(0))
            for stage in STAGES
        }
        if (
            not selected
            or nature in seen_natures
            or group["nature_label"] != NATURES[nature]
            or group["row_count"] != sum(monthly_counts[key] for key in selected)
            or group["observed_months"] != sorted({m for key in selected for m in observed[key]})
            or amounts(group["amounts"]) != expected_totals
        ):
            raise ValueError("Nature totals differ from observed functions.")
        seen_natures.add(nature)
    if seen_natures != {key[0] for key in identities}:
        raise ValueError("Nature coverage differs.")
    recon = p["reconciliation"]
    if not isinstance(recon, dict) or set(recon) != {
        "row_payment_difference_max",
        "group_total_differences",
        "raw_minus_rounded_totals",
        "published_subset",
    }:
        raise ValueError("Invalid reconciliation fields.")
    if (
        recon["row_payment_difference_max"] != "0.00"
        or any(v != "0.00" for v in recon["group_total_differences"].values())
        or set(recon["group_total_differences"]) != set(STAGES)
    ):
        raise ValueError("Source payment or partition reconciliation failed.")
    if set(recon["raw_minus_rounded_totals"]) != set(STAGES):
        raise ValueError("Missing raw rounding precision audit.")
    for value in recon["raw_minus_rounded_totals"].values():
        if abs(_number(value)) > Decimal(p["row_count"]) * Decimal("0.005"):
            raise ValueError("Raw rounding residual exceeds row precision bound.")
    subset = recon["published_subset"]
    if (
        not isinstance(subset, dict)
        or set(subset)
        != {
            "scope",
            "labels",
            "months",
            "annual_published_total",
            "annual_calculated_total",
            "annual_difference",
        }
        or subset["scope"] != SUBSET_SCOPE
        or not isinstance(subset["labels"], list)
        or not 1 <= len(subset["labels"]) <= 200
        or any(
            not isinstance(label, str) or len(label) > 500 or not re.match(r"[12]\.\d", label)
            for label in subset["labels"]
        )
        or sorted(set(subset["labels"])) != subset["labels"]
        or not isinstance(subset["months"], list)
        or len(subset["months"]) != 12
    ):
        raise ValueError("Invalid independently published subset definition.")
    subtotal = Decimal(0)
    for number, month in enumerate(subset["months"], 1):
        if (
            not isinstance(month, dict)
            or set(month) != {"month", "published_total", "calculated_total", "difference"}
            or type(month["month"]) is not int
            or month["month"] != number
            or month["difference"] != "0.00"
            or cents(month["published_total"]) != cents(month["calculated_total"])
        ):
            raise ValueError("Independent monthly summary differs.")
        subtotal += cents(month["calculated_total"])
    # Twelve independent month roundings (12×0.005) plus the annual rounding (0.005)
    # have a conservative cent ceiling of 0.07. This is an internal published summary.
    if (
        subtotal != cents(subset["annual_calculated_total"])
        or subtotal - cents(subset["annual_published_total"]) != cents(subset["annual_difference"])
        or abs(cents(subset["annual_difference"])) > Decimal("0.07")
    ):
        raise ValueError("Independent annual summary exceeds monthly rounding allowance.")


def fetch_year(year, as_of):
    _closed_year(year, as_of)
    metadata = json.loads(_download(CATALOG_URL, 1_000_000), object_pairs_hook=_unique_object)
    resource = _metadata(metadata, year)
    return parse_workbook(_download(resource["url"], MAX_DOWNLOAD), year, resource)
