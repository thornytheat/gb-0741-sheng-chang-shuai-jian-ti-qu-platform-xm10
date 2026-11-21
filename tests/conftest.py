import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.config import SAMPLES
from app.main import create_app
from app.modules.m1_intake.contract import HEADER
from app.modules.m1_intake.reader import read
from app.modules.m6_reconcile.service import evaluate
from app.records import Signal


@pytest.fixture(scope='session')
def raw():
    return SAMPLES['hall'].read_bytes()


@pytest.fixture(scope='session')
def data(raw):
    return read(raw)


@pytest.fixture(scope='session')
def report(data):
    return evaluate(data)


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'hall.sqlite3')) as session:
        yield session


@pytest.fixture
def source(client):
    return client.get('/api/intake/sample/hall').json()['source_id']


@pytest.fixture
def encode():
    def make(*records, header=HEADER):
        stream = io.StringIO(newline='')
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(records)
        return stream.getvalue().encode()
    return make


@pytest.fixture
def signal():
    def make(values, peak=0, rate=1000):
        values = tuple(values)
        return Signal(500, rate, peak, values, tuple(range(2, 2 + len(values))))
    return make
