import {draw} from './curve.js';
import * as panels from './panels.js';

const {$, fixed} = panels;
const state = {result: null, manifest: null, band: 500, cursor: null, source: null, busy: false, view: 'decay'};
const nav = [...document.querySelectorAll('nav a')];
const auxiliary = ['intake', 'calibration', 'archive'];

async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message || `请求失败 · HTTP ${response.status}`);
  }
  return response.json();
}

function feedback(message, bad = false) {
  $('run-feedback').textContent = message;
  $('run-feedback').hidden = !message;
  $('run-feedback').toggleAttribute('data-bad', bad);
}

function controls() {
  document.querySelector('[form="run-form"]').disabled = state.busy;
  $('upload').querySelector('button').disabled = state.busy;
  $('rerun').disabled = state.busy || !state.manifest;
  const link = $('export');
  if (state.manifest) {
    link.href = `/api/runs/${state.manifest.id}/export`;
    link.removeAttribute('aria-disabled');
  } else {
    link.removeAttribute('href'); link.setAttribute('aria-disabled', 'true');
  }
}

async function act(operation) {
  if (state.busy) return;
  state.busy = true; controls(); feedback('');
  $('status').textContent = '正在计算';
  try {
    await operation();
    $('status').textContent = '分析已更新';
  } catch (error) {
    feedback(error.message, true);
    $('status').textContent = '操作失败';
  } finally {
    state.busy = false; controls();
  }
}

const selected = (group) => state.result?.[group]?.bands.find((row) => row.band_hz === state.band);

function chart() {
  const curve = selected('decay');
  const index = state.cursor;
  const cursor = index == null ? null : curve?.points[index];
  $('coordinate').textContent = cursor ? `${fixed(cursor.t)} s · ${fixed(cursor.db, 1)} dB · 行 ${cursor.source_line}` : '—';
  draw($('plot'), curve, selected('fit'), selected('noise'), cursor);
}

function choose(band) {
  state.band = Number(band);
  state.cursor = null;
  $('band').value = String(band);
  $('frequency').textContent = band ? `${band} Hz` : '— Hz';
  const curve = selected('decay');
  const row = selected('reconcile');
  const plotMessage = $('plot-empty');
  plotMessage.hidden = Boolean(curve && !curve.error);
  plotMessage.textContent = curve?.error?.message ?? row?.findings[0]?.message ?? '此频带待复测';
  const cursor = $('cursor');
  cursor.max = Math.max(0, (curve?.points.length ?? 1) - 1);
  cursor.value = 0;
  cursor.disabled = !curve || Boolean(curve.error);
  panels.fitPanel(selected('fit'), row);
  panels.noisePanel(selected('noise'));
  panels.reconcile(state.result.reconcile, state.band, choose);
  chart();
}

function render(result, manifest = null) {
  state.result = result;
  state.manifest = manifest;
  state.source = result.intake.source_id;
  $('source-meta').textContent = state.source.slice(0, 12);
  $('run-meta').textContent = manifest?.id.slice(0, 12) ?? '未归档';
  $('run-time').textContent = manifest?.created_at.slice(0, 19).replace('T', ' ') ?? '—';
  $('sample-count').textContent = `${result.intake.counts.accepted} 个采信采样点`;
  const rows = result.reconcile.bands;
  const select = $('band');
  select.replaceChildren(...(rows.length ? rows.map((item) => new Option(`${item.band_hz} Hz`, String(item.band_hz))) : [new Option('—', '')]));
  select.disabled = rows.length === 0;
  choose(rows.find((row) => row.band_hz === state.band)?.band_hz ?? rows[0]?.band_hz ?? 0);
  panels.intake(result.intake);
  panels.calibration(result.calibration);
  controls();
}

async function loadHistory() {
  const list = await request('/api/runs');
  panels.history(list.runs, state.manifest?.id, (id) => act(async () => {
    const archived = await request(`/api/runs/${id}`);
    $('sample').value = 'custom';
    render(archived.result, archived.manifest);
    await loadHistory();
  }));
}

async function archive(spec) {
  const body = await request('/api/runs', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(spec)});
  render(body.result, body.manifest);
  if (state.view === 'archive') await loadHistory();
  feedback(body.reused ? '已复用该批次' : '提取完成，已归档');
}

function switchView() {
  const hash = location.hash.slice(1);
  state.view = nav.some((link) => link.hash.slice(1) === hash) ? hash : 'decay';
  for (const link of nav) {
    const target = link.hash.slice(1);
    $(target).classList.toggle('is-current', target === state.view);
    if (target === state.view) {
      link.setAttribute('aria-current', 'page'); $('section-name').textContent = link.textContent;
    } else link.removeAttribute('aria-current');
  }
  for (const name of auxiliary) $(name).hidden = name !== state.view;
  if (hash === state.view) $(hash).scrollIntoView({block: 'nearest'});
  if (state.view === 'archive') loadHistory().catch((error) => feedback(error.message, true));
}

$('run-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const sample = $('sample').value;
  act(() => archive(sample === 'custom' ? {source_id: state.source} : {sample}));
});
$('upload').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  act(async () => {
    const source = await request('/api/intake', {method: 'POST', body: data});
    $('sample').value = 'custom';
    await archive({source_id: source.source_id});
  });
});
$('rerun').addEventListener('click', () => act(async () => {
  const id = state.manifest.id;
  const run = await request(`/api/runs/${id}/rerun`, {method: 'POST'});
  render(run.result, run.manifest);
  await loadHistory();
  feedback('重跑一致，已复用该批次');
}));
$('band').addEventListener('change', (event) => choose(event.target.value));
$('cursor').addEventListener('input', (event) => { state.cursor = Number(event.target.value); chart(); });
window.addEventListener('hashchange', switchView);
new ResizeObserver(chart).observe($('plot'));
switchView();
act(async () => {
  const source = await request('/api/intake/sample/hall');
  render(await request(`/api/reconcile/${source.source_id}/preview`));
});
