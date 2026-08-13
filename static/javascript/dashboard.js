/* DataPilot — dashboard.js
   Drives the hero's live "before → after" demo table.
   Loops: dirty state -> scanning -> cleaned -> pause -> reset.
   Respects prefers-reduced-motion by showing the cleaned state statically. */

document.addEventListener('DOMContentLoaded', function () {
  const table = document.getElementById('demo-table');
  const status = document.getElementById('demo-status');
  if (!table || !status) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const dupeRow = table.querySelector('[data-role="dupe-row"]');
  const nullCells = table.querySelectorAll('[data-role="null-cell"]');
  const dateCell = table.querySelector('[data-role="date-cell"]');

  function setDirty() {
    status.textContent = '4 issues found';
    status.dataset.state = 'scanning';
    dupeRow?.classList.remove('row-removed');
    nullCells.forEach((c) => { c.classList.add('is-null'); c.classList.remove('is-fixed'); c.textContent = 'NULL'; });
    if (dateCell) { dateCell.classList.remove('is-fixed'); dateCell.textContent = '03/14/2026'; }
  }

  function setClean() {
    status.textContent = 'cleaned';
    status.dataset.state = 'clean';
    dupeRow?.classList.add('row-removed');
    nullCells.forEach((c) => { c.classList.remove('is-null'); c.classList.add('is-fixed'); c.textContent = '0'; });
    if (dateCell) { dateCell.classList.add('is-fixed'); dateCell.textContent = '2026-03-14'; }
  }

  if (reduceMotion) {
    setClean();
    return;
  }

  setDirty();
  setInterval(() => {
    const isDirty = status.dataset.state !== 'clean';
    if (isDirty) setClean(); else setDirty();
  }, 2600);
});