// Node validation harness: compares JS model against Python reference.
const ROF = require("./js/model.js");
const CFG = require("./js/config.js");
const ref = require("/home/user/workspace/fermi_reference.json");

let pass = 0, fail = 0;
function check(name, got, exp, tol, rel) {
  let ok;
  if (rel) {
    const denom = Math.max(Math.abs(exp), 1e-9);
    ok = Math.abs(got - exp) / denom <= tol;
  } else {
    ok = Math.abs(got - exp) <= tol;
  }
  (ok ? pass++ : fail++);
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}: got=${got} exp=${exp}` + (ok ? "" : `  DELTA=${got - exp}`));
}

console.log("=== Lambert W ===");
check("W(1)", ROF.lambertW0(1.0), ref.lambert.W1, 1e-9);
check("W(e)", ROF.lambertW0(Math.E), ref.lambert.We, 1e-9);
check("W(0)", ROF.lambertW0(0.0), ref.lambert.W0, 1e-12);
check("W(10)", ROF.lambertW0(10.0), ref.lambert.W10, 1e-8);
check("W(-0.2)", ROF.lambertW0(-0.2), ref.lambert.Wneg, 1e-9);

console.log("\n=== Function spot checks ===");
const p0 = CFG.makeParams();
check("F_saturating(3,K5)", ROF.F_REGISTRY.saturating(3, p0), 3 / (1 + 3 / 5), 1e-12);
check("O_peaked(4,lam.3)", ROF.O_REGISTRY.peaked(4, p0), 4 * Math.exp(-0.3 * 4), 1e-12);
check("h(2,k1)", ROF.hDetect(2, p0), 1 - Math.exp(-2), 1e-12);

console.log("\n=== Default trajectory (y0=1.0,0.8,0.2, tau_max=50) ===");
const dp = CFG.makeParams();
const dres = ROF.integrate(dp, [1.0, 0.8, 0.2]);
const dt = ref.default_trajectory;
function atTau(res, tv) {
  let bi = 0, bd = Infinity;
  for (let i = 0; i < res.tau.length; i++) { const d = Math.abs(res.tau[i] - tv); if (d < bd) { bd = d; bi = i; } }
  return { I: res.I[bi], R: res.R[bi], O: res.O[bi] };
}
for (const [tv, key] of [[10, "tau10"], [25, "tau25"], [50, "tau50"]]) {
  const a = atTau(dres, tv);
  check(`I@${tv}`, a.I, dt[key].I, 0.01, true);
  check(`R@${tv}`, a.R, dt[key].R, 0.01, true);
  check(`O@${tv}`, a.O, dt[key].O, 0.01, true);
}

console.log("\n=== 8 preset regimes ===");
let regimeOK = 0;
for (const key of CFG.STAGE_ORDER) {
  const { params, y0 } = CFG.stageParams(key);
  const res = ROF.integrate(params, y0);
  const { label } = ROF.classifyRegime(res, params);
  const expected = ref.presets[key].regime;
  const ok = label === expected;
  (ok ? pass++ : fail++);
  if (ok) regimeOK++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${key}: got=${label} exp=${expected}` +
    `  | I_f=${res.I[res.I.length-1].toFixed(3)} O_f=${res.O[res.O.length-1].toFixed(3)} R_f=${res.R[res.R.length-1].toFixed(3)}`);
}

console.log(`\n=== SUMMARY: ${pass} passed, ${fail} failed. Regimes ${regimeOK}/8 ===`);
process.exit(fail > 0 ? 1 : 0);
