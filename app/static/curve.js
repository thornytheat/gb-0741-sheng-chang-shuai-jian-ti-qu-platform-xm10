const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export function draw(canvas, curve, fit, gate, cursor) {
  const bounds = canvas.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(bounds.width * ratio);
  canvas.height = Math.round(bounds.height * ratio);
  const ctx = canvas.getContext('2d');
  ctx.scale(ratio, ratio);
  const left = 40, top = 15, right = bounds.width - 14, bottom = bounds.height - 32;
  const px = (time) => left + time / last * (right - left);
  const py = (db) => top + db / base * (bottom - top);
  const last = curve?.points.at(-1)?.t || 1;
  const floor = gate?.floor_db;
  const base = Math.max(-120, Math.min(-50, Math.floor((floor ?? -45) / 10) * 10 - 10));
  const ink = css('--muted'), grid = css('--line-soft'), noise = css('--noise');
  const accent = css('--accent'), regression = css('--fit');
  const line = (x1, y1, x2, y2, color, width = 1, dash = []) => {
    ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash);
    ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]);
  };
  ctx.font = '10px monospace';
  ctx.fillStyle = ink;
  ctx.textAlign = 'right';
  ctx.fillText('dB', left - 7, 11);
  for (let db = 0; db >= base; db -= 10) {
    const y = py(db);
    line(left, y, right, y, grid);
    ctx.fillText(String(db), left - 7, y + 3);
  }
  const divisions = bounds.width < 450 ? 4 : 6;
  ctx.textAlign = 'center';
  for (let i = 0; i <= divisions; i += 1) {
    const t = last * i / divisions;
    const x = px(t);
    line(x, top, x, bottom, grid);
    ctx.fillText(t.toFixed(2), x, bottom + 14);
  }
  ctx.fillText('峰值后时间 / 秒', (left + right) / 2, bottom + 29);
  if (!curve) return;

  const range = gate?.usable_until_s;
  ctx.save();
  ctx.beginPath(); ctx.rect(left, top, right - left, bottom - top); ctx.clip();
  if (gate) {
    const x = px(gate.noise_from_s);
    ctx.fillStyle = '#ad5d3615'; ctx.fillRect(x, top, right - x, bottom - top);
  }
  if (range != null) line(px(range), top, px(range), bottom, noise, 1, [3, 3]);
  if (floor != null && floor >= base) line(left, py(floor), right, py(floor), noise, 1.3, [4, 4]);
  if (fit) {
    for (const name of ['t30', 't20']) {
      const trial = fit[name];
      if (trial.rt60_s == null) continue;
      const {start_s: from, end_s: to} = trial.window;
      ctx.fillStyle = name === 't30' ? '#8170c117' : '#8170c127';
      ctx.fillRect(px(from), py(trial.from_db), px(to) - px(from), py(trial.to_db) - py(trial.from_db));
      line(px(from), py(trial.intercept_db + trial.slope_db_s * from), px(to), py(trial.intercept_db + trial.slope_db_s * to),
        regression, name === 't20' ? 2.0 : 1.5, name === 't30' ? [5, 3] : []);
    }
  }
  ctx.beginPath(); ctx.lineWidth = 1.8; ctx.strokeStyle = accent;
  let first = true;
  for (const point of curve.points) {
    if (point.db == null) { first = true; continue; }
    if (first) ctx.moveTo(px(point.t), py(point.db));
    else ctx.lineTo(px(point.t), py(point.db));
    first = false;
  }
  ctx.stroke();
  if (cursor) line(px(cursor.t), top, px(cursor.t), bottom, ink, 1, [2, 3]);
  ctx.restore();
}
