// Dump browser-implementation trajectories for the cross-validation figure.
// Usage:  node js_dump.js      (writes paper/js_dump.json)
const fs = require("fs");
const path = require("path");

const WEB = path.join(__dirname, "..", "web_html_version", "js");
const CFG = require(path.join(WEB, "config.js"));
const ROF = require(path.join(WEB, "model.js"));

const out = {};
for (const key of CFG.STAGE_ORDER) {
  const { params, y0 } = CFG.stageParams(key);
  const res = ROF.integrate(params, y0, [0, params.tau_max]);
  const step = Math.max(1, Math.floor(res.tau.length / 200));
  const idx = [];
  for (let i = 0; i < res.tau.length; i += step) idx.push(i);
  if (idx[idx.length - 1] !== res.tau.length - 1) idx.push(res.tau.length - 1);
  out[key] = {
    tau: idx.map(i => res.tau[i]),
    I: idx.map(i => res.I[i]),
    R: idx.map(i => res.R[i]),
    O: idx.map(i => res.O[i]),
    regime: ROF.classifyRegime(res, params).label,
  };
}
fs.writeFileSync(path.join(__dirname, "js_dump.json"), JSON.stringify(out));
console.log("wrote js_dump.json for", Object.keys(out).length, "stages");
