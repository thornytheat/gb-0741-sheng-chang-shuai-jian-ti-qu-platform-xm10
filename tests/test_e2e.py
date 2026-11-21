from app.config import SAMPLES


def test_upload_to_all_stage_endpoints_and_archive(client):
    raw = SAMPLES['reference'].read_bytes()
    reply = client.post('/api/intake', files={'file':('reference.csv', raw)})
    assert reply.status_code == 200
    source = reply.json()['source_id']
    run = client.post('/api/runs', json={'source_id':source}).json()
    for stage in ('intake', 'calibration', 'decay', 'fit', 'noise', 'reconcile'):
        result = client.get(f'/api/{stage}/{source}')
        assert result.status_code == 200 and result.json() == run['result'][stage]
    assert client.get(f"/api/runs/{run['id']}/export").json()['result'] == run['result']


def test_home_serves_native_workbench_and_chart(client):
    page = client.get('/')
    assert page.status_code == 200 and '声场衰减提取台' in page.text
    assert all(f'href="#{section}"' in page.text for section in ('intake', 'calibration', 'decay', 'fit', 'noise', 'reconcile', 'archive'))
    assert client.get('/static/curve.js').status_code == 200
