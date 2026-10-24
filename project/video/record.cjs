// 按 video/timeline.json 的解说时间轴录制系统操作画面。
// 运行：先启动 app/server.py，再执行
//   NODE_PATH=<playwright所在node_modules> CHROME_PATH=<chrome路径> node video/record.cjs
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const timeline = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
const outDir = path.join(__dirname, 'build');
fs.mkdirSync(outDir, {recursive: true});

(async () => {
  const launch = process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {channel: 'chrome'};
  const browser = await chromium.launch({...launch, headless: true, args: ["--lang=zh-CN"], env: {...process.env, LANG: "zh_CN.UTF-8", LANGUAGE: "zh_CN:zh"}});
  const ctx = await browser.newContext({viewport: {width: 1600, height: 1000}, locale: 'zh-CN',
    recordVideo: {dir: outDir, size: {width: 1600, height: 1000}}, acceptDownloads: true});
  const page = await ctx.newPage();
  const created = Date.now();
  await page.goto('http://127.0.0.1:8765');
  await page.waitForFunction(() => document.querySelector('#result').innerText.includes('毛灌溉量'));
  await page.addStyleTag({content: `
    #ov{position:fixed;inset:0;z-index:999;background:#244f3b;color:#f6f3ec;display:flex;flex-direction:column;
        justify-content:center;padding:0 140px;font-family:"Noto Sans CJK SC",sans-serif;transition:opacity .8s;pointer-events:none}
    #ov .k{font-size:22px;letter-spacing:4px;color:#dde7d3}
    #ov h1{font-size:120px;margin:28px 0 8px;font-weight:700;letter-spacing:12px}
    #ov h2{font-size:44px;margin:0 0 40px;font-weight:400}
    #ov .m{font-size:24px;line-height:1.8;color:#dde7d3;border-left:4px solid #a86b43;padding-left:22px}
    #ov .t{position:absolute;left:140px;bottom:160px;font-size:24px;color:#dde7d3;line-height:1.7}
    #ov .t b{color:#fff}
    #chip{position:fixed;top:18px;right:24px;z-index:998;background:#244f3bf0;color:#f6f3ec;padding:10px 22px;
          font:600 20px "Noto Sans CJK SC",sans-serif;letter-spacing:2px;border-radius:4px;transition:opacity .4s;pointer-events:none}
    html{scroll-behavior:smooth}`});
  await page.evaluate(() => {
    document.body.style.zoom = '.9';
    const c = document.createElement('div'); c.id = 'chip'; c.style.opacity = 0; document.body.append(c);
  });
  const overlay = async (html) => page.evaluate(h => {
    let o = document.getElementById('ov'); if (!o) {o = document.createElement('div'); o.id = 'ov'; document.body.append(o);}
    o.innerHTML = h; o.style.opacity = 1;
  }, html);
  const hideOverlay = async () => page.evaluate(() => {const o = document.getElementById('ov'); if (o) o.style.opacity = 0;});
  const chip = async (t) => page.evaluate(t => {const c = document.getElementById('chip'); c.textContent = t; c.style.opacity = t ? 1 : 0;}, t);

  const team = '<div class="t">团队名称　<b>得分队</b><br>团队编号　<b>AIC-2026-54247845</b></div>';
  await overlay(`<div class="k">2026 全球校园人工智能算法精英大赛 · AI＋农业</div><h1>墒策</h1><h2>可信需水预测与灌溉决策</h2>
    <div class="m">“墒”——土壤墒情，根区土壤的水分状况<br>“策”——灌溉决策：明天浇不浇、浇多少</div>${team}`);
  await page.waitForTimeout(300);

  const begin = Date.now();
  const at = async (sec) => {const w = begin + sec * 1000 - Date.now(); if (w > 0) await page.waitForTimeout(w);};
  const set = async (sel, v) => {const l = page.locator(sel); await l.fill(String(v)); await l.dispatchEvent('input'); await l.dispatchEvent('change');};
  const scroll = async (y) => page.evaluate(y => scrollTo({top: y, behavior: 'smooth'}), y);

  for (const sc of timeline) {
    await at(sc.start);
    const L = sc.lines.map(l => l.start);
    if (sc.key !== 'intro' && sc.key !== 'closing') await chip(sc.title);
    if (sc.key === 'overview') {
      await hideOverlay(); await scroll(0);
      await at(L[2]); await scroll(160);
    }
    if (sc.key === 'curve') {
      await scroll(560);
      const box = await page.locator('#chart').boundingBox();
      await at(L[1]); await page.mouse.move(box.x + box.width * .25, box.y + box.height * .5);
      await page.mouse.move(box.x + box.width * .55, box.y + box.height * .5, {steps: 60});
      await at(L[2]); await page.mouse.move(box.x + box.width * .95, box.y + box.height * .5, {steps: 80});
      await at(L[3]); await page.mouse.move(20, 20); await page.click('[data-window="90"]');
      await at(L[3] + 4.5); await page.click('[data-window="30"]');
    }
    if (sc.key === 'soil') {
      await scroll(700);
      await at(L[1]); await set('#deficit', 20);
      await at(L[2]); await set('#deficit', 70);
    }
    if (sc.key === 'capacity') {
      await scroll(560);
      await at(L[1]); await page.locator('#cap').fill('5'); await page.locator('#cap').press('Tab');
      await at(L[2]); const dl = page.waitForEvent('download'); await page.click('#export'); await (await dl).saveAs(path.join(outDir, 'demo_decision.json'));
    }
    if (sc.key === 'evidence') {
      await page.evaluate(() => scrollTo(0, 0)); await page.click('[data-tab="evidence"]');
      await at(L[2]); await scroll(380);
    }
    if (sc.key === 'transfer') {
      await scroll(760);
    }
    if (sc.key === 'simulation') {
      await page.evaluate(() => scrollTo(0, 0)); await page.click('[data-tab="simulation"]');
      await at(L[1]); await scroll(250);
      await at(L[3]); await scroll(560);
    }
    if (sc.key === 'closing') {
      await chip('');
      await overlay(`<div class="k">AI＋农业 · 作品总结</div><h1 style="font-size:96px">墒策</h1>
        <div class="m" style="font-size:26px">次日需水预测 MAE 0.776 mm/日，较昨日值降低 7.68%<br>90% 预测区间实际覆盖率 91.06%<br>
        180 组生长季仿真：区间上界策略缺水风险日降至 0<br>下一步：接入天气预报与田间墒情传感器，开展试点验证</div>${team}`);
    }
  }
  const end = timeline[timeline.length - 1].end;
  await at(end + 0.3);
  const video = page.video();
  await ctx.close();
  const vpath = await video.path();
  fs.writeFileSync(path.join(outDir, 'recording.json'), JSON.stringify({path: vpath, offset_s: (begin - created) / 1000, duration_s: end}));
  await browser.close();
  console.log('recorded', vpath);
})().catch(e => {console.error(e); process.exit(1);});
