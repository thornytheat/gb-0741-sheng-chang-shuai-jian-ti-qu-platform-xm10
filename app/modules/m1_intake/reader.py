import csv
import io
from collections import defaultdict

from app.config import MAX_BYTES, MAX_ROWS
from app.errors import Problem
from app.modules.m1_intake.continuity import check_band, issue
from app.modules.m1_intake.contract import HEADER, InvalidRow, band_hz, parse
from app.records import Intake


def decode(content):
    if not content:
        raise Problem('EMPTY_FILE', '文件为零字节')
    if len(content) > MAX_BYTES:
        raise Problem('FILE_TOO_LARGE', '文件超过 8 MiB', 413)
    for encoding in ('utf-8-sig', 'gb18030'):
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue
        if '\x00' not in text:
            return text, encoding
    raise Problem('ENCODING_INVALID', '文件编码无法识别')


def read(content):
    text, encoding = decode(content)
    stream = csv.reader(io.StringIO(text, newline=''), strict=True)
    valid, invalid = defaultdict(list), defaultdict(list)
    issues = []
    counts = dict(input=0, accepted=0, isolated=0, duplicate=0, blank=0, repeated_headers=0)
    header = None
    try:
        while True:
            line = stream.line_num + 1
            record = next(stream, None)
            if record is None:
                break
            normalized = tuple(value.strip().lstrip('\ufeff') for value in record)
            if header is None:
                if not any(normalized):
                    continue
                if len(normalized) != len(HEADER) or set(normalized) != set(HEADER):
                    raise Problem('BAD_HEADER', f'第 {line} 行列定义不匹配')
                header = normalized
                continue
            counts['input'] += 1
            if counts['input'] > MAX_ROWS:
                raise Problem('TOO_MANY_ROWS', '记录超过 100000 条', 413)
            if not any(normalized):
                counts['blank'] += 1
                continue
            if normalized == header:
                counts['repeated_headers'] += 1
                continue
            offset = header.index('band_hz')
            hz = band_hz(record[offset]) if len(record) > offset else None
            raw = dict(zip(header, record)) if len(record) == len(header) else record
            try:
                if isinstance(raw, list):
                    raise InvalidRow('ROW_WIDTH')
                if hz is None:
                    raise InvalidRow('BAND_INVALID')
                valid[hz].append(parse(line, raw))
            except InvalidRow as error:
                counts['isolated'] += 1
                issues.append(issue(line, hz, str(error), raw))
                if hz is not None:
                    invalid[hz].append(line)
    except csv.Error as error:
        raise Problem('BROKEN_CSV', f'第 {line} 行 CSV 损坏') from error
    if header is None:
        raise Problem('BLANK_FILE', '文件只有空行')
    if counts['input'] == counts['blank'] + counts['repeated_headers']:
        raise Problem('HEADER_ONLY', '表头后没有响应记录')
    bands, rejected = [], []
    for hz in sorted(valid.keys() | invalid.keys()):
        band, failure, duplicates, rejected_count = check_band(hz, valid[hz], invalid[hz])
        if band:
            bands.append(band)
            counts['accepted'] += len(band.samples)
        if failure:
            rejected.append(failure)
            counts['isolated'] += rejected_count
        issues.extend(duplicates)
        counts['duplicate'] += len(duplicates)
    return Intake(bands, rejected, sorted(issues, key=lambda item: item['line']), counts, encoding)
