import pytest

from app.config import SAMPLES
from app.errors import Problem
from app.modules.m1_intake.reader import read


def test_sample_counts_are_exclusive_and_remove_repeated_header(data):
    assert data.counts == {'input': 8466, 'accepted': 6000, 'isolated': 2463, 'duplicate': 1, 'blank': 1, 'repeated_headers': 1}  # TRAP-04
    assert sum(value for key, value in data.counts.items() if key != 'input') == data.counts['input']


def test_bom_and_multiline_keep_physical_sample_lines(data):
    assert data.encoding == 'utf-8-sig'  # TRAP-02
    band = next(band for band in data.bands if band.hz == 500)
    assert (band.samples[6].line, band.samples[6].raw['note'], band.samples[7].line) == (2207, '直达声\n舞台柜位', 2209)  # TRAP-03


def test_reference_reads_gb18030():
    source = read(SAMPLES['reference'].read_bytes())
    assert source.encoding == 'gb18030'  # TRAP-01
    assert source.bands[0].samples[6].raw['note'].startswith('直达声')


def test_short_width_and_missing_amplitude_have_distinct_codes(data):
    bad = {row['code']: row for row in data.row_issues}
    assert (bad['ROW_WIDTH']['line'], bad['ROW_WIDTH']['raw']) == (8468, ['NOT-A-BAND', '4'])  # TRAP-05
    assert (bad['AMPLITUDE_MISSING']['band_hz'], bad['AMPLITUDE_MISSING']['raw']['amplitude']) == (63, 'N/A')  # TRAP-07
    assert 63 not in [band.hz for band in data.bands]


def test_missing_points_and_truncated_tail_are_different(data):
    by_band = {row['band_hz']: row['findings'] for row in data.rejected_bands}
    assert by_band[250][0]['indices'] == [100]
    tail = next(item for item in by_band[2000] if item['code'] == 'TRUNCATED_BAND')  # TRAP-16
    assert (tail['from_index'], tail['to_index']) == (1062, 1099)


def test_contradictory_duplicate_band_never_reaches_fit(data):
    conflict = next(item for row in data.rejected_bands if row['band_hz'] == 2000 for item in row['findings'] if item['code'] == 'DUPLICATE_CONFLICT')  # TRAP-14
    assert conflict['index'] == 14 and len(conflict['lines']) == 2 and conflict['values'][1] == '99'
    assert [row['band_hz'] for row in data.row_issues if row['code'] == 'DUPLICATE_ROW'] == [500]


def test_arrival_order_reconstructed_by_sample_index(data):
    band = next(row for row in data.bands if row.hz == 1000)
    assert (band.samples[21].index, band.samples[22].index) == (21, 22)  # TRAP-13
    assert band.samples[21].line > band.samples[22].line


def test_empty_cases_raise_distinct_codes(encode):
    for content, expected in [(b'', 'EMPTY_FILE'), (b'\n\n', 'BLANK_FILE'), (encode(), 'HEADER_ONLY')]:
        with pytest.raises(Problem) as failure:
            read(content)
        assert failure.value.code == expected  # TRAP-18


def test_incomplete_csv_is_rejected_before_storage(client, encode):
    reply = client.post('/api/intake', files={'file': ('broken.csv', encode() + b'"broken')})
    assert (reply.status_code, reply.json()['code']) == (422, 'BROKEN_CSV')
    with client.app.state.store.connect() as connection:
        assert connection.execute('SELECT COUNT(*) FROM source').fetchone()[0] == 2


def test_config_conflict_keeps_both_citation_lines(encode):
    content = encode((500,0,1000,64,'Pa',0,'',1,''), (500,1,1000,64,'Pa',3,'',1,''))
    row = read(content).rejected_bands[0]
    assert row['findings'][0]['code'] == 'CAL_CONFLICT'
    assert row['findings'][0]['lines'] == [2, 3]
